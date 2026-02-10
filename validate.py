#!/usr/bin/env python3
"""Validation script for Temporary Entities integration."""

import sys
from pathlib import Path

def validate_implementation():
    """Validate that all required files exist and have content."""
    
    base_path = Path(__file__).parent / "custom_components" / "temporary"
    
    required_files = {
        "manifest.json": "Integration metadata",
        "const.py": "Constants and configuration",
        "config_flow.py": "UI configuration flow",
        "entity.py": "Base TemporaryEntity class",
        "manager.py": "TemporaryEntityManager",
        "__init__.py": "Integration setup",
        "timer.py": "Timer platform",
        "services.yaml": "Service definitions",
        "strings.json": "UI strings",
        "translations/en.json": "English translations",
    }
    
    print("🔍 Validating Temporary Entities Implementation\n")
    print("=" * 60)
    
    all_valid = True
    
    for file_path, description in required_files.items():
        full_path = base_path / file_path
        
        if full_path.exists():
            size = full_path.stat().st_size
            if size > 0:
                print(f"✅ {file_path:<30} ({size:>6} bytes) - {description}")
            else:
                print(f"❌ {file_path:<30} (EMPTY!) - {description}")
                all_valid = False
        else:
            print(f"❌ {file_path:<30} (MISSING!) - {description}")
            all_valid = False
    
    print("=" * 60)
    
    if all_valid:
        print("\n✨ All required files are present and valid!")
        print("\n📋 Implementation Summary:")
        print("   - Foundation: manifest.json, const.py, config_flow.py")
        print("   - Core: entity.py, manager.py")
        print("   - Integration: __init__.py")
        print("   - Platform: timer.py")
        print("   - UI: services.yaml, strings.json, translations/")
        print("\n🚀 Ready to test in Home Assistant!")
        return 0
    else:
        print("\n❌ Some files are missing or empty!")
        return 1

if __name__ == "__main__":
    sys.exit(validate_implementation())
