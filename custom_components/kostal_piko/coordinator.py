"""DataUpdateCoordinator für die Kostal Piko Integration."""
from __future__ import annotations

import asyncio
import html
import logging
import re
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Die alte Piko-Serie (PIKO 10.1 mit "PV Webserver") hat KEINE JSON-
# Schnittstelle (/api/dxs.json existiert dort nicht). Alle Werte stehen auf
# der Startseite "/" als HTML-Tabelle (HTTP Basic Auth, Standard
# pvserver / pvwr). Diese Seite wird geladen und ausgelesen.
REQUEST_TIMEOUT = 15

_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_NBSP_RE = re.compile(r"&nbsp;?", re.IGNORECASE)
_STRING_RE = re.compile(r"^String (\d+)$")
_MODEL_RE = re.compile(r"(PIKO\s*[\d.]+\w*)", re.IGNORECASE)


class PikoParseError(ValueError):
    """Die Antwort ist keine bekannte Piko-Statusseite."""


def _clean(fragment: str) -> str:
    text = _NBSP_RE.sub(" ", fragment)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return " ".join(text.split())


def _to_float(token: str | None) -> float | None:
    if token is None:
        return None
    try:
        return float(token.replace(",", "."))
    except ValueError:
        return None


def parse_status_page(page: str) -> dict[str, Any]:
    """Liest die Werte aus der Statusseite. Die Schlüssel entsprechen den
    Sensor-Keys aus const.py."""
    tokens: list[str] = []
    for match in _TD_RE.finditer(page):
        text = _clean(match.group(1))
        if text:
            tokens.append(text)

    if "Gesamtenergie" not in tokens and "Tagesenergie" not in tokens:
        raise PikoParseError("Unbekannte Antwort - keine Piko-Statusseite")

    def after(label: str) -> str | None:
        try:
            idx = tokens.index(label)
        except ValueError:
            return None
        return tokens[idx + 1] if idx + 1 < len(tokens) else None

    data: dict[str, Any] = {}

    model_match = _MODEL_RE.search(page)
    data["model"] = _clean(model_match.group(1)) if model_match else None

    data["ac_power"] = _to_float(after("aktuell"))
    data["yield_total"] = _to_float(after("Gesamtenergie"))  # kWh
    day_kwh = _to_float(after("Tagesenergie"))
    data["yield_day"] = round(day_kwh * 1000) if day_kwh is not None else None  # Wh

    status = after("Status")
    data["operating_status"] = None if status in (None, "PV-Generator") else status

    # Strings (DC) und Phasen (AC) stehen nebeneinander in einer Tabelle. Pro
    # Block "String n" folgen die Werte in der Reihenfolge
    # Spannung (DC), Spannung (AC), Strom (DC), Leistung (AC).
    starts = [i for i, t in enumerate(tokens) if _STRING_RE.match(t)]
    dc_total = 0.0
    dc_found = False
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(tokens)
        for i in range(start, end):
            if tokens[i].startswith("RS485"):
                end = i
                break
        block = tokens[start:end]
        idx = _STRING_RE.match(block[0]).group(1)  # type: ignore[union-attr]

        label_positions = [
            i for i, t in enumerate(block) if t in ("Spannung", "Strom", "Leistung")
        ]
        if len(label_positions) < 4:
            continue
        values = [
            _to_float(block[i + 1]) if i + 1 < len(block) else None
            for i in label_positions[:4]
        ]
        dc_v, ac_v, dc_i, ac_p = values

        data[f"dc{idx}_voltage"] = dc_v
        data[f"dc{idx}_current"] = dc_i
        dc_p = round(dc_v * dc_i) if dc_v is not None and dc_i is not None else None
        data[f"dc{idx}_power"] = dc_p
        if dc_p is not None:
            dc_total += dc_p
            dc_found = True
        data[f"ac_l{idx}_voltage"] = ac_v
        data[f"ac_l{idx}_power"] = ac_p

    data["dc_power_total"] = round(dc_total) if dc_found else None
    return data


async def async_fetch_status(
    session: aiohttp.ClientSession,
    host: str,
    use_https: bool,
    username: str | None,
    password: str | None,
) -> dict[str, Any]:
    """Lädt die Statusseite und gibt die geparsten Werte zurück."""
    scheme = "https" if use_https else "http"
    auth = aiohttp.BasicAuth(username, password or "") if username else None

    async with asyncio.timeout(REQUEST_TIMEOUT):
        async with session.get(f"{scheme}://{host}/", auth=auth, ssl=False) as resp:
            resp.raise_for_status()
            raw = await resp.read()

    return parse_status_page(raw.decode("iso-8859-1"))


class KostalPikoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Liest zyklisch die Statusseite des Wechselrichters aus."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        use_https: bool,
        username: str | None,
        password: str | None,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._session = async_get_clientsession(hass)
        self._host = host
        self._use_https = use_https
        self._username = username
        self._password = password

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await async_fetch_status(
                self._session,
                self._host,
                self._use_https,
                self._username,
                self._password,
            )
        except aiohttp.ClientResponseError as err:
            if err.status in (401, 403):
                raise UpdateFailed(
                    "Anmeldung am Wechselrichter wurde abgelehnt"
                ) from err
            raise UpdateFailed(
                f"Wechselrichter antwortete mit Status {err.status}"
            ) from err
        except PikoParseError as err:
            raise UpdateFailed(str(err)) from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(
                f"Verbindung zum Wechselrichter fehlgeschlagen: {err!r}"
            ) from err
