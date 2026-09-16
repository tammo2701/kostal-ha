"""Sensor-Plattform für die Kostal Piko Integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    DXS_INVERTER_NAME,
    KostalPikoSensorDescription,
    MANUFACTURER,
    SENSOR_DESCRIPTIONS,
)
from .coordinator import KostalPikoCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Legt die Sensor-Entities anhand der beim WR tatsächlich vorhandenen
    DXS-Werte an. Dadurch passt sich die Integration automatisch an
    unterschiedliche PIKO-Varianten (Anzahl Strings/Phasen, mit/ohne
    Batterie) an."""
    coordinator: KostalPikoCoordinator = hass.data[DOMAIN][entry.entry_id]

    device_name = entry.title
    if coordinator.data and DXS_INVERTER_NAME in coordinator.data:
        device_name = str(coordinator.data[DXS_INVERTER_NAME])

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=device_name or "Kostal Piko",
        manufacturer=MANUFACTURER,
        model="PIKO",
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )

    entities = [
        KostalPikoSensor(coordinator, description, entry.entry_id, device_info)
        for description in SENSOR_DESCRIPTIONS
        if coordinator.data and description.dxs_id in coordinator.data
    ]

    if not entities:
        _LOGGER.warning(
            "Es konnten keine unterstützten DXS-Werte beim Wechselrichter "
            "%s gefunden werden - Sensoren werden ggf. beim nächsten "
            "Neustart der Integration ergänzt",
            entry.data[CONF_HOST],
        )

    async_add_entities(entities)


class KostalPikoSensor(CoordinatorEntity[KostalPikoCoordinator], SensorEntity):
    """Repräsentiert einen einzelnen DXS-Wert des Wechselrichters."""

    entity_description: KostalPikoSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KostalPikoCoordinator,
        description: KostalPikoSensorDescription,
        entry_id: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self.entity_description.dxs_id)
        if raw is None:
            return None
        value_fn = self.entity_description.value_fn
        if value_fn is not None:
            try:
                return value_fn(raw)
            except (TypeError, ValueError):
                return None
        return raw

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data is not None
            and self.entity_description.dxs_id in self.coordinator.data
        )
