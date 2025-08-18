import os
from pathlib import Path

# Define main scripts to keep in root (add more if needed)
main_scripts = {
    'complete_dcms_setup.py',
    'manage.py',
    'cleanup_debug_scripts.py',
}

base = Path(__file__).parent
scripts_dir = base / 'test_scripts'
scripts_dir.mkdir(exist_ok=True)

# Move all .py files except main scripts and __init__.py
for pyfile in base.glob('*.py'):
    if pyfile.name not in main_scripts and pyfile.name != '__init__.py':
        dst = scripts_dir / pyfile.name
        pyfile.rename(dst)
        print(f"Moved: {pyfile.name} -> test_scripts/")

# Reminder already exists
print("All non-main scripts have been moved to test_scripts/.")
