import os
from pathlib import Path

base = Path(__file__).parent
scripts_dir = base / 'test_scripts'

if scripts_dir.exists():
    for pyfile in scripts_dir.glob('*.py'):
        dst = base / pyfile.name
        pyfile.rename(dst)
        print(f"Moved back: {pyfile.name} -> {base}")
else:
    print("test_scripts directory does not exist.")

print("All scripts have been moved back to the main directory.")
