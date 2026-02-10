"""Config flow for Temporary Entities integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback

from .const import (
    CONF_CLEANUP_INTERVAL,
    CONF_FINALIZED_GRACE_PERIOD,
    CONF_INACTIVE_MAX_AGE,
    CONF_MIN_PERSIST_DURATION,
    DEFAULT_CLEANUP_INTERVAL,
    DEFAULT_FINALIZED_GRACE_PERIOD,
    DEFAULT_INACTIVE_MAX_AGE,
    DEFAULT_MIN_PERSIST_DURATION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class TemporaryConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Temporary Entities."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        if user_input is not None:
            # Create entry with default options
            return self.async_create_entry(title="Temporary Entities", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> TemporaryOptionsFlow:
        """Get the options flow for this handler."""
        return TemporaryOptionsFlow(config_entry)


class TemporaryOptionsFlow(OptionsFlow):
    """Handle options flow for Temporary Entities."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MIN_PERSIST_DURATION,
                        default=self._config_entry.options.get(
                            CONF_MIN_PERSIST_DURATION, DEFAULT_MIN_PERSIST_DURATION
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
                    vol.Optional(
                        CONF_CLEANUP_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_CLEANUP_INTERVAL, DEFAULT_CLEANUP_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=3600)),
                    vol.Optional(
                        CONF_FINALIZED_GRACE_PERIOD,
                        default=self._config_entry.options.get(
                            CONF_FINALIZED_GRACE_PERIOD, DEFAULT_FINALIZED_GRACE_PERIOD
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=300)),
                    vol.Optional(
                        CONF_INACTIVE_MAX_AGE,
                        default=self._config_entry.options.get(
                            CONF_INACTIVE_MAX_AGE, DEFAULT_INACTIVE_MAX_AGE
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=3600, max=604800)),
                }
            ),
        )
