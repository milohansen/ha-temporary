# Implementation Plan: Temporary Entities for Home Assistant

## Project Overview

Create a custom Home Assistant integration that manages temporary entities with automatic cleanup. The system will support timers initially, with architecture to extend to other temporary entity types (holds, reminders, etc.).

## Directory Structure

```
custom_components/temporary/
├── __init__.py              # Component setup, service registration
├── manifest.json            # Integration metadata
├── config_flow.py          # Configuration UI
├── const.py                # Constants and defaults
├── entity.py               # Base TemporaryEntity class
├── manager.py              # TemporaryEntityManager
├── timer.py                # Timer platform implementation
├── services.yaml           # Service definitions
├── strings.json            # UI strings for config flow
└── translations/
    └── en.json             # English translations
```

## File-by-File Implementation Plan

### 1. `manifest.json`

**Purpose:** Integration metadata for HACS and Home Assistant

**Content:**

```json
{
  "domain": "temporary",
  "name": "Temporary Entities",
  "codeowners": ["@yourusername"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/yourusername/temporary-entities",
  "iot_class": "calculated",
  "issue_tracker": "https://github.com/yourusername/temporary-entities/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

### 2. `const.py`

**Purpose:** Centralize all constants, defaults, and configuration keys

**Requirements:**

- Domain name
- Platform list
- All configuration option keys
- Default values for:
  - Minimum persist duration (60s)
  - Cleanup interval (300s / 5 min)
  - Finalized grace period (30s)
  - Inactive max age (86400s / 24 hours)
- State constants (active, paused, finalized, idle)
- Attribute keys
- Service names

**Implementation notes:**

- Use descriptive constant names
- Group related constants together
- Add docstrings explaining each configuration option

### 3. `config_flow.py`

**Purpose:** UI-based configuration with options flow

**Requirements:**

- ConfigFlow class for initial setup
  - Single step: confirm to add integration
  - Generate unique entry ID
- OptionsFlow class for configuration changes
  - Schema with all 4 configurable parameters:
    - min_persist_duration (int, range 1-300, default 60)
    - cleanup_interval (int, range 60-3600, default 300)
    - finalized_grace_period (int, range 0-300, default 30)
    - inactive_max_age (int, range 3600-604800, default 86400)
  - Validation for sensible ranges
  - Help text for each option

**Implementation notes:**

- Use `vol.All` for range validation
- Include user-friendly descriptions
- Handle import from YAML (mark as deprecated, migrate to config entry)
- Return `self.async_create_entry()` with user input

### 4. `entity.py` - Base TemporaryEntity Class

**Purpose:** Abstract base class for all temporary entities

**Core Properties:**

- `_created_at`: datetime of creation
- `_finalized_at`: datetime when marked finalized (nullable)
- `_expected_duration`: expected lifetime in seconds (nullable)
- `_state`: current state (active/paused/finalized)
- `_attr_should_poll = False`

**Core Methods:**

**`__init__(hass, unique_id, name, expected_duration=None)`**

- Initialize base properties
- Set created_at to now
- Set state to active

**`@property should_persist() -> bool`**

- Get manager from hass.data
- Return True if expected_duration is None
- Return True if expected_duration >= manager.min_persist_duration
- Return False otherwise

**`@property is_finalized() -> bool`**

- Return self.\_state == STATE_FINALIZED

**`@property is_paused() -> bool`**

- Return self.\_state == STATE_PAUSED

**`@property is_active() -> bool`**

- Return self.\_state == STATE_ACTIVE

**`should_cleanup() -> bool`**

- Get manager and current time
- If finalized: check if (now - finalized_at) >= grace_period
- If paused: check if (now - created_at) >= inactive_max_age
- If active: return False (active entities don't auto-cleanup)
- Return cleanup decision

**`_mark_finalized()`**

- Set \_state = STATE_FINALIZED
- Set \_finalized_at = now
- Call async_write_ha_state()

**`_mark_paused()`**

- Set \_state = STATE_PAUSED
- Call async_write_ha_state()

**`_mark_active()`**

- Set \_state = STATE_ACTIVE
- Call async_write_ha_state()

**`async_added_to_hass()`**

- Call super()
- Restore state if exists (call \_restore_from_old_state)
- Register with manager
- If entity should NOT persist, log debug message

**`async_will_remove_from_hass()`**

- Unregister from manager
- Cancel any pending callbacks

**`_restore_from_old_state(old_state)`**

- Parse created_at from attributes
- Parse finalized_at from attributes if exists
- Parse expected_duration from attributes
- Restore \_state from old_state.state
- Subclasses override to restore their own attributes

**`@property extra_state_attributes`**

- Return dict with:
  - created_at (ISO format)
  - expected_duration
  - finalized_at (ISO format, if set)
  - state (active/paused/finalized)
- Subclasses extend this

### 5. `manager.py` - TemporaryEntityManager

**Purpose:** Centralized management of all temporary entities

**Core Properties:**

- `hass`: HomeAssistant instance
- `min_persist_duration`: seconds threshold
- `cleanup_interval`: seconds between cleanup runs
- `finalized_grace_period`: seconds to wait after finalized
- `inactive_max_age`: seconds for paused entity max age
- `_entities`: dict[entity_id, entity]
- `_cleanup_unsub`: cleanup task unsubscriber

**Core Methods:**

**`__init__(hass, min_persist_duration, cleanup_interval, finalized_grace_period, inactive_max_age)`**

- Store all parameters
- Initialize \_entities as empty dict
- Set \_cleanup_unsub to None

**`@callback register_entity(entity)`**

- Add entity to \_entities dict by entity_id
- Log debug message

**`@callback unregister_entity(entity_id)`**

- Remove entity from \_entities dict
- Log debug message

**`async async_start()`**

- Set up periodic cleanup using async_track_time_interval
- Store unsubscriber in \_cleanup_unsub
- Log info message

**`async async_stop()`**

- Cancel cleanup task if active
- Set \_cleanup_unsub to None

**`async _async_cleanup_task(now)`**

- Iterate through all registered entities
- Collect entity_ids that should_cleanup() == True
- Call async_remove_entity for each
- Log info with count of cleaned entities

**`async async_remove_entity(entity_id)`**

- Get entity from \_entities
- If not found, log warning and return
- Get entity_registry
- Remove from entity_registry if exists
- Call entity.async_remove(force_remove=True)
- Log debug message

**`get_entity(entity_id) -> TemporaryEntity | None`**

- Return entity from \_entities or None

**`get_all_entities() -> list[TemporaryEntity]`**

- Return list of all registered entities

### 6. `__init__.py` - Component Setup

**Purpose:** Integration initialization and service registration

**Functions:**

**`async async_setup_entry(hass, entry) -> bool`**

- Initialize hass.data[DOMAIN] dict if needed
- Create TemporaryEntityManager with options from entry
- Store manager in hass.data[DOMAIN]["manager"]
- Start manager cleanup task
- Forward entry setup to platforms (TIMER)
- Register domain services:
  - `temporary.delete` - delete any temporary entity
  - `temporary.pause` - pause entity (if supported)
  - `temporary.resume` - resume entity (if supported)
- Return True

**`async async_unload_entry(hass, entry) -> bool`**

- Get manager from hass.data
- Stop manager cleanup task
- Unload all platforms
- Remove manager from hass.data
- Unregister services
- Return unload success status

**`async async_reload_entry(hass, entry) -> None`**

- Call async_unload_entry
- Call async_setup_entry

**Service Handlers:**

**`handle_delete(call)`**

- Extract entity_id from call.data
- Get manager
- Call manager.async_remove_entity(entity_id)

**`handle_pause(call)`**

- Extract entity_id from call.data
- Get entity from manager
- If entity doesn't support pause, log error
- Call entity.\_mark_paused()

**`handle_resume(call)`**

- Extract entity_id from call.data
- Get entity from manager
- If entity doesn't support resume, log error
- Call entity.\_mark_active()

### 7. `timer.py` - Timer Platform

**Purpose:** Temporary timer entity implementation

**Platform Setup:**

**`async async_setup_entry(hass, entry, async_add_entities)`**

- Register services:
  - `timer.create_temporary` - create new timer
  - `timer.start` - start/restart a timer
  - `timer.pause` - pause a running timer
  - `timer.cancel` - cancel and finalize timer
  - `timer.finish` - manually finish timer

**TemporaryTimer Class:**

**Inherits from:** TemporaryEntity

**Additional Properties:**

- `_duration`: total duration in seconds
- `_remaining`: remaining seconds
- `_start_time`: when timer started (nullable)
- `_end_time`: calculated end time (nullable)
- `_timer_unsub`: callback unsubscriber for tick updates

**State Mapping:**

- active → "active"
- paused → "paused"
- finalized → "idle"

**`__init__(hass, unique_id, name, duration)`**

- Call super().**init** with expected_duration=duration
- Set \_duration = duration
- Set \_remaining = duration
- Set \_start_time = None
- Set \_end_time = None
- Set \_timer_unsub = None

**`@property state`**

- Return state string based on \_state

**`@property extra_state_attributes`**

- Get base attributes from super()
- Add:
  - duration (total seconds)
  - remaining (remaining seconds)
  - finishes_at (ISO format, if running)
- Return merged dict

**`async start()`**

- Cancel existing timer if running
- Set \_start_time = now
- Calculate \_end_time = now + remaining seconds
- Set state to active
- Schedule tick every second
- Schedule finish at end_time
- Write state

**`async pause()`**

- If not active, return
- Cancel timer callbacks
- Calculate \_remaining based on time elapsed
- Call \_mark_paused()
- Write state

**`async resume()`**

- If not paused, return
- Call start() with current \_remaining

**`async cancel()`**

- Cancel all timer callbacks
- Set \_remaining = 0
- Call \_mark_finalized()

**`async finish()`**

- Cancel all timer callbacks
- Set \_remaining = 0
- Call \_mark_finalized()
- Trigger any completion automations

**`async _tick(now)`**

- Calculate new \_remaining based on \_end_time
- If \_remaining <= 0, call finish()
- Else, write state with updated remaining

**`_restore_from_old_state(old_state)`**

- Call super().\_restore_from_old_state()
- Restore \_duration from attributes
- Restore \_remaining from attributes
- Restore \_start_time from attributes if exists
- Restore \_end_time from attributes if exists
- If state was active when saved, call start() to resume

**`async async_will_remove_from_hass()`**

- Cancel timer callbacks
- Call super()

### 8. `services.yaml`

**Purpose:** Service definitions for UI

**Services to Define:**

**`temporary.delete`**

- Description: Delete a temporary entity
- Fields:
  - entity_id (required): Entity to delete
  - Selector: entity with domain filter for temporary

**`temporary.pause`**

- Description: Pause a temporary entity
- Fields:
  - entity_id (required): Entity to pause
  - Selector: entity with domain filter for temporary

**`temporary.resume`**

- Description: Resume a paused temporary entity
- Fields:
  - entity_id (required): Entity to resume
  - Selector: entity with domain filter for temporary

**`timer.create_temporary`**

- Description: Create a temporary timer
- Fields:
  - name (required): Timer name
  - duration (required): Duration in seconds
  - Selector: text for name, number for duration

**`timer.start`**

- Description: Start a temporary timer
- Fields:
  - entity_id (required): Timer to start
  - duration (optional): Override duration
  - Selector: entity

**`timer.pause`**

- Description: Pause a running timer
- Fields:
  - entity_id (required): Timer to pause

**`timer.cancel`**

- Description: Cancel a timer
- Fields:
  - entity_id (required): Timer to cancel

**`timer.finish`**

- Description: Finish a timer immediately
- Fields:
  - entity_id (required): Timer to finish

### 9. `strings.json`

**Purpose:** UI strings for configuration flow

**Structure:**

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Temporary Entities",
        "description": "Set up temporary entities component"
      }
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Temporary Entities Options",
        "data": {
          "min_persist_duration": "Minimum duration to persist (seconds)",
          "cleanup_interval": "Cleanup check interval (seconds)",
          "finalized_grace_period": "Grace period after finalized (seconds)",
          "inactive_max_age": "Maximum age for paused entities (seconds)"
        },
        "data_description": {
          "min_persist_duration": "Entities shorter than this won't be saved to disk",
          "cleanup_interval": "How often to check for expired entities",
          "finalized_grace_period": "How long to keep finalized entities",
          "inactive_max_age": "How long to keep paused/inactive entities"
        }
      }
    }
  }
}
```

