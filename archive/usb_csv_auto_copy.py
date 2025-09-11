#!/usr/bin/env python3
"""
Script to monitor for USB drive insertion and automatically copy all CSV files from the dashboard's csv_data directory to the USB drive.
After copying, it creates an empty 'done' file on the USB to indicate success.

Usage: Run this script in the background on the RPi.
"""

from datetime import datetime
import os
import time
import shutil
import json
import re
from pathlib import Path

# CONFIGURABLE PATHS
CSV_DIR = Path(__file__).parent / 'csv_data'
USB_MOUNT_BASE = Path('/media')  # Typical mount point for USB drives on RPi
DONE_FILENAME = 'done'
POLL_INTERVAL = 2  # seconds
DEVICE_CONFIG_PATH = Path(__file__).parent / 'device_config.json'

# Helper to strip comments from JSONC


def strip_jsonc_comments(text):
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text

# Get the set of CSV files that are being written by the dashboard (per location)


def get_active_csv_files():
    if not DEVICE_CONFIG_PATH.exists():
        return set()
    with open(DEVICE_CONFIG_PATH, 'r') as f:
        config = json.loads(strip_jsonc_comments(f.read()))
    locations = set(d.get('location', 'Unknown') for d in config)
    # Clean location names as in dashboard
    clean_names = set(''.join(c for c in loc if c.isalnum()
                      or c in ('-', '_')) for loc in locations)
    return set(f"{name}.csv" for name in clean_names)


def find_usb_mount():
    """
    Returns the path to the first detected USB mount, or None if not found.
    """
    if not USB_MOUNT_BASE.exists():
        return None
    for user_dir in USB_MOUNT_BASE.iterdir():
        if user_dir.is_dir():
            # Look for subdirs (actual USB mount points)
            for mount in user_dir.iterdir():
                if mount.is_dir() and os.access(mount, os.W_OK):
                    return mount
    return None


def copy_csv_to_usb(usb_path):
    """
    Copy all CSV files from CSV_DIR to the USB drive.
    """
    if not CSV_DIR.exists():
        print(f"CSV directory {CSV_DIR} does not exist.")
        return False
    copied = False
    active_csvs = get_active_csv_files()
    for csv_file in CSV_DIR.glob('*.csv'):
        if csv_file.name not in active_csvs:
            continue
        dest = usb_path / csv_file.name
        try:
            shutil.copy2(csv_file, dest)
            print(f"Copied {csv_file} to {dest}")
            copied = True
        except Exception as e:
            print(f"Failed to copy {csv_file} to USB: {e}")
    return copied


def touch_done_file(usb_path):
    # Delete any existing done_* files first
    for f in usb_path.glob(f"{DONE_FILENAME}_*"):
        try:
            f.unlink()
            print(f"Deleted old done file: {f}")
        except Exception as e:
            print(f"Failed to delete old done file {f}: {e}")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    done_filename = f"{DONE_FILENAME}_{timestamp}"
    done_path = usb_path / done_filename
    try:
        done_path.touch()
        print(f"Created done file: {done_path}")
    except Exception as e:
        print(f"Failed to create done file: {e}")


def main():
    print("[USB CSV Auto Copy] Monitoring for USB drive...")
    last_usb = None
    while True:
        usb_mount = find_usb_mount()
        if usb_mount and usb_mount != last_usb:
            print(f"USB detected at {usb_mount}")
            if copy_csv_to_usb(usb_mount):
                touch_done_file(usb_mount)
            last_usb = usb_mount
        elif not usb_mount:
            last_usb = None
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
