"""Temporary timer platform."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.timer import DOMAIN as TIMER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall, State, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_DURATION,
    ATTR_FINISHES_AT,
    ATTR_REMAINING,
    DOMAIN,
    SERVICE_CANCEL,
    SERVICE_CREATE_TEMPORARY,
    SERVICE_FINISH,
    SERVICE_PAUSE,
    SERVICE_START,
    STATE_ACTIVE,
    STATE_FINALIZED,
    STATE_IDLE,
    STATE_PAUSED,
)
from .entity import TemporaryEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up temporary timer platform."""

    async def handle_create(call: ServiceCall) -> None:
        """Handle create timer service."""
        name = call.data["name"]
        duration = call.data["duration"]  # seconds

        timer = TemporaryTimer(
            hass,
            unique_id=f"timer_{dt_util.utcnow().timestamp()}",
            name=name,
            duration=duration,
        )

        async_add_entities([timer])
        await timer.start()

    async def handle_start(call: ServiceCall) -> None:
        """Handle start timer service."""
        entity_id = call.data[ATTR_ENTITY_ID]
        manager = hass.data[DOMAIN]["manager"]
        entity = manager.get_entity(entity_id)

        if not entity or not isinstance(entity, TemporaryTimer):
            _LOGGER.error("Timer %s not found", entity_id)
            return

        duration = call.data.get("duration")
        if duration:
            entity.set_duration(duration)

        await entity.start()

    async def handle_pause(call: ServiceCall) -> None:
        """Handle pause timer service."""
        entity_id = call.data[ATTR_ENTITY_ID]
        manager = hass.data[DOMAIN]["manager"]
        entity = manager.get_entity(entity_id)

        if not entity or not isinstance(entity, TemporaryTimer):
            _LOGGER.error("Timer %s not found", entity_id)
            return

        await entity.pause()

    async def handle_cancel(call: ServiceCall) -> None:
        """Handle cancel timer service."""
        entity_id = call.data[ATTR_ENTITY_ID]
        manager = hass.data[DOMAIN]["manager"]
        entity = manager.get_entity(entity_id)

        if not entity or not isinstance(entity, TemporaryTimer):
            _LOGGER.error("Timer %s not found", entity_id)
            return

        await entity.cancel()

    async def handle_finish(call: ServiceCall) -> None:
        """Handle finish timer service."""
        entity_id = call.data[ATTR_ENTITY_ID]
        manager = hass.data[DOMAIN]["manager"]
        entity = manager.get_entity(entity_id)

        if not entity or not isinstance(entity, TemporaryTimer):
            _LOGGER.error("Timer %s not found", entity_id)
            return

        await entity.finish()

    # Register services
    hass.services.async_register(
        TIMER_DOMAIN,
        SERVICE_CREATE_TEMPORARY,
        handle_create,
        schema=vol.Schema(
            {
                vol.Required("name"): cv.string,
                vol.Required("duration"): cv.positive_int,
            }
        ),
    )

    hass.services.async_register(
        TIMER_DOMAIN,
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
        TIMER_DOMAIN,
        SERVICE_PAUSE,
        handle_pause,
        schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id}),
    )

    hass.services.async_register(
        TIMER_DOMAIN,
        SERVICE_CANCEL,
        handle_cancel,
        schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id}),
    )

    hass.services.async_register(
        TIMER_DOMAIN,
        SERVICE_FINISH,
        handle_finish,
        schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_id}),
    )


