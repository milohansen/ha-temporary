# Contributing to Temporary Entities Integration

Thank you for your interest in contributing! This project follows Home Assistant core's coding standards.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ha-temporary.git
   cd ha-temporary
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements_dev.txt
   pre-commit install
   ```

## Code Quality Standards

This project uses the same linting and validation tools as Home Assistant core:

### Ruff (Linting and Formatting)
- **Linter**: Ruff replaces flake8, isort, and many other tools
- **Formatter**: Ruff format replaces black
- **Version**: >= 0.15.0

```bash
# Check for linting issues
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Check formatting
ruff format --check .

# Auto-format code
ruff format .
```

### MyPy (Type Checking)
Type hints are required for all functions and methods.

```bash
mypy custom_components/temporary
```

### Pre-commit Hooks
Pre-commit hooks run automatically before each commit:

```bash
# Run manually on all files
pre-commit run --all-files
```

### Validation
Run the validation script to ensure all required files exist:

```bash
python validate.py
```

## Common Commands

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

# Run all checks (like CI)
ruff check . && ruff format --check . && mypy custom_components/temporary && pytest tests/ -v
```

## Code Style Guidelines

### Import Conventions
Follow Home Assistant's import aliases:
```python
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
```

### Docstrings
Use Google-style docstrings:
```python
def example_function(param1: str, param2: int) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When something goes wrong.
    """
    pass
```

### Type Hints
All public functions must have type hints:
```python
from __future__ import annotations

from typing import Any
from homeassistant.core import HomeAssistant

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up from config entry."""
    pass
```

### Naming Conventions
- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants
- Prefix private methods with underscore: `_private_method`

### Line Length
- Maximum line length: 88 characters (matches Home Assistant core)
- Let ruff format handle this automatically

## Testing

Tests should be placed in the `tests/` directory:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_manager.py -v

# Run with coverage report
pytest --cov=custom_components/temporary --cov-report=html
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following the style guidelines
   - Add/update tests
   - Update documentation if needed

3. **Run checks locally**
   ```bash
   ruff check . && ruff format --check . && mypy custom_components/temporary && pytest tests/ -v
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```
   Pre-commit hooks will run automatically.

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

## CI/CD Pipeline

GitHub Actions will automatically run:
- Ruff linting
- Ruff format check
- MyPy type checking
- Pytest tests (Python 3.12 and 3.13)
- Integration validation

All checks must pass before merging.

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about contributing
- Clarification on guidelines

## License

By contributing, you agree that your contributions will be licensed under the Apache-2.0 License.
