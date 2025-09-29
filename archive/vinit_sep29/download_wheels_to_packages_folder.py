#!/usr/bin/env python3
"""
Download all required wheels (and dependencies) for offline installation.
Wheels are downloaded for the current architecture and moved to packages_folder.
Run this script on your Raspberry Pi for correct architecture wheels.
"""
import subprocess
from pathlib import Path
import shutil
import sys


script_dir = Path(__file__).parent.absolute()
packages_folder = script_dir / "packages_folder"
temp_download_dir = script_dir / "_temp_wheels_download"

import argparse
parser = argparse.ArgumentParser(description="Download wheels for a single package and dependencies.")
parser.add_argument("package", nargs="?", default="paramiko", help="Package name to download (default: paramiko)")
args = parser.parse_args()
package_name = args.package

# Ensure packages_folder exists
packages_folder.mkdir(exist_ok=True)
# Create temp download dir
if temp_download_dir.exists():
    shutil.rmtree(temp_download_dir)
temp_download_dir.mkdir(exist_ok=True)

print(f"Downloading wheels for '{package_name}' to temporary folder: {temp_download_dir}")

# Download wheels for the specified package and dependencies
cmd = [
    sys.executable, "-m", "pip", "download",
    package_name,
    "--only-binary=:all:",
    "--dest", str(temp_download_dir)
]
result = subprocess.run(cmd)
if result.returncode != 0:
    print(f"pip download failed for {package_name}. Check your internet connection and package name.")
    sys.exit(result.returncode)

# Move all .whl files to packages_folder
for whl_file in temp_download_dir.glob("*.whl"):
    shutil.move(str(whl_file), str(packages_folder / whl_file.name))
    print(f"Moved: {whl_file.name} -> {packages_folder}")

# Clean up temp dir
shutil.rmtree(temp_download_dir)
print(f"All wheels for '{package_name}' downloaded and moved to packages_folder.")
