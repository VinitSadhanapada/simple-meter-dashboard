#!/usr/bin/env python3
"""
Offline Package Preparation Script

This script downloads all required packages for offline deployment.
Run this on a machine with internet connectivity before deploying
to air-gapped systems.

Usage:
    python prepare_offline.py
    
The script will create an 'offline_packages' directory with all
dependencies that can be transferred to offline systems.
"""

import sys
from pathlib import Path

# Import our venv utilities
try:
    from venv_utils import download_packages_for_offline_use
except ImportError:
    print("❌ Error: venv_utils.py not found in current directory")
    sys.exit(1)

def main():
    """Main function to prepare offline packages."""
    
    print("🌐 Offline Package Preparation for Meter Dashboard")
    print("=" * 50)
    
    # Define all required packages for the meter dashboard
    required_packages = [
        "pymodbus==2.5.3",
        "pyserial==3.5", 
        "paho-mqtt==2.1.0",
        "termcolor==3.1.0",
        "numpy==1.24.3",
        "pandas==2.0.3"
    ]
    
    print("📦 Required packages:")
    for pkg in required_packages:
        print(f"   - {pkg}")
    print()
    
    # Download packages
    success = download_packages_for_offline_use(
        packages=required_packages,
        download_dir="offline_packages"
    )
    
    if success:
        print("\n✅ Offline package preparation complete!")
        print("\n📋 Next steps:")
        print("1. Copy the 'offline_packages' directory to your target system")
        print("2. On the target system, run:")
        print("   python print_dashboard2.py --setup-venv --offline")
        print("   OR")
        print("   python simple_rpi_dashboard.py (will auto-detect offline packages)")
        print("\n📁 Files created:")
        offline_dir = Path("offline_packages")
        if offline_dir.exists():
            files = list(offline_dir.glob("*"))
            for file in files:
                print(f"   - {file.name}")
    else:
        print("\n❌ Offline package preparation failed!")
        print("Check your internet connection and try again.")

if __name__ == "__main__":
    main()
