"""Temporary timer platform."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_point_in_time
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_DURATION,
    ATTR_FINISHES_AT,
    ATTR_REMAINING,
    STATE_ACTIVE,
    STATE_IDLE,
    STATE_PAUSED,
)
from .entity import TemporaryEntity

_LOGGER = logging.getLogger(__name__)

EVENT_TIMER_FINISHED = "temporary.timer_finished"
EVENT_TIMER_CANCELLED = "temporary.timer_cancelled"
EVENT_TIMER_CHANGED = "temporary.timer_changed"
EVENT_TIMER_CREATED = "temporary.timer_created"
EVENT_TIMER_RESUMED = "temporary.timer_resumed"
EVENT_TIMER_PAUSED = "temporary.timer_paused"


def _format_timedelta(delta: timedelta) -> str:
    """Format timedelta as H:MM:SS string."""
    total_seconds = max(delta.total_seconds(), 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}:{int(minutes):02}:{int(seconds):02}"


def _parse_timedelta(time_str: str) -> int:
    """Parse H:MM:SS string to seconds."""
    try:
        parts = time_str.split(":")
        if len(parts) != 3:
            return 0
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    except ValueError:
        return 0
    except AttributeError:
        return 0


class TemporaryTimer(TemporaryEntity):
    """Temporary timer entity."""

    _attr_icon = "mdi:timer"

    def __init__(
        self,
        hass: HomeAssistant,
        unique_id: str,
        name: str,
        duration: int,
        config_entry_id: str | None = None,
    ) -> None:
        """Initialize timer."""
        super().__init__(
            hass,
            unique_id,
            name,
            expected_duration=duration,
            config_entry_id=config_entry_id,
        )

        self._duration_s: int = duration
        self._remaining: timedelta | None = None
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._finish_unsub = None
        self._is_restoring: bool = False
        self._set_internal_state(STATE_IDLE)

    def set_duration(self, duration: int) -> None:
        """Set the duration."""
        old_duration = self._duration_s
        self._duration_s = duration

        # Fire changed event
        if not self._is_restoring:
            event_data = self._build_event_data()
            event_data["old_duration"] = old_duration
            event_data[ATTR_DURATION] = duration
            self.hass.bus.async_fire(EVENT_TIMER_CHANGED, event_data)

        self.async_write_ha_state()

    def _update_extra_state_attributes(self) -> None:
        """Update extra state attributes."""
        # Call parent to set base attributes
        super()._update_extra_state_attributes()

        # Add timer-specific attributes
        self._attr_extra_state_attributes = self._attr_extra_state_attributes or {}

        # Calculate remaining time based on state
        if self.is_active and self._end_time:
            # Active: calculate from end time
            now = dt_util.utcnow()
            remaining = self._end_time - now
            if remaining.total_seconds() < 0:
                remaining = timedelta(0)
        elif self.is_paused and self._remaining is not None:
            # Paused: use stored remaining time
            remaining = self._remaining
        else:
            # Idle/finalized or no remaining data: show zero
            remaining = timedelta(0)

        # Format duration as timedelta for formatting
        duration_delta = timedelta(seconds=self._duration_s)

        self._attr_extra_state_attributes.update(
            {
                ATTR_DURATION: _format_timedelta(duration_delta),
                ATTR_REMAINING: _format_timedelta(remaining),
            }
        )

        if self._end_time:
            self._attr_extra_state_attributes[ATTR_FINISHES_AT] = (
                self._end_time.isoformat()
            )

    def _build_event_data(self) -> dict[str, Any]:
        """Build common event data for timer events."""
        event_data: dict[str, Any] = {
            ATTR_ENTITY_ID: self.entity_id,
            "name": self._attr_name,
            ATTR_DURATION: self._duration_s,
            ATTR_FINISHES_AT: self._end_time.isoformat() if self._end_time else None,
        }
        return event_data

    async def start(self, is_resume: bool = False) -> None:
        """Start the timer.

        Args:
            is_resume: True if starting from a resume operation, False otherwise.
        """
        # Cancel existing timer if running
        self._cancel_timers()

        # Determine duration: use remaining if resuming from pause, otherwise use full duration
        duration = (
            self._remaining
            if self._remaining is not None
            else timedelta(seconds=self._duration_s)
        )

        # Set start and end times
        self._start_time = dt_util.utcnow()
        self._end_time = self._start_time + duration

        # Clear remaining since we're now tracking via end_time
        self._remaining = None

        # Mark as active
        self._mark_active()

        # Schedule finish at end_time (convert to Python datetime)
        self._finish_unsub = async_track_point_in_time(
            self.hass, self._async_finish_callback, self._end_time
        )

        _LOGGER.debug(
            "Started timer %s for %s seconds",
            self.entity_id,
            duration.total_seconds(),
        )

        # Fire created event (only if not resuming and not restoring)
        if not is_resume and not self._is_restoring:
            event_data = self._build_event_data()
            self.hass.bus.async_fire(EVENT_TIMER_CREATED, event_data)

    def async_pause(self) -> None:
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

        _LOGGER.debug(
            "Paused timer %s with %s seconds remaining",
            self.entity_id,
            self._remaining.total_seconds() if self._remaining else 0,
        )

        # Fire paused event
        if not self._is_restoring:
            event_data = self._build_event_data()
            if self._remaining:
                event_data[ATTR_REMAINING] = self._remaining.total_seconds()
            self.hass.bus.async_fire(EVENT_TIMER_PAUSED, event_data)

    async def async_resume(self) -> None:
        """Resume the timer."""
        if not self.is_paused:
            return

        await self.start(is_resume=True)

        # Fire resumed event before starting
        if not self._is_restoring:
            event_data = self._build_event_data()
            self.hass.bus.async_fire(EVENT_TIMER_RESUMED, event_data)

    def async_cancel(self) -> None:
        """Cancel the timer."""
        self._cancel_timers()
        self._mark_finalized()
        _LOGGER.debug("Cancelled timer %s", self.entity_id)

        # Fire cancelled event
        if not self._is_restoring:
            event_data = self._build_event_data()
            # Include remaining time if timer was active or paused
            self.hass.bus.async_fire(EVENT_TIMER_CANCELLED, event_data)

    def async_finish(self) -> None:
        """Finish the timer."""
        self._cancel_timers()
        self._mark_finalized()
        _LOGGER.info("Timer %s finished", self.entity_id)

        # Fire event for automations
        if not self._is_restoring:
            event_data = self._build_event_data()
            self.hass.bus.async_fire(EVENT_TIMER_FINISHED, event_data)

    @callback
    def _async_finish_callback(self, now: Any) -> None:
        """Callback when timer finishes."""
        self.async_finish()

    def _cancel_timers(self) -> None:
        """Cancel all timer callbacks."""
        if self._finish_unsub:
            self._finish_unsub()
            self._finish_unsub = None

    def _restore_from_old_state(self, old_state: State) -> None:
        """Restore from previous state."""
        super()._restore_from_old_state(old_state)

        # Set restoration flag to suppress events
        self._is_restoring = True

        # Restore timer-specific attributes
        if old_state.attributes.get(ATTR_DURATION):
            duration_val = old_state.attributes[ATTR_DURATION]
            # Handle both formatted string (H:MM:SS) and raw int/float
            if isinstance(duration_val, str):
                self._duration_s = _parse_timedelta(duration_val)
            else:
                self._duration_s = int(duration_val)

        if old_state.attributes.get("start_time"):
            start_dt = dt_util.parse_datetime(old_state.attributes["start_time"])
            if start_dt:
                self._start_time = start_dt

        if old_state.attributes.get(ATTR_FINISHES_AT):
            end_dt = dt_util.parse_datetime(old_state.attributes[ATTR_FINISHES_AT])
            if end_dt:
                self._end_time = end_dt

        # Restore based on saved state
        if old_state.state == STATE_ACTIVE and self._end_time:
            # For active timers, derive remaining from finishes_at
            now = dt_util.utcnow()
            remaining = self._end_time - now
            if remaining.total_seconds() > 0:
                self._remaining = remaining
                self.hass.async_create_task(self.start())
            else:
                # Timer expired during downtime — finish immediately
                self.async_finish()
        elif old_state.state == STATE_PAUSED:
            # Only set _remaining from saved attribute for paused timers
            if old_state.attributes.get(ATTR_REMAINING):
                remaining_val = old_state.attributes[ATTR_REMAINING]
                if isinstance(remaining_val, str):
                    remaining_seconds = _parse_timedelta(remaining_val)
                else:
                    remaining_seconds = float(remaining_val)
                self._remaining = timedelta(seconds=remaining_seconds)
            self.async_write_ha_state()
        else:
            self.async_write_ha_state()

        # Clear restoration flag
        self._is_restoring = False

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        self._cancel_timers()
        await super().async_will_remove_from_hass()
