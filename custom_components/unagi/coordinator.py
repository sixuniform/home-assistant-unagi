"""DataUpdateCoordinator for Unagi."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import UnagiApiClient, UnagiApiError
from .const import (
    CONF_AREA,
    CONF_UPDATE_INTERVAL_HOURS,
    DEFAULT_UPDATE_INTERVAL_HOURS,
)

_LOGGER = logging.getLogger(__name__)


class UnagiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate the single low-frequency request used by an Unagi entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.area: str = entry.data[CONF_AREA]
        interval_hours = int(
            entry.options.get(
                CONF_UPDATE_INTERVAL_HOURS,
                entry.data.get(
                    CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS
                ),
            )
        )
        self.api = UnagiApiClient(async_get_clientsession(hass), self.area)

        super().__init__(
            hass,
            _LOGGER,
            name=f"Unagi {self.area}",
            config_entry=entry,
            update_interval=timedelta(hours=interval_hours),
            always_update=False,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest CDN-cached forecast document."""
        try:
            return await self.api.async_get_forecast()
        except UnagiApiError as err:
            raise UpdateFailed(f"Error fetching Unagi {self.area}: {err}") from err