### 10. `translations/en.json`

**Purpose:** English translations (copy of strings.json for now)

## Implementation Steps for Claude Code

### Phase 1: Foundation (Files 1-3)

1. Create directory structure
2. Implement `manifest.json`
3. Implement `const.py` with all constants
4. Implement `config_flow.py` with validation

### Phase 2: Core Architecture (Files 4-5)

5. Implement `entity.py` - TemporaryEntity base class
   - All properties and methods as specified
   - Full state restoration logic
   - Proper lifecycle hooks
6. Implement `manager.py` - TemporaryEntityManager
   - Entity registration/unregistration
   - Periodic cleanup task
   - Entity removal logic

### Phase 3: Integration Setup (File 6)

7. Implement `__init__.py`
   - Entry setup/unload/reload
   - Service registration
   - Service handlers with error handling

### Phase 4: Timer Platform (File 7)

8. Implement `timer.py`
   - TemporaryTimer class with full timer logic
   - Start/pause/resume/cancel/finish methods
   - Tick callbacks and scheduling
   - State restoration for running timers
   - Service handlers

### Phase 5: Services & UI (Files 8-10)

9. Implement `services.yaml` with all service definitions
10. Implement `strings.json` and `translations/en.json`

### Phase 6: Testing & Validation

11. Create test configuration entry
12. Test entity creation and cleanup
13. Test state restoration after restart
14. Test all services
15. Test edge cases:
    - Very short timers (< min_persist)
    - Timer restoration mid-run
    - Multiple simultaneous cleanups
    - Paused timer expiration
    - Invalid entity_id in services

