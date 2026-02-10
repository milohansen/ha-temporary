# Linting and Validation Setup Summary

This document summarizes the linting and validation tools configured for this project, aligned with Home Assistant core standards.

## 📋 Overview

The project now uses the same linting and validation stack as Home Assistant core:
- **Ruff** (>= 0.15.0) - Fast Python linter and formatter
- **MyPy** - Static type checking
- **Pylint** - Additional code analysis
- **Pytest** - Testing framework
- **Pre-commit** - Automated checks on commit

## 📁 Files Created/Modified

### Configuration Files
- ✅ **pyproject.toml** - Main configuration for ruff, pylint, mypy, pytest, coverage
- ✅ **.pre-commit-config.yaml** - Pre-commit hooks configuration
- ✅ **requirements_dev.txt** - Development dependencies
- ✅ **.gitignore** - Updated with all cache directories
- ✅ **CONTRIBUTING.md** - Contribution guidelines with code style info

### CI/CD
- ✅ **.github/workflows/ci.yml** - GitHub Actions CI pipeline

### VS Code Integration
- ✅ **.vscode/settings.json** - Editor settings for ruff, mypy
- ✅ **.vscode/extensions.json** - Recommended VS Code extensions

### Documentation
- ✅ **README.md** - Updated Development section
- ✅ **LINTING_SETUP.md** - This file

### Removed Files
- ❌ **.isortcfg** - Removed (ruff handles import sorting now)

## 🚀 Quick Start

### 1. Install Development Dependencies

```bash
# Create/activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements_dev.txt
pre-commit install
```

### 2. Run Checks

```bash
# Run all checks
ruff check . && ruff format --check . && mypy custom_components/temporary

# Or run individually:
ruff check .                          # Ruff linting
ruff format --check .                 # Check formatting
mypy custom_components/temporary      # MyPy type checking
pytest tests/ -v                      # Run tests
python validate.py                    # Integration validation
```

### 3. Auto-fix Issues

```bash
# Auto-format and fix linting issues
ruff format . && ruff check --fix .

# Or separately:
ruff format .          # Format with ruff
ruff check --fix .     # Fix linting issues
```

## 🛠️ Tools Configuration

### Ruff (Linting & Formatting)

**Purpose**: Fast all-in-one linter and formatter (replaces flake8, isort, black, and more)

**Configuration**: `[tool.ruff]` in `pyproject.toml`

**Key Settings**:
- Line length: 88 characters
- Target Python: 3.12+
- 100+ linting rules enabled (aligned with HA core)
- Import conventions (e.g., `voluptuous as vol`, `config_validation as cv`)

**Commands**:
```bash
ruff check .                    # Check for issues
ruff check --fix .              # Auto-fix issues
ruff format .                   # Format code
ruff format --check .           # Check formatting without changes
```

### MyPy (Type Checking)

**Purpose**: Static type checking

**Configuration**: `[tool.mypy]` in `pyproject.toml`

**Key Settings**:
- Strict mode enabled
- Python 3.12+
- All type checking options from HA core

**Commands**:
```bash
mypy custom_components/temporary
```

### Pylint (Additional Analysis)

**Purpose**: Additional code quality checks

**Configuration**: `[tool.pylint]` in `pyproject.toml`

**Key Settings**:
- Python 3.12+
- Format checking disabled (handled by ruff)
- Aligned with HA core disabled checks

**Commands**:
```bash
pylint custom_components/temporary
```

### Pytest (Testing)

**Purpose**: Unit and integration testing

**Configuration**: `[tool.pytest.ini_options]` in `pyproject.toml`

**Key Settings**:
- Asyncio mode: auto
- Test path: `tests/`
- Coverage tracking enabled

**Commands**:
```bash
pytest tests/ -v
pytest --cov=custom_components/temporary --cov-report=term-missing
pytest --cov=custom_components/temporary --cov-report=html
```

### Pre-commit Hooks

**Purpose**: Automated checks before each commit

**Configuration**: `.pre-commit-config.yaml`

**Hooks Enabled**:
- Ruff linting (with auto-fix)
- Ruff formatting
- MyPy type checking
- Standard pre-commit hooks (trailing whitespace, JSON/YAML validation, etc.)
- Codespell (spell checking)

