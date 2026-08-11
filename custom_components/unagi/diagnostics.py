"""Diagnostics support for the Unagi integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_AREA, CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS
from .coordinator import UnagiDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return compact diagnostics without duplicating the full forecast payload."""
    coordinator: UnagiDataUpdateCoordinator = entry.runtime_data
    data = coordinator.data or {}

    days: list[dict[str, Any]] = []
    for day in data.get("days", []):
        days.append(
            {
                "date": day.get("date"),
                "horizon_days": day.get("horizon_days"),
                "kind": day.get("kind"),
                "hour_count": len(day.get("hours", [])),
                "daily_avg": day.get("daily_avg"),
            }
        )

    return {
        "config": {
            "area": entry.data.get(CONF_AREA),
            "update_interval_hours": entry.options.get(
                CONF_UPDATE_INTERVAL_HOURS,
                entry.data.get(
                    CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS
                ),
            ),
        },
        "feed": {
            "schema_version": data.get("schema_version"),
            "generated_at": data.get("generated_at"),
            "area": data.get("area"),
            "unit": data.get("unit"),
            "price_basis": data.get("price_basis"),
            "timezone": data.get("timezone"),
            "resolution": data.get("resolution"),
            "days": days,
            "accuracy": data.get("accuracy"),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_exception": (
                str(coordinator.last_exception)
                if coordinator.last_exception is not None
                else None
            ),
        },
    }
