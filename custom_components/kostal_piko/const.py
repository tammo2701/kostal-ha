"""Konstanten und Sensor-Definitionen für die Kostal Piko Integration.

Die alte Kostal-Piko-Serie (u. a. PIKO 4.2, 5.5, 7.2, 8.3, 9.3, 10, 10.1, 12,
15, 17, 20, 36 sowie die BA-Varianten mit Webserver-Version >= 6.00) bietet
eine undokumentierte, aber frei zugängliche lokale JSON-Schnittstelle unter

    http://<ip-adresse>/api/dxs.json?dxsEntries=<ID>[&dxsEntries=<ID>...]

Jede Mess- bzw. Statistikgröße besitzt eine feste numerische "DXS-ID". Die
hier verwendeten IDs wurden aus mehreren unabhängigen Community-Projekten
(u. a. Tafkas/collect_kostal.py, klausenbusk, msxfaq.de, openWB-Forum)
zusammengetragen und untereinander abgeglichen.

Hinweis: Die PIKO Plenticore-Serie (Hybridwechselrichter) nutzt ein anderes
Protokoll (Modbus/REST über pykoplenti) und wird von dieser Integration
NICHT unterstützt - dafür gibt es die offizielle "Kostal Plenticore"
Integration in Home Assistant Core.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.helpers.entity import EntityCategory

DOMAIN = "kostal_piko"
MANUFACTURER = "Kostal"

CONF_USE_HTTPS = "use_https"

DEFAULT_SCAN_INTERVAL = 30  # Sekunden
MIN_SCAN_INTERVAL = 10

# Standard-Zugangsdaten, die Kostal werkseitig für den DXS-Zugriff vergibt.
# Werden in der Config-Flow-Hilfe als Vorschlag angezeigt.
DEFAULT_USERNAME = "pvserver"
DEFAULT_PASSWORD = "pvwr"

# --- Einzelne, immer benötigte DXS-IDs -------------------------------------------------
DXS_INVERTER_NAME = 16777984
DXS_INVERTER_STATUS = 16780032

INVERTER_STATUS_MAP: dict[int, str] = {
    0: "Aus",
    1: "Leerlauf",
    2: "Anfahren",
    3: "Einspeisung (MPP-Betrieb)",
    4: "Abgeregelt",
    5: "Einspeisung",
    6: "Selbsttest",
    7: "Fehler",
    8: "EVU-Sperre",
    9: "Netzausfall",
    10: "Wartung",
}


def _status_value(raw: float) -> str:
    """Wandelt den numerischen Betriebsstatus in einen lesbaren Text um."""
    code = int(raw)
    return INVERTER_STATUS_MAP.get(code, f"Unbekannt ({code})")


@dataclass(frozen=True, kw_only=True)
class KostalPikoSensorDescription(SensorEntityDescription):
    """Beschreibt einen einzelnen, aus einem DXS-Wert abgeleiteten Sensor."""

    dxs_id: int
    value_fn: Callable[[float], object] | None = None


def _dc_string_sensors(idx: int, u_id: int, i_id: int, p_id: int) -> tuple[KostalPikoSensorDescription, ...]:
    return (
        KostalPikoSensorDescription(
            key=f"dc{idx}_voltage",
            dxs_id=u_id,
            name=f"DC String {idx} Spannung",
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        KostalPikoSensorDescription(
            key=f"dc{idx}_current",
            dxs_id=i_id,
            name=f"DC String {idx} Strom",
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        KostalPikoSensorDescription(
            key=f"dc{idx}_power",
            dxs_id=p_id,
            name=f"DC String {idx} Leistung",
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.WATT,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:solar-panel",
        ),
    )


def _ac_phase_sensors(idx: int, u_id: int, i_id: int, p_id: int) -> tuple[KostalPikoSensorDescription, ...]:
    return (
        KostalPikoSensorDescription(
            key=f"ac_l{idx}_voltage",
            dxs_id=u_id,
            name=f"AC Phase {idx} Spannung",
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        KostalPikoSensorDescription(
            key=f"ac_l{idx}_current",
            dxs_id=i_id,
            name=f"AC Phase {idx} Strom",
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        KostalPikoSensorDescription(
            key=f"ac_l{idx}_power",
            dxs_id=p_id,
            name=f"AC Phase {idx} Leistung",
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.WATT,
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    )


SENSOR_DESCRIPTIONS: tuple[KostalPikoSensorDescription, ...] = (
    # --- Übersicht / Momentanleistung ---------------------------------------------------
    KostalPikoSensorDescription(
        key="ac_power",
        dxs_id=67109120,
        name="AC-Ausgangsleistung",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power-variant",
    ),
    KostalPikoSensorDescription(
        key="dc_power_total",
        dxs_id=33556736,
        name="DC-Gesamtleistung",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    KostalPikoSensorDescription(
        key="self_consumption_power",
        dxs_id=83888128,
        name="Eigenverbrauch aktuell",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:home-lightning-bolt",
    ),
    KostalPikoSensorDescription(
        key="operating_status",
        dxs_id=DXS_INVERTER_STATUS,
        name="Betriebsstatus",
        icon="mdi:state-machine",
        value_fn=_status_value,
    ),
    # --- Statistik: heute -----------------------------------------------------------------
    KostalPikoSensorDescription(
        key="yield_day",
        dxs_id=251658754,
        name="Ertrag heute",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-power",
    ),
    KostalPikoSensorDescription(
        key="home_consumption_day",
        dxs_id=251659010,
        name="Hausverbrauch heute",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:home-lightning-bolt",
    ),
    KostalPikoSensorDescription(
        key="self_consumption_day",
        dxs_id=251659266,
        name="Eigenverbrauch heute",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:home-battery",
    ),
    KostalPikoSensorDescription(
        key="self_consumption_rate_day",
        dxs_id=251659278,
        name="Eigenverbrauchsquote heute",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent",
    ),
    KostalPikoSensorDescription(
        key="autarky_day",
        dxs_id=251659279,
        name="Autarkiegrad heute",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent",
    ),
    # --- Statistik: gesamt -----------------------------------------------------------------
    KostalPikoSensorDescription(
        key="yield_total",
        dxs_id=251658753,
        name="Ertrag gesamt",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-power",
    ),
    KostalPikoSensorDescription(
        key="home_consumption_total",
        dxs_id=251659009,
        name="Hausverbrauch gesamt",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:home-lightning-bolt",
    ),
    KostalPikoSensorDescription(
        key="self_consumption_total",
        dxs_id=251659265,
        name="Eigenverbrauch gesamt",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:home-battery",
    ),
    KostalPikoSensorDescription(
        key="self_consumption_rate_total",
        dxs_id=251659280,
        name="Eigenverbrauchsquote gesamt",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent",
    ),
    KostalPikoSensorDescription(
        key="autarky_total",
        dxs_id=251659281,
        name="Autarkiegrad gesamt",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent",
    ),
    KostalPikoSensorDescription(
        key="operating_time",
        dxs_id=251658496,
        name="Betriebszeit",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:timer-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # --- DC-Strings (bis zu 3, PIKO 10.1 hat i. d. R. 2-3) ---------------------------------
    *_dc_string_sensors(1, 33555202, 33555201, 33555203),
    *_dc_string_sensors(2, 33555458, 33555457, 33555459),
    *_dc_string_sensors(3, 33555714, 33555713, 33555715),
    # --- Netzparameter -----------------------------------------------------------------------
    KostalPikoSensorDescription(
        key="grid_frequency",
        dxs_id=67110400,
        name="Netzfrequenz",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KostalPikoSensorDescription(
        key="grid_cos_phi",
        dxs_id=67110656,
        name="cos(phi)",
        icon="mdi:angle-acute",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # --- AC-Phasen (PIKO 10.1 ist 3-phasig) ---------------------------------------------------
    *_ac_phase_sensors(1, 67109378, 67109377, 67109379),
    *_ac_phase_sensors(2, 67109634, 67109633, 67109635),
    *_ac_phase_sensors(3, 67109890, 67109889, 67109891),
    # --- Hausverbrauch nach Quelle -------------------------------------------------------------
    KostalPikoSensorDescription(
        key="home_consumption_from_solar",
        dxs_id=83886336,
        name="Hausverbrauch aus PV",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    KostalPikoSensorDescription(
        key="home_consumption_from_battery",
        dxs_id=83886592,
        name="Hausverbrauch aus Batterie",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:home-battery",
    ),
    KostalPikoSensorDescription(
        key="home_consumption_from_grid",
        dxs_id=83886848,
        name="Hausverbrauch aus Netz",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
    ),
    KostalPikoSensorDescription(
        key="home_consumption_l1",
        dxs_id=83887106,
        name="Hausverbrauch Phase 1",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KostalPikoSensorDescription(
        key="home_consumption_l2",
        dxs_id=83887362,
        name="Hausverbrauch Phase 2",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    KostalPikoSensorDescription(
        key="home_consumption_l3",
        dxs_id=83887618,
        name="Hausverbrauch Phase 3",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

# Alle DXS-IDs, die pro Update-Zyklus abgefragt werden müssen.
ALL_DXS_IDS: tuple[int, ...] = tuple(
    dict.fromkeys([DXS_INVERTER_NAME, *[d.dxs_id for d in SENSOR_DESCRIPTIONS]])
)