**Commands**:
```bash
pre-commit install                # Install hooks
pre-commit run --all-files        # Run on all files
make pre-commit                   # Shortcut
```

## 📊 CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on push/PR:

1. **Lint Job**: Ruff linting and format checking
2. **Type Check Job**: MyPy type checking
3. **Validate Job**: Integration validation
4. **Test Job**: Pytest on Python 3.12 and 3.13 with coverage

All checks must pass before merging.

## 🎯 Key Rules Aligned with HA Core

### Import Order (Ruff)
1. Future imports (`from __future__ import annotations`)
2. Standard library
3. Third-party packages
4. Home Assistant imports
5. Local imports

### Type Hints (MyPy)
- All public functions must have type hints
- Use `from __future__ import annotations` for forward references
- Return types required
- Strict mode enabled

### Docstrings (Ruff D-rules)
- Google-style docstrings
- Required for all public modules, classes, functions
- Short description on first line
- Longer description if needed
- Args, Returns, Raises sections as appropriate

### Naming (Ruff N-rules)
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Private members: `_leading_underscore`

## 🔧 Common Commands

| Command | Description |
|---------|-------------|
| `pip install -r requirements_dev.txt` | Install development dependencies |
| `ruff check .` | Run ruff linter |
| `ruff format .` | Format code with ruff |
| `ruff format --check .` | Check formatting without changes |
| `mypy custom_components/temporary` | Run mypy type checker |
| `pytest tests/ -v` | Run pytest tests |
| `python validate.py` | Run integration validation |
| `pre-commit run --all-files` | Run all pre-commit hooks |
| `ruff check . && ruff format --check . && mypy custom_components/temporary` | Run all checks |
| `ruff format . && ruff check --fix .` | Auto-fix formatting and linting |

## 📝 VS Code Integration

The project includes VS Code configuration for seamless development:

### Settings (`.vscode/settings.json`)
- Ruff as default linter and formatter
- Format on save enabled
- Auto-organize imports on save
- MyPy type checking enabled
- Pytest integration
- Exclude cache directories

### Recommended Extensions (`.vscode/extensions.json`)
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)
- MyPy (ms-python.mypy-type-checker)
- Error Lens (usernamehw.errorlens)
- GitHub Actions (github.vscode-github-actions)
- YAML (redhat.vscode-yaml)
- TOML (tamasfe.even-better-toml)

## 🆚 Changes from Original Setup

### Replaced
- ❌ **flake8** → ✅ **ruff** (faster, more features)
- ❌ **black** → ✅ **ruff format** (compatible replacement)
- ❌ **isort** → ✅ **ruff** (includes import sorting)
- ❌ **.isortcfg** → ✅ **pyproject.toml** [tool.ruff.lint.isort]

### Added
- ✅ **MyPy** - Type checking
- ✅ **Pylint** - Additional code analysis
- ✅ **Pre-commit** - Automated hooks
- ✅ **Pytest** - Testing framework
- ✅ **Coverage** - Code coverage tracking
- ✅ **CI/CD** - GitHub Actions workflow
- ✅ **VS Code config** - Editor integration

### Upgraded
- ✅ All configurations aligned with Home Assistant core 2026.3.0.dev0
- ✅ Ruff 0.15.0+ with latest rule set
- ✅ Python 3.12+ target (with 3.13 support)

## 📖 Documentation

- **CONTRIBUTING.md**: Full contribution guidelines
- **README.md**: Updated Development section
- **This file**: Linting setup summary

## 🎓 Learning Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Pre-commit Documentation](https://pre-commit.com/)

## ✅ Next Steps

1. **Install development environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements_dev.txt
   pre-commit install
   ```

2. **Run initial checks**:
   ```bash
   ruff check . && ruff format --check . && mypy custom_components/temporary
   ```

3. **Fix any issues found**:
   ```bash
   ruff format . && ruff check --fix .
   ```

4. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

5. **Start developing** with confidence that code quality is maintained!

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full contribution guidelines.

## 📞 Support

If you encounter any issues with the linting setup:
1. Check this document
2. Review [CONTRIBUTING.md](CONTRIBUTING.md)
3. Check tool documentation
4. Open an issue on GitHub

---

**Last Updated**: February 2026
**Aligned With**: Home Assistant core 2026.3.0.dev0
**Ruff Version**: >= 0.15.0
