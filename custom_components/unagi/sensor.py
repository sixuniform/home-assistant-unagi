"""Sensor platform for Unagi."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from statistics import mean, median
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import ATTR_ACCURACY, ATTR_FORECAST_DATA, DOMAIN, SOURCE_TIME_ZONE
from .coordinator import UnagiDataUpdateCoordinator

_SOURCE_TZ = ZoneInfo(SOURCE_TIME_ZONE)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Unagi sensor."""
    async_add_entities([UnagiPriceSensor(entry.runtime_data)])


def _as_source_datetime(value: str) -> datetime:
    """Convert an ISO timestamp to a Europe/Stockholm ZoneInfo datetime."""
    return datetime.fromisoformat(value).astimezone(_SOURCE_TZ)


def _day_map(data: dict[str, Any]) -> dict[date, dict[str, Any]]:
    """Index Unagi days by their explicit date."""
    result: dict[date, dict[str, Any]] = {}
    for item in data.get("days", []):
        try:
            result[date.fromisoformat(item["date"])] = item
        except (KeyError, TypeError, ValueError):
            continue
    return result


def _compat_raw(day: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return Nordpool-compatible start/end/value dictionaries."""
    if not day:
        return []
    result: list[dict[str, Any]] = []
    for slot in day.get("hours", []):
        try:
            result.append(
                {
                    "start": _as_source_datetime(slot["start"]),
                    "end": _as_source_datetime(slot["end"]),
                    "value": float(slot["value"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    result.sort(key=lambda item: item["start"])
    return result


def _values(day: dict[str, Any] | None) -> list[float]:
    return [item["value"] for item in _compat_raw(day)]


def _rich_forecast(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten all Unagi hours while retaining forecast metadata."""
    result: list[dict[str, Any]] = []
    for day in data.get("days", []):
        day_date = day.get("date")
        kind = day.get("kind")
        horizon = day.get("horizon_days")
        for slot in day.get("hours", []):
            try:
                result.append(
                    {
                        "date": day_date,
                        "kind": kind,
                        "horizon_days": horizon,
                        "start": _as_source_datetime(slot["start"]),
                        "end": _as_source_datetime(slot["end"]),
                        "value": float(slot["value"]),
                        "forecast": (
                            float(slot["forecast"])
                            if slot.get("forecast") is not None
                            else None
                        ),
                        "low": (
                            float(slot["low"])
                            if slot.get("low") is not None
                            else None
                        ),
                        "high": (
                            float(slot["high"])
                            if slot.get("high") is not None
                            else None
                        ),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    result.sort(key=lambda item: item["start"])
    return result


class UnagiPriceSensor(CoordinatorEntity[UnagiDataUpdateCoordinator], SensorEntity):
    """Current hourly Unagi value plus Nordpool-shaped forecast attributes."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "SEK/kWh"
    _attr_icon = "mdi:transmission-tower"
    _attr_suggested_display_precision = 4

    # These large list attributes are intentionally not stored by Recorder,
    # matching the strategy used by the Nordpool custom integration.
    _unrecorded_attributes = frozenset(
        {
            "today",
            "tomorrow",
            "raw_today",
            "raw_tomorrow",
            ATTR_FORECAST_DATA,
            ATTR_ACCURACY,
            *(f"day_{offset}" for offset in range(2, 8)),
            *(f"raw_day_{offset}" for offset in range(2, 8)),
            *(f"day_{offset}_cheapest_hours" for offset in range(2, 8)),
        }
    )

    def __init__(self, coordinator: UnagiDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"unagi_{coordinator.area.lower()}"
        self._attr_name = f"Unagi {coordinator.area}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.area)},
            name=f"Unagi {coordinator.area}",
            manufacturer="Unagi",
            model="Public electricity price forecast feed",
            configuration_url="https://unagieel.net",
        )
        self._remove_hour_listener = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator and local hourly state changes."""
        await super().async_added_to_hass()
        self._remove_hour_listener = async_track_time_change(
            self.hass,
            self._handle_local_hour_change,
            minute=0,
            second=1,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Remove the local hourly timer."""
        if self._remove_hour_listener is not None:
            self._remove_hour_listener()
            self._remove_hour_listener = None
        await super().async_will_remove_from_hass()

    @callback
    def _handle_local_hour_change(self, _now: datetime) -> None:
        """Advance current price from cached data without touching the network."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        """Return the value covering the current local time."""
        now = dt_util.now().astimezone(_SOURCE_TZ)
        today = _day_map(self.coordinator.data).get(now.date())
        for slot in _compat_raw(today):
            if slot["start"] <= now < slot["end"]:
                return slot["value"]
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose Nordpool-compatible and Unagi-specific forecast attributes."""
        data = self.coordinator.data
        now = dt_util.now().astimezone(_SOURCE_TZ)
        days = _day_map(data)
        today_date = now.date()
        today_day = days.get(today_date)
        tomorrow_day = days.get(today_date + timedelta(days=1))

        today = _values(today_day)
        tomorrow = _values(tomorrow_day)
        current = self.native_value

        average = mean(today) if today else None
        minimum = min(today) if today else None
        maximum = max(today) if today else None
        med = median(today) if today else None
        off_peak_1 = mean(today[0:8]) if len(today) >= 8 else None
        peak = mean(today[8:20]) if len(today) >= 20 else None
        off_peak_2 = mean(today[20:]) if len(today) >= 21 else None

        attrs: dict[str, Any] = {
            # Nordpool-compatible core attributes.
            "average": average,
            "off_peak_1": off_peak_1,
            "off_peak_2": off_peak_2,
            "peak": peak,
            "min": minimum,
            "max": maximum,
            "mean": med,
            "unit": "kWh",
            "currency": "SEK",
            "country": "Sweden",
            "region": self.coordinator.area,
            "low_price": (
                current < average
                if current is not None and average is not None
                else None
            ),
            "price_percent_to_average": (
                current / average
                if current is not None and average not in (None, 0)
                else None
            ),
            "today": today,
            "tomorrow": tomorrow,
            "tomorrow_valid": bool(
                tomorrow_day
                and tomorrow_day.get("kind") == "actual"
                and len(tomorrow) >= 23
            ),
            "raw_today": _compat_raw(today_day),
            "raw_tomorrow": _compat_raw(tomorrow_day),
            "current_price": current,
            "additional_costs_current_hour": 0.0,
            "price_in_cents": False,
            # Source metadata.
            "attribution": "Data: Unagi — unagieel.net",
            "source": "Unagi — unagieel.net",
            "source_price_basis": data.get("price_basis"),
            "source_resolution": data.get("resolution"),
            "source_generated_at": data.get("generated_at"),
            "source_schema_version": data.get("schema_version"),
            ATTR_ACCURACY: data.get("accuracy"),
            ATTR_FORECAST_DATA: _rich_forecast(data),
        }

        # Day +2 through +7 extensions. Selection is date-based, never array-index based.
        for offset in range(2, 8):
            target = today_date + timedelta(days=offset)
            day = days.get(target)
            attrs[f"day_{offset}_date"] = target.isoformat()
            attrs[f"day_{offset}_kind"] = day.get("kind") if day else None
            attrs[f"day_{offset}"] = _values(day)
            attrs[f"raw_day_{offset}"] = _compat_raw(day)
            attrs[f"day_{offset}_daily_avg"] = day.get("daily_avg") if day else None
            attrs[f"day_{offset}_cheapest_hours"] = (
                day.get("cheapest_hours") if day else []
            )

        return attrs
