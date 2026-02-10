# Temporary Entities for Home Assistant

A custom Home Assistant integration that manages temporary entities with automatic cleanup. The system currently supports timers, with architecture designed to extend to other temporary entity types (holds, reminders, etc.).

## Features

- **Temporary Timers**: Create timers that automatically clean up after completion
- **Smart Persistence**: Only saves entities that meet minimum duration threshold
- **Automatic Cleanup**: Configurable cleanup intervals for finalized and inactive entities
- **State Restoration**: Running timers resume correctly after Home Assistant restart
- **Flexible Configuration**: UI-based configuration with sensible defaults
- **Service Integration**: Full suite of services for entity management

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install" on the Temporary Entities card
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/temporary` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration → Integrations
4. Click the "+ ADD INTEGRATION" button
5. Search for "Temporary Entities" and follow the configuration steps

## Configuration

The integration is configured via the UI. After installation:

1. Go to **Settings** → **Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for **Temporary Entities**
4. Click **Configure** to adjust options:

### Configuration Options

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| **Minimum persist duration** | 60s | 1-300s | Entities shorter than this won't be saved to disk |
| **Cleanup interval** | 300s (5min) | 60-3600s | How often to check for expired entities |
| **Finalized grace period** | 30s | 0-300s | How long to keep finalized entities before cleanup |
| **Inactive max age** | 86400s (24h) | 3600-604800s | How long to keep paused/inactive entities |

## Usage

### Creating Temporary Timers

#### Via Service Call

```yaml
service: timer.create_temporary
data:
  name: "Coffee Timer"
  duration: 300  # 5 minutes in seconds
```

#### In Automations

```yaml
automation:
  - alias: "Start cooking timer"
    trigger:
      - platform: state
        entity_id: sensor.stove
        to: "on"
    action:
      - service: timer.create_temporary
        data:
          name: "Cooking Safety Timer"
          duration: 1800  # 30 minutes
```

### Timer Services

#### Start/Restart Timer
```yaml
service: timer.start
data:
  entity_id: timer.temporary_timer_12345
  duration: 600  # Optional: override duration
```

#### Pause Timer
```yaml
service: timer.pause
data:
  entity_id: timer.temporary_timer_12345
```

#### Resume Timer
```yaml
service: temporary.resume
data:
  entity_id: timer.temporary_timer_12345
```

#### Cancel Timer
```yaml
service: timer.cancel
data:
  entity_id: timer.temporary_timer_12345
```

#### Finish Timer
```yaml
service: timer.finish
data:
  entity_id: timer.temporary_timer_12345
```

#### Delete Entity
```yaml
service: temporary.delete
data:
  entity_id: timer.temporary_timer_12345
```

### Timer States

- **active**: Timer is running
- **paused**: Timer is paused
- **idle**: Timer has finished or been cancelled

### Timer Attributes

Each timer entity provides the following attributes:

| Attribute | Description |
|-----------|-------------|
| `created_at` | ISO timestamp when timer was created |
| `expected_duration` | Total duration in seconds |
| `duration` | Same as expected_duration (timer-specific) |
| `remaining` | Seconds remaining |
| `finishes_at` | ISO timestamp when timer will finish (if running) |
| `state` | Internal state (active/paused/finalized) |

### Automation Examples

#### Notify when timer finishes

```yaml
automation:
  - alias: "Timer finished notification"
    trigger:
      - platform: event
        event_type: timer.finished
    action:
      - service: notify.mobile_app
        data:
          title: "Timer Complete"
          message: "Your timer has finished!"
```

#### Create timer with voice command

```yaml
automation:
  - alias: "Create timer via voice"
    trigger:
      - platform: event
        event_type: intent_create_timer
    action:
      - service: timer.create_temporary
        data:
          name: "{{ trigger.event.data.name }}"
          duration: "{{ trigger.event.data.duration }}"
```

#### Auto-pause timer when leaving home

```yaml
automation:
  - alias: "Pause timers when leaving"
    trigger:
      - platform: state
        entity_id: person.your_name
        to: "not_home"
    action:
      - service: temporary.pause
        target:
          entity_id: "{{ states.timer | selectattr('attributes.state', 'eq', 'active') | map(attribute='entity_id') | list }}"