## Key Implementation Details

### Error Handling

- Wrap all service calls in try/except
- Log errors with context (entity_id, operation)
- Return gracefully on invalid entity_ids
- Handle missing entities in cleanup gracefully

### State Management

- Use dt_util for all datetime operations
- Store all times in UTC
- Convert to ISO format for attributes
- Parse carefully during restoration

### Performance Considerations

- Use @callback where possible to avoid executor
- Batch entity removals in cleanup
- Don't schedule individual cleanup per entity
- Use entity_registry efficiently

### Logging Strategy

- DEBUG: Entity registration/unregistration, individual cleanups
- INFO: Component start/stop, batch cleanups
- WARNING: Invalid operations, missing entities
- ERROR: Unexpected failures, state restoration errors

### Configuration Validation

- Ensure cleanup_interval > finalized_grace_period
- Ensure min_persist_duration > 0
- Ensure inactive_max_age > cleanup_interval
- Provide sensible defaults

## Testing Checklist

**Basic Functionality:**

- [ ] Integration loads without errors
- [ ] Config flow creates entry
- [ ] Options flow updates configuration
- [ ] Timer creation works
- [ ] Timer starts and counts down
- [ ] Timer pause/resume works
- [ ] Timer cancel works
- [ ] Timer finish works

**Persistence:**

