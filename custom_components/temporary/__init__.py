"""The Temporary Entities integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

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
    PLATFORMS,
    SERVICE_DELETE,
    SERVICE_PAUSE,
    SERVICE_RESUME,
)
from .manager import TemporaryEntityManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up temporary entities from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create manager with options from config entry
    manager = TemporaryEntityManager(
        hass,
        min_persist_duration=entry.options.get(
            CONF_MIN_PERSIST_DURATION, DEFAULT_MIN_PERSIST_DURATION
        ),
        cleanup_interval=entry.options.get(
            CONF_CLEANUP_INTERVAL, DEFAULT_CLEANUP_INTERVAL
        ),
        finalized_grace_period=entry.options.get(
            CONF_FINALIZED_GRACE_PERIOD, DEFAULT_FINALIZED_GRACE_PERIOD
        ),
        inactive_max_age=entry.options.get(
            CONF_INACTIVE_MAX_AGE, DEFAULT_INACTIVE_MAX_AGE
        ),
    )
    hass.data[DOMAIN]["manager"] = manager

    # Start cleanup task
    await manager.async_start()

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register domain services
    async def handle_delete(call: ServiceCall) -> None:
        """Handle delete service call."""
        entity_id = call.data[ATTR_ENTITY_ID]
        try:
            await manager.async_remove_entity(entity_id)
        except (KeyError, ValueError) as err:
            _LOGGER.error("Error deleting entity %s: %s", entity_id, err)

    async def handle_pause(call: ServiceCall) -> None:
        """Handle pause service call."""
        entity_id = call.data[ATTR_ENTITY_ID]
        try:
            entity = manager.get_entity(entity_id)
            if not entity:
                _LOGGER.error("Entity %s not found", entity_id)
                return
            if not hasattr(entity, "mark_paused"):
                _LOGGER.error("Entity %s does not support pause", entity_id)
                return
            entity.mark_paused()
        except (KeyError, ValueError, AttributeError) as err:
            _LOGGER.error("Error pausing entity %s: %s", entity_id, err)

    async def handle_resume(call: ServiceCall) -> None:
        """Handle resume service call."""
        entity_id = call.data[ATTR_ENTITY_ID]
        try:
            entity = manager.get_entity(entity_id)
            if not entity:
                _LOGGER.error("Entity %s not found", entity_id)
                return
            if not hasattr(entity, "mark_active"):
                _LOGGER.error("Entity %s does not support resume", entity_id)
                return
            entity.mark_active()
        except (KeyError, ValueError, AttributeError) as err:
            _LOGGER.error("Error resuming entity %s: %s", entity_id, err)

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE,
        handle_delete,
        schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_PAUSE,
        handle_pause,
        schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESUME,
        handle_resume,
        schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id}),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    manager = hass.data[DOMAIN]["manager"]
    await manager.async_stop()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop("manager")
        # Unregister services
        hass.services.async_remove(DOMAIN, SERVICE_DELETE)
        hass.services.async_remove(DOMAIN, SERVICE_PAUSE)
        hass.services.async_remove(DOMAIN, SERVICE_RESUME)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
