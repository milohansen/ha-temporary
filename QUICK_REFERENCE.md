# Quick Reference: Linting & Validation Commands

## 🚀 Getting Started

```bash
# Setup (one-time)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements_dev.txt
pre-commit install
```

## ⚡ Quick Commands

```bash
# Check everything
ruff check . && ruff format --check . && mypy custom_components/temporary

# Auto-fix issues
ruff format . && ruff check --fix .

# Run tests
pytest tests/ -v

# Full check (like CI)
ruff check . && ruff format --check . && mypy custom_components/temporary && pytest tests/ -v
```

## 📋 Individual Tools

### Ruff (Linting & Formatting)
```bash
ruff check .              # Check for issues
ruff check --fix .        # Auto-fix issues
ruff format .             # Format code
ruff format --check .     # Check formatting only
```

### MyPy (Type Checking)
```bash
mypy custom_components/temporary
```

### Pytest (Testing)
```bash
pytest tests/ -v
pytest --cov=custom_components/temporary --cov-report=term-missing
pytest --cov=custom_components/temporary --cov-report=html
```

### Pre-commit (Automated Hooks)
```bash
pre-commit run --all-files
```

## 📊 Status Checks

```bash
python validate.py  # Validate integration structure
```

## 🧹 Cleanup

```bash
# Remove all cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null
rm -rf .coverage htmlcov/
```

## 💡 Tips

- **Before commit**: Let pre-commit hooks run automatically
- **Quick fix**: `ruff format . && ruff check --fix .`
- **CI testing**: Run the command from "Full check" above
- **VS Code**: Install recommended extensions for auto-formatting on save

## 🔗 More Info

- Full details: [LINTING_SETUP.md](LINTING_SETUP.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
