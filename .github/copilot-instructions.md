# Temporary Entities Integration - Copilot Instructions

## Project Overview

This is a custom Home Assistant integration that manages temporary entities with automatic cleanup. The system provides a framework for creating entities that have a defined lifecycle and automatically clean themselves up when no longer needed.

## Project Goals

### Primary Goals
1. **Temporary Timer Platform**: Provide fully-functional temporary timers that can be created programmatically, run for a specified duration, and automatically clean up
2. **Smart Persistence**: Only persist entities to disk that exceed a minimum duration threshold to reduce unnecessary I/O
3. **Automatic Cleanup**: Implement configurable cleanup intervals for finalized and inactive entities to prevent entity accumulation
4. **State Restoration**: Ensure running timers and active entities properly restore their state after Home Assistant restart
5. **Extensible Architecture**: Design the system to support future temporary entity types (holds, reminders, notes, etc.)
6. **User-Friendly Configuration**: Provide UI-based configuration with sensible defaults

### Technical Goals
- Follow Home Assistant integration best practices
- Use proper async/await patterns throughout
- Implement proper error handling and logging
- Support both service calls and UI interactions
- Maintain clean separation of concerns between components
- Use type hints consistently

## Code Quality Requirements

### Before Considering Any Task Complete

0. **Use the python virtual environment**: Always work within the project's virtual environment to ensure dependencies are correctly managed
   ```bash
   source .venv/bin/activate
   ```

1. **Always run Ruff for linting and formatting**:
   ```bash
   ruff check custom_components/temporary/
   ruff format custom_components/temporary/
   ```

2. **Check for errors using get_errors tool** to verify there are no type checking or compilation issues

3. **Verify the following**:
   - All imports are properly sorted and at the top of the file (except necessary inline imports to avoid circular dependencies)
   - Type hints are present for all function parameters and return values
   - Docstrings are present for all functions, classes, and methods
   - Error handling is implemented with try/catch where appropriate
   - Logging statements use appropriate log levels (debug, info, warning, error)
   - No unused imports or variables

4. **Test edge cases**:
   - What happens if an entity doesn't exist?
   - What happens if a service is called with invalid parameters?
   - What happens during Home Assistant restart or reload?
   - What happens if the entity type doesn't support the operation?

## Architecture Overview

### Components

1. **TemporaryEntity** (`entity.py`): Base class for all temporary entities
   - Manages lifecycle states (active, paused, finalized)
   - Handles persistence decisions
   - Provides cleanup determination logic
   - Implements state restoration

2. **TemporaryEntityManager** (`manager.py`): Central management
   - Tracks all temporary entities
   - Runs periodic cleanup tasks
   - Provides entity lookup and removal

3. **TemporaryTimer** (`timer.py`): Timer implementation
   - Extends TemporaryEntity
   - Uses `whenever` library for time handling
   - Supports start, pause, resume, cancel, finish operations
   - Fires events on completion

4. **Services** (`__init__.py`): Integration services
   - `temporary.create_temporary`: Create new timer
   - `temporary.start`: Start/restart timer
   - `temporary.pause`: Pause entity
   - `temporary.resume`: Resume entity
   - `temporary.cancel`: Cancel timer
   - `temporary.finish`: Finish timer
   - `temporary.delete`: Delete entity

### Key Design Decisions

- **Inline imports**: The `TemporaryTimer` import in `__init__.py` service handlers is intentionally inline to avoid circular dependencies
- **Type ignore comments**: Used for dynamic method calls on entities where the base class doesn't define timer-specific methods
- **Smart persistence**: Short-lived entities (< min_persist_duration) are not saved to disk to reduce I/O
- **Grace periods**: Finalized entities are kept briefly to allow automations to react before cleanup

## Common Patterns

### Service Handler Pattern
```python
async def handle_service(call: ServiceCall) -> None:
    """Handle service call."""
    entity_id = call.data[ATTR_ENTITY_ID]

    try:
        entity = manager.get_entity(entity_id)
        if not entity:
            _LOGGER.error("Entity %s not found", entity_id)
            return

        # Check if entity supports operation
        if not hasattr(entity, "method_name"):
            _LOGGER.error("Entity %s does not support operation", entity_id)
            return

        await entity.method_name()  # type: ignore[attr-defined]
    except (KeyError, ValueError, AttributeError) as err:
        _LOGGER.error("Error in operation for %s: %s", entity_id, err)
```

### Entity State Update Pattern
```python
@callback
def _mark_state_change(self) -> None:
    """Mark entity state change."""
    self._state = NEW_STATE
    self._update_extra_state_attributes()
    self.async_write_ha_state()
```

## Testing Considerations

When implementing or modifying features:
1. Test via Home Assistant Developer Tools → Services
2. Test automation integration
3. Test state restoration after restart
4. Test error conditions (invalid entity_id, wrong entity type, etc.)
5. Verify cleanup behavior after configured grace periods

## Future Extensions

The architecture supports adding new temporary entity types:
- Temporary holds (block execution temporarily)
- Temporary reminders (one-time notifications)
- Temporary notes (auto-expiring annotations)
- Temporary sensors (temporary value tracking)

New entity types should:
1. Extend `TemporaryEntity`
2. Implement type-specific behavior
3. Register appropriate platform services
4. Follow the established patterns for state management and cleanup