class TemporaryTimer(TemporaryEntity):
    """Temporary timer entity."""

    def __init__(
        self, hass: HomeAssistant, unique_id: str, name: str, duration: int
    ) -> None:
        """Initialize timer."""
        super().__init__(hass, unique_id, name, expected_duration=duration)
        self._duration_s: int = duration
        self._remaining = timedelta(seconds=duration)
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._finish_unsub = None

    def set_duration(self, duration: int) -> None:
        """Set the duration and remaining time."""
        self._duration_s = duration
        self._remaining = timedelta(seconds=duration)

    def _update_state_attr(self) -> None:
        """Update the state attribute based on internal state."""
        if self._state == STATE_FINALIZED:
            self._attr_state = STATE_IDLE
        elif self._state == STATE_PAUSED:
            self._attr_state = STATE_PAUSED
        else:
            self._attr_state = STATE_ACTIVE

    def _update_extra_state_attributes(self) -> None:
        """Update extra state attributes."""
        # Call parent to set base attributes
        super()._update_extra_state_attributes()

        # Add timer-specific attributes
        self._attr_extra_state_attributes = self._attr_extra_state_attributes or {}

        # Calculate remaining time on-demand if timer is active
        remaining = self._remaining
        if self.is_active and self._end_time:
            now = dt_util.utcnow()
            remaining = self._end_time - now
            if remaining.total_seconds() < 0:
                remaining = timedelta(0)

        # Round to 2 decimal places for display
        remaining_seconds = round(remaining.total_seconds(), 2)

        self._attr_extra_state_attributes.update(
            {
                ATTR_DURATION: self._duration_s,
                ATTR_REMAINING: remaining_seconds,
            }
        )

        if self._end_time:
            self._attr_extra_state_attributes[ATTR_FINISHES_AT] = (
                self._end_time.isoformat()
            )

    async def start(self) -> None:
        """Start the timer."""
        # Cancel existing timer if running
        self._cancel_timers()

        # Set start and end times
        self._start_time = dt_util.utcnow()
        self._end_time = self._start_time + self._remaining

        # Mark as active
        self._mark_active()
        self._update_state_attr()

        # Schedule finish at end_time (convert to Python datetime)
        self._finish_unsub = async_track_point_in_time(
            self.hass, self._async_finish_callback, self._end_time
        )

        _LOGGER.debug(
            "Started timer %s for %s seconds",
            self.entity_id,
            self._remaining.total_seconds(),
        )

    async def pause(self) -> None:
        """Pause the timer."""
        if not self.is_active:
            return

        # Cancel timer callbacks
        self._cancel_timers()

        # Calculate remaining time with 2 decimal precision
        if self._end_time:
            now = dt_util.utcnow()
            remaining_delta = self._end_time - now
            if remaining_delta.total_seconds() < 0:
                self._remaining = timedelta(0)
            else:
                # Round to 2 decimal places
                self._remaining = timedelta(
                    seconds=round(remaining_delta.total_seconds(), 2)
                )

        # Mark as paused
        self._mark_paused()
        self._update_state_attr()

        _LOGGER.debug(
            "Paused timer %s with %s seconds remaining",
            self.entity_id,
            self._remaining.total_seconds(),
        )

    async def resume(self) -> None:
        """Resume the timer."""
        if not self.is_paused:
            return

        await self.start()

    async def cancel(self) -> None:
        """Cancel the timer."""
        self._cancel_timers()
        self._remaining = timedelta(0)
        self._mark_finalized()
        self._update_state_attr()
        _LOGGER.debug("Cancelled timer %s", self.entity_id)

    async def finish(self) -> None:
        """Finish the timer."""
        self._cancel_timers()
        self._remaining = timedelta(0)
        self._mark_finalized()
        self._update_state_attr()
        _LOGGER.info("Timer %s finished", self.entity_id)

        # Fire event for automations
        self.hass.bus.async_fire(
            "timer.finished",
            {ATTR_ENTITY_ID: self.entity_id},
        )

    @callback
    def _async_finish_callback(self, now: Any) -> None:
        """Callback when timer finishes."""
        self.hass.async_create_task(self.finish())

    def _cancel_timers(self) -> None:
        """Cancel all timer callbacks."""
        if self._finish_unsub:
            self._finish_unsub()
            self._finish_unsub = None

    def _restore_from_old_state(self, old_state: State) -> None:
        """Restore from previous state."""
        super()._restore_from_old_state(old_state)

        # Restore timer-specific attributes
        if old_state.attributes.get(ATTR_DURATION):
            self._duration_s = int(old_state.attributes[ATTR_DURATION])

        if old_state.attributes.get(ATTR_REMAINING):
            remaining_seconds = float(old_state.attributes[ATTR_REMAINING])
            self._remaining = timedelta(seconds=remaining_seconds)

        if old_state.attributes.get("start_time"):
            start_dt = dt_util.parse_datetime(old_state.attributes["start_time"])
            if start_dt:
                self._start_time = start_dt

        if old_state.attributes.get(ATTR_FINISHES_AT):
            end_dt = dt_util.parse_datetime(old_state.attributes[ATTR_FINISHES_AT])
            if end_dt:
                self._end_time = end_dt

        # If timer was active when saved, resume it
        if old_state.state == STATE_ACTIVE and self._remaining.total_seconds() > 0:
            self.hass.async_create_task(self.start())
        else:
            self._update_state_attr()

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self._cancel_timers()
        await super().async_will_remove_from_hass()
