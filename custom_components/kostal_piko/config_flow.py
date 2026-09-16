"""Config Flow für die Kostal Piko Integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import asyncio
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_USE_HTTPS,
    DEFAULT_PASSWORD,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
    DXS_INVERTER_NAME,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_and_get_name(
    hass: HomeAssistant,
    host: str,
    use_https: bool,
    username: str | None,
    password: str | None,
) -> str:
    """Prüft die Erreichbarkeit und liest den vom WR gemeldeten Namen aus."""
    session = async_get_clientsession(hass)
    scheme = "https" if use_https else "http"
    url = f"{scheme}://{host}/api/dxs.json"
    auth = aiohttp.BasicAuth(username, password) if username else None

    async with asyncio.timeout(10):
        async with session.get(
            url, params={"dxsEntries": DXS_INVERTER_NAME}, auth=auth
        ) as resp:
            resp.raise_for_status()
            payload = await resp.json(content_type=None)

    entries = payload.get("dxsEntries") or []
    if entries and "value" in entries[0]:
        return str(entries[0]["value"])
    return "Kostal Piko"


class KostalPikoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Behandelt den Einrichtungsdialog für Kostal Piko."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
            try:
                name = await _validate_and_get_name(
                    self.hass,
                    user_input[CONF_HOST],
                    user_input[CONF_USE_HTTPS],
                    user_input.get(CONF_USERNAME) or None,
                    user_input.get(CONF_PASSWORD) or None,
                )
            except aiohttp.ClientResponseError as err:
                errors["base"] = (
                    "invalid_auth" if err.status in (401, 403) else "cannot_connect"
                )
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unerwarteter Fehler beim Verbindungstest")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=name, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_USE_HTTPS, default=False): bool,
                vol.Optional(CONF_USERNAME, default=""): str,
                vol.Optional(CONF_PASSWORD, default=""): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "default_username": DEFAULT_USERNAME,
                "default_password": DEFAULT_PASSWORD,
            },
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> KostalPikoOptionsFlow:
        return KostalPikoOptionsFlow(config_entry)


class KostalPikoOptionsFlow(config_entries.OptionsFlow):
    """Ermöglicht das nachträgliche Ändern des Abfrageintervalls."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)
