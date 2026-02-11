"""Base class for temporary entities."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_CREATED_AT,
    ATTR_EXPECTED_DURATION,
    ATTR_FINALIZED_AT,
    DOMAIN,
    STATE_ACTIVE,
    STATE_FINALIZED,
    STATE_PAUSED,
)

if TYPE_CHECKING:
    from .manager import TemporaryEntityManager

_LOGGER = logging.getLogger(__name__)


class TemporaryEntity(RestoreEntity, Entity):
    """Base class for temporary entities."""

    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        unique_id: str,
        name: str,
        expected_duration: int | None = None,
    ) -> None:
        """Initialize temporary entity."""
        self.hass = hass
        self._attr_unique_id = unique_id
        self._attr_name = name

        # Temporary entity metadata
        self._created_at: datetime = dt_util.utcnow()
        self._finalized_at: datetime | None = None
        self._expected_duration = (
            timedelta(seconds=expected_duration)
            if expected_duration is not None
            else None
        )
        self._state: str = STATE_ACTIVE

    def _update_extra_state_attributes(self) -> None:
        """Update entity specific state attributes."""
        attrs: dict[str, Any] = {
            ATTR_CREATED_AT: self._created_at.isoformat(),
            ATTR_EXPECTED_DURATION: self._expected_duration.total_seconds()
            if self._expected_duration
            else None,
            "state": self._state,
        }

        if self._finalized_at:
            attrs[ATTR_FINALIZED_AT] = self._finalized_at.isoformat()

        self._attr_extra_state_attributes = attrs

    @property
    def should_persist(self) -> bool:
        """Check if entity should be persisted based on duration."""
        manager: TemporaryEntityManager = self.hass.data[DOMAIN]["manager"]

        # If we don't know duration, persist to be safe
        if self._expected_duration is None:
            return True

        return self._expected_duration >= manager.min_persist_duration

    @property
    def is_finalized(self) -> bool:
        """Return if entity is in finalized state."""
        return self._state == STATE_FINALIZED

    @property
    def is_paused(self) -> bool:
        """Return if entity is paused."""
        return self._state == STATE_PAUSED

    @property
    def is_active(self) -> bool:
        """Return if entity is active."""
        return self._state == STATE_ACTIVE

    def should_cleanup(self) -> bool:
        """Determine if entity should be cleaned up."""
        manager: TemporaryEntityManager = self.hass.data[DOMAIN]["manager"]
        now = dt_util.utcnow()

        # Finalized entities: cleanup after grace period
        if self.is_finalized and self._finalized_at:
            age = now - self._finalized_at
            return age >= manager.finalized_grace_period

        # Paused entities: cleanup after max age
        if self.is_paused:
            age = now - self._created_at
            return age >= manager.inactive_max_age

        return False

    @callback
    def _mark_finalized(self) -> None:
        """Mark entity as finalized."""
        self._state = STATE_FINALIZED
        self._finalized_at = dt_util.utcnow()
        self._update_extra_state_attributes()
        self.async_write_ha_state()

    @callback
    def _mark_paused(self) -> None:
        """Mark entity as paused."""
        self._state = STATE_PAUSED
        self._update_extra_state_attributes()
        self.async_write_ha_state()

    @callback
    def _mark_active(self) -> None:
        """Mark entity as active."""
        self._state = STATE_ACTIVE
        self._update_extra_state_attributes()
        self.async_write_ha_state()

    def mark_paused(self) -> None:
        """Mark entity as paused (public method)."""
        self._mark_paused()

    def mark_active(self) -> None:
        """Mark entity as active (public method)."""
        self._mark_active()

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Restore previous state
        if old_state := await self.async_get_last_state():
            self._restore_from_old_state(old_state)

        # Register with manager
        manager: TemporaryEntityManager = self.hass.data[DOMAIN]["manager"]
        manager.register_entity(self)

        # Log if entity won't persist
        if not self.should_persist:
            _LOGGER.debug(
                "Entity %s (duration: %s) will not persist to disk",
                self.entity_id,
                self._expected_duration,
            )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        manager: TemporaryEntityManager = self.hass.data[DOMAIN]["manager"]
        manager.unregister_entity(self.entity_id)

    def _restore_from_old_state(self, old_state: State) -> None:
        """Restore from previous state."""
        # Restore timestamps
        if old_state.attributes.get("created_at"):
            parsed_time = dt_util.parse_datetime(old_state.attributes["created_at"])
            if parsed_time:
                self._created_at = parsed_time

        if old_state.attributes.get("finalized_at"):
            self._finalized_at = dt_util.parse_datetime(
                old_state.attributes["finalized_at"]
            )

        if old_state.attributes.get("expected_duration"):
            self._expected_duration = timedelta(
                seconds=old_state.attributes["expected_duration"]
            )

        # Restore state
        self._state = old_state.state
