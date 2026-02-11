"""The Temporary Entities integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import (
    config_validation as cv,
    entity_component,
    entity_registry as er,
)
import homeassistant.util.ulid as ulid_util

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
    SERVICE_CANCEL,
    SERVICE_CREATE_TEMPORARY,
    SERVICE_DELETE,
    SERVICE_FINISH,
    SERVICE_PAUSE,
    SERVICE_RESUME,
    SERVICE_START,
)
from .manager import TemporaryEntityManager

_LOGGER = logging.getLogger(__name__)


async def _restore_timer_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    timer_component: entity_component.EntityComponent,
) -> None:
    """Restore timer entities from registry."""
    ent_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(ent_reg, entry.entry_id)

    if not entries:
        return

    # Import here to avoid circular dependency at module level
    from .timer import TemporaryTimer  # noqa: PLC0415

    entities_to_restore: list[TemporaryTimer] = []
    for ent_entry in entries:
        if ent_entry.domain == "timer":
            # Extract name from entity_id or use unique_id
            name = ent_entry.original_name or ent_entry.entity_id.split(".")[-1]

            # Create timer entity with stored unique_id
            timer = TemporaryTimer(
                hass,
                unique_id=ent_entry.unique_id,
                name=name,
                duration=60,  # Default, will be restored from state
            )
            entities_to_restore.append(timer)
            _LOGGER.debug("Restoring timer entity: %s", ent_entry.entity_id)

    if entities_to_restore:
        await timer_component.async_add_entities(entities_to_restore)
        _LOGGER.info("Restored %d timer entities", len(entities_to_restore))


def _register_services(
    hass: HomeAssistant,
    manager: TemporaryEntityManager,
) -> None:
    """Register integration services."""

    async def handle_create_temporary(call: ServiceCall) -> None:
        """Handle create temporary timer service call."""
        name = call.data["name"]
        duration = call.data["duration"]  # seconds

        # Import here to avoid circular dependency at module level
        from .timer import TemporaryTimer  # noqa: PLC0415

        # Create unique ID based on timestamp
        unique_id = f"timer_{ulid_util.ulid_now()}"

        # Create timer entity
        timer = TemporaryTimer(
            hass,
            unique_id=unique_id,
            name=name,
            duration=duration,
        )

        # Get the timer component from stored data
        timer_component = hass.data[DOMAIN]["timer_component"]
        await timer_component.async_add_entities([timer])

        # Start the timer
        await timer.start()
        _LOGGER.info("Created and started temporary timer: %s", timer.entity_id)

    async def handle_start(call: ServiceCall) -> None:
        """Handle start timer service call."""
        entity_id = call.data[ATTR_ENTITY_ID]
        duration = call.data.get("duration")

        try:
            entity = manager.get_entity(entity_id)
            if not entity:
                _LOGGER.error("Timer %s not found", entity_id)
                return

            # Check if entity has start method (timer specific)
            if not hasattr(entity, "start"):
                _LOGGER.error("Entity %s does not support start", entity_id)
                return

            # Set new duration if provided
            if duration and hasattr(entity, "set_duration"):
                entity.set_duration(duration)  # type: ignore[attr-defined]

            await entity.start()  # type: ignore[attr-defined]
        except (KeyError, ValueError, AttributeError) as err:
            _LOGGER.error("Error starting entity %s: %s", entity_id, err)

    async def handle_cancel(call: ServiceCall) -> None:
        """Handle cancel timer service call."""
        entity_id = call.data[ATTR_ENTITY_ID]

        try:
            entity = manager.get_entity(entity_id)
            if not entity:
                _LOGGER.error("Timer %s not found", entity_id)
                return

            # Check if entity has cancel method (timer specific)
            if not hasattr(entity, "async_cancel"):
                _LOGGER.error("Entity %s does not support cancel", entity_id)
                return

            await entity.async_cancel()  # type: ignore[attr-defined]
        except (KeyError, ValueError, AttributeError) as err:
            _LOGGER.error("Error canceling entity %s: %s", entity_id, err)

    async def handle_finish(call: ServiceCall) -> None:
        """Handle finish timer service call."""
        entity_id = call.data[ATTR_ENTITY_ID]

        try:
            entity = manager.get_entity(entity_id)
            if not entity:
                _LOGGER.error("Timer %s not found", entity_id)
                return

            # Check if entity has finish method (timer specific)
            if not hasattr(entity, "async_finish"):
                _LOGGER.error("Entity %s does not support finish", entity_id)
                return

            await entity.async_finish()  # type: ignore[attr-defined]
        except (KeyError, ValueError, AttributeError) as err:
            _LOGGER.error("Error finishing entity %s: %s", entity_id, err)

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
            if not hasattr(entity, "async_pause"):
                _LOGGER.error("Entity %s does not support pause", entity_id)
                return
            await entity.async_pause()  # type: ignore[attr-defined]
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
            if not hasattr(entity, "async_resume"):
                _LOGGER.error("Entity %s does not support resume", entity_id)
                return
            await entity.async_resume()  # type: ignore[attr-defined]
        except (KeyError, ValueError, AttributeError) as err:
            _LOGGER.error("Error resuming entity %s: %s", entity_id, err)

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_TEMPORARY,
        handle_create_temporary,
        schema=vol.Schema(
            {
                vol.Required("name"): cv.string,
                vol.Required("duration"): cv.positive_int,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START,
        handle_start,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.entity_id,
                vol.Optional("duration"): cv.positive_int,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL,
        handle_cancel,
        schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_FINISH,
        handle_finish,
        schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id}),
    )

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

    # Get or create timer EntityComponent
    if "entity_components" not in hass.data:
        hass.data["entity_components"] = {}

    if "timer" not in hass.data["entity_components"]:
        timer_component = entity_component.EntityComponent(_LOGGER, "timer", hass)
        hass.data["entity_components"]["timer"] = timer_component
    else:
        timer_component = hass.data["entity_components"]["timer"]

    # Store component for later use
    hass.data[DOMAIN]["timer_component"] = timer_component

    # Restore entities from registry
    await _restore_timer_entities(hass, entry, timer_component)

    # Register domain services
    _register_services(hass, manager)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    manager = hass.data[DOMAIN]["manager"]
    await manager.async_stop()

    # Clean up stored data
    hass.data[DOMAIN].pop("manager")
    hass.data[DOMAIN].pop("timer_component", None)

    # Unregister services
    hass.services.async_remove(DOMAIN, SERVICE_CREATE_TEMPORARY)
    hass.services.async_remove(DOMAIN, SERVICE_START)
    hass.services.async_remove(DOMAIN, SERVICE_CANCEL)
    hass.services.async_remove(DOMAIN, SERVICE_FINISH)
    hass.services.async_remove(DOMAIN, SERVICE_DELETE)
    hass.services.async_remove(DOMAIN, SERVICE_PAUSE)
    hass.services.async_remove(DOMAIN, SERVICE_RESUME)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