- [ ] Timers > min_persist survive restart
- [ ] Timers < min_persist don't persist
- [ ] Running timers resume correctly after restart
- [ ] Paused timers restore correctly

**Cleanup:**

- [ ] Finalized timers removed after grace period
- [ ] Paused timers removed after max age
- [ ] Active timers NOT removed
- [ ] Cleanup task runs periodically
- [ ] Multiple entities cleaned in one pass

**Services:**

- [ ] temporary.delete removes entity
- [ ] temporary.pause pauses timer
- [ ] temporary.resume resumes timer
- [ ] All timer services work
- [ ] Invalid entity_id handled gracefully

**Edge Cases:**

- [ ] Creating 100+ timers doesn't crash
- [ ] Rapid create/delete cycles work
- [ ] Cleanup during restart works
- [ ] Removing non-existent entity fails gracefully
- [ ] Timer with 0 duration works

## Documentation Requirements

Create `README.md` with:

1. Installation instructions
2. Configuration options explained
3. Service usage examples
4. Automation examples
5. Architecture overview
6. Extension guide for new entity types

## Future Extensions (Not in Initial Implementation)

- Thermostat hold entities
- Reminder entities
- Guest access tokens
- Presence overrides
- Custom expiration callbacks
- Per-entity cleanup rules
- Entity templates for common patterns

---

**This plan is ready for Claude Code to implement step-by-step. Each phase builds on the previous, and all specifications are detailed enough to code directly.**
