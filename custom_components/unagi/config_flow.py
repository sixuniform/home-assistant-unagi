"""Config flow for Unagi."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload
from homeassistant.core import callback

from .const import (
    AREAS,
    CONF_AREA,
    CONF_UPDATE_INTERVAL_HOURS,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
    UPDATE_INTERVAL_OPTIONS,
)


class UnagiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Unagi config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Set up an Unagi bidding area."""
        if user_input is not None:
            area = user_input[CONF_AREA]
            await self.async_set_unique_id(area)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Unagi {area}",
                data={
                    CONF_AREA: area,
                    CONF_UPDATE_INTERVAL_HOURS: user_input[
                        CONF_UPDATE_INTERVAL_HOURS
                    ],
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_AREA, default="SE3"): vol.In(AREAS),
                vol.Required(
                    CONF_UPDATE_INTERVAL_HOURS,
                    default=DEFAULT_UPDATE_INTERVAL_HOURS,
                ): vol.In(UPDATE_INTERVAL_OPTIONS),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return UnagiOptionsFlow()


class UnagiOptionsFlow(OptionsFlowWithReload):
    """Allow changing the network polling interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage Unagi options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = int(
            self.config_entry.options.get(
                CONF_UPDATE_INTERVAL_HOURS,
                self.config_entry.data.get(
                    CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS
                ),
            )
        )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL_HOURS,
                    default=current,
                ): vol.In(UPDATE_INTERVAL_OPTIONS)
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
