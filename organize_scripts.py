#!/usr/bin/env python3
"""
Cleanup and organize test scripts into separate directory
"""
import os
import shutil
from pathlib import Path


def organize_test_scripts():
    """Move all test/debug scripts to a separate directory"""

    main_dir = Path('/home/isha/deepak/MFM_offline_setup')
    test_dir = main_dir / 'test_scripts'

    # Create test directory
    test_dir.mkdir(exist_ok=True)

    # List of test/debug scripts to move
    test_scripts = [
        'debug_postgres_helper.py',
        'register_pi_enhanced.py',
        'register_pi_adaptive.py',
        'check_dcms_table.py',
        'fix_connection_refs.py',
        'debug_server_connection.py',
        'test_postgresql_data.py',
        'migrate_enhanced_tables.py',
        'dcms_integration_guide.py'
    ]

    moved_scripts = []
    kept_scripts = []

    for script in test_scripts:
        script_path = main_dir / script
        if script_path.exists():
            try:
                # Move to test directory
                shutil.move(str(script_path), str(test_dir / script))
                moved_scripts.append(script)
                print(f"📦 Moved: {script}")
            except Exception as e:
                print(f"❌ Error moving {script}: {e}")
                kept_scripts.append(script)
        else:
            print(f"⚠️  Not found: {script}")

    print(f"\n✅ Moved {len(moved_scripts)} test scripts to {test_dir}")
    print(f"📁 Test directory: {test_dir}")

    if kept_scripts:
        print(f"⚠️  Could not move: {kept_scripts}")

    # Create a README in test directory
    readme_content = """# Test Scripts Directory

This directory contains test, debug, and development scripts that are not part of the main application.

## Scripts:
- debug_postgres_helper.py - Debug PostgreSQL connection
- register_pi_*.py - Test Pi registration functions  
- check_dcms_table.py - Check database table structure
- test_postgresql_data.py - Test database connectivity
- migrate_enhanced_tables.py - Database migration scripts
- dcms_integration_guide.py - DCMS integration examples

## Usage:
These scripts are for testing and debugging only. The main application uses:
- offline_rpi_dashboard_db.py (main script)
- config.jsonc (configuration)
- device_config.jsonc (device setup)

## Cleanup:
You can safely delete this entire directory once development is complete.
"""

    readme_path = test_dir / 'README.md'
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    print(f"📝 Created README: {readme_path}")

    # Show clean main directory
    print(f"\n🧹 Clean main directory now contains:")
    main_files = [f.name for f in main_dir.iterdir(
    ) if f.is_file() and f.suffix in ['.py', '.jsonc']]
    for file in sorted(main_files):
        print(f"  ✅ {file}")


if __name__ == "__main__":
    print("🧹 Organizing test scripts...")
    organize_test_scripts()
    print("\n🎉 Directory cleanup complete!")