```

## Architecture Overview

### Core Components

1. **TemporaryEntity** (`entity.py`): Abstract base class for all temporary entities
   - Manages lifecycle and state
   - Handles persistence decisions
   - Implements cleanup logic

2. **TemporaryEntityManager** (`manager.py`): Central management system
   - Registers and tracks all temporary entities
   - Runs periodic cleanup tasks
   - Handles entity removal

3. **Timer Platform** (`timer.py`): Temporary timer implementation
   - Start/pause/resume/cancel/finish operations
   - Second-by-second updates
   - State restoration after restart

### State Management

Temporary entities have three states:

- **active**: Entity is actively running/in use
- **paused**: Entity is temporarily paused
- **finalized**: Entity has completed its purpose

### Cleanup Logic

Entities are cleaned up based on:

1. **Finalized entities**: Removed after `finalized_grace_period`
2. **Paused entities**: Removed after `inactive_max_age` from creation
3. **Active entities**: Never auto-removed

### Persistence Strategy

Entities are persisted to disk only if:
- Expected duration is unknown, OR
- Expected duration ≥ `min_persist_duration`

This prevents cluttering the state machine with very short-lived entities.

## Extending to New Entity Types

The architecture supports adding new temporary entity types:

1. Create new entity class inheriting from `TemporaryEntity`
2. Implement platform-specific logic
3. Add platform to `PLATFORMS` in `const.py`
4. Register services in platform setup

Example structure for a temporary reminder:

```python
class TemporaryReminder(TemporaryEntity):
    def __init__(self, hass, unique_id, name, remind_at):
        super().__init__(hass, unique_id, name)
        self._remind_at = remind_at

    async def trigger_reminder(self):
        # Send notification
        self._mark_finalized()
```

## Troubleshooting

### Timers not persisting after restart

Check that your timer duration exceeds `min_persist_duration` (default: 60 seconds).

### Entities not cleaning up

1. Verify cleanup interval is appropriate
2. Check logs for cleanup task execution
3. Ensure entities are properly finalized

### Timer not resuming after restart

Ensure the timer was in "active" state when Home Assistant was stopped. Paused timers remain paused after restart.

## Development

This project follows Home Assistant core's coding standards and uses the same linting/validation tools.

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/milohansen/ha-temporary.git
cd ha-temporary

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -r requirements_dev.txt
pre-commit install
```

### Code Quality Tools

This project uses:
- **Ruff** (>=0.15.0) - Fast Python linter and formatter (replaces flake8, isort, black)
- **MyPy** - Static type checking
- **Pylint** - Additional code analysis
- **Pytest** - Testing framework
- **Pre-commit** - Git hooks for automatic checks

### Common Development Commands

```bash
# Linting and formatting
ruff check .                    # Check for issues
ruff check --fix .              # Auto-fix issues
ruff format .                   # Format code
ruff format --check .           # Check formatting only

# Type checking
mypy custom_components/temporary

# Testing
pytest tests/ -v
pytest --cov=custom_components/temporary --cov-report=term-missing

# Validation
python validate.py

# Pre-commit hooks
pre-commit run --all-files
```

### Code Style Guidelines

- **Line length**: 88 characters (matches Home Assistant core)
- **Import order**: Managed by ruff (follows Home Assistant conventions)
- **Type hints**: Required for all public functions
- **Docstrings**: Google-style docstrings required
- **Naming**: snake_case for functions, PascalCase for classes

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Debug Logging

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.temporary: debug
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_manager.py -v

# Run with coverage report
pytest --cov=custom_components/temporary --cov-report=html
```

**Manual Testing Scenarios:**
1. Create a short timer (< 60s) - should not persist
2. Create a long timer (> 60s) - should persist
3. Restart Home Assistant - timer should resume
4. Pause a timer for 24h+ - should auto-cleanup

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/milohansen/ha-temporary/issues)
- **Documentation**: This README
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

## Changelog

### 0.1.0 (Initial Release)
- Temporary timer entities
- Automatic cleanup system
- UI-based configuration
- State restoration
- Service integration
