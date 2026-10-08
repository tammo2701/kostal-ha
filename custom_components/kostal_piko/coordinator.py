"""DataUpdateCoordinator für die Kostal Piko Integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import ALL_DXS_IDS, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Die Firmware älterer Kostal-Piko-Wechselrichter verarbeitet lange
# Query-Strings zuverlässiger, wenn nicht alle DXS-IDs auf einmal abgefragt
# werden. Deshalb wird in Blöcken abgefragt.
CHUNK_SIZE = 15
REQUEST_TIMEOUT = 10


class KostalPikoCoordinator(DataUpdateCoordinator[dict[int, Any]]):
    """Fragt zyklisch alle bekannten DXS-Werte des Wechselrichters ab."""

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
        scheme = "https" if use_https else "http"
        self._base_url = f"{scheme}://{host}/api/dxs.json"
        self._auth = aiohttp.BasicAuth(username, password or "") if username else None

    async def _fetch_chunk(self, chunk: list[int]) -> list[dict[str, Any]]:
        params = [("dxsEntries", str(dxs_id)) for dxs_id in chunk]
        async with asyncio.timeout(REQUEST_TIMEOUT):
            async with self._session.get(
                self._base_url, params=params, auth=self._auth, ssl=False
            ) as resp:
                if resp.status in (401, 403):
                    raise UpdateFailed("Anmeldung am Wechselrichter wurde abgelehnt")
                if resp.status != 200:
                    raise UpdateFailed(
                        f"Wechselrichter antwortete mit Status {resp.status}"
                    )
                # Manche Piko-Firmwares liefern den Content-Type nicht
                # korrekt als application/json.
                payload = await resp.json(content_type=None)
        if not isinstance(payload, dict):
            return []
        return payload.get("dxsEntries") or []

    async def _async_update_data(self) -> dict[int, Any]:
        results: dict[int, Any] = {}
        ids = list(ALL_DXS_IDS)
        chunks = [ids[i : i + CHUNK_SIZE] for i in range(0, len(ids), CHUNK_SIZE)]

        # Nacheinander statt parallel abfragen: die Webserver der alten
        # Piko-Serie sind sehr schwach und brechen bei parallelen Requests
        # gerne mit Timeouts/Resets ab. Ein fehlgeschlagener Block darf nicht
        # alle anderen Werte mitreissen.
        last_error: Exception | None = None
        for chunk in chunks:
            try:
                entries = await self._fetch_chunk(chunk)
            except (aiohttp.ClientError, TimeoutError, ValueError) as err:
                _LOGGER.debug("Abfrage eines DXS-Blocks fehlgeschlagen: %r", err)
                last_error = err
                continue

            for entry in entries:
                dxs_id = entry.get("dxsId")
                if dxs_id is None or "value" not in entry:
                    continue
                results[dxs_id] = entry["value"]

        if not results and last_error is not None:
            raise UpdateFailed(
                f"Verbindung zum Wechselrichter fehlgeschlagen: {last_error!r}"
            ) from last_error

        if not results:
            raise UpdateFailed(
                "Keine gültigen Daten vom Wechselrichter erhalten - "
                "ist die IP-Adresse korrekt und unterstützt die Firmware die "
                "/api/dxs.json Schnittstelle?"
            )

        return results
