"""Manager for temporary entities."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_interval

if TYPE_CHECKING:
    from .entity import TemporaryEntity

_LOGGER = logging.getLogger(__name__)


class TemporaryEntityManager:
    """Manager for temporary entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        min_persist_duration: int,
        cleanup_interval: int,
        finalized_grace_period: int,
        inactive_max_age: int,
    ):
        """Initialize manager."""
        self.hass = hass
        self.min_persist_duration = timedelta(seconds=min_persist_duration)
        self.cleanup_interval = timedelta(seconds=cleanup_interval)
        self.finalized_grace_period = timedelta(seconds=finalized_grace_period)
        self.inactive_max_age = timedelta(seconds=inactive_max_age)

        self._entities: dict[str, TemporaryEntity] = {}
        self._cleanup_unsub = None

    @callback
    def register_entity(self, entity: TemporaryEntity) -> None:
        """Register a temporary entity."""
        self._entities[entity.entity_id] = entity
        _LOGGER.debug("Registered temporary entity: %s", entity.entity_id)

    @callback
    def unregister_entity(self, entity_id: str):
        """Unregister a temporary entity."""
        self._entities.pop(entity_id, None)
        _LOGGER.debug("Unregistered temporary entity: %s", entity_id)

    async def async_start(self):
        """Start the cleanup task."""
        self._cleanup_unsub = async_track_time_interval(
            self.hass,
            self._async_cleanup_task,
            self.cleanup_interval,
        )
        _LOGGER.info("Temporary entity cleanup task started")

    async def async_stop(self):
        """Stop the cleanup task."""
        if self._cleanup_unsub:
            self._cleanup_unsub()
            self._cleanup_unsub = None
        _LOGGER.info("Temporary entity cleanup task stopped")

    async def _async_cleanup_task(self, now: datetime) -> None:
        """Periodic cleanup task."""
        to_remove: list[str] = []

        for entity_id, entity in self._entities.items():
            if entity.should_cleanup():
                to_remove.append(entity_id)

        for entity_id in to_remove:
            await self.async_remove_entity(entity_id)

        if to_remove:
            _LOGGER.info("Cleaned up %d temporary entities", len(to_remove))

    async def async_remove_entity(self, entity_id: str) -> None:
        """Remove a temporary entity."""
        entity = self._entities.get(entity_id)
        if not entity:
            _LOGGER.warning("Entity %s not found for removal", entity_id)
            return

        # Remove from entity registry
        entity_reg = er.async_get(self.hass)
        if entity_reg.async_get(entity_id):
            entity_reg.async_remove(entity_id)

        # Remove entity from hass
        await entity.async_remove(force_remove=True)

        _LOGGER.debug("Removed temporary entity: %s", entity_id)

    def get_entity(self, entity_id: str) -> TemporaryEntity | None:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def get_all_entities(self) -> list[TemporaryEntity]:
        """Get all registered entities."""
        return list(self._entities.values())
