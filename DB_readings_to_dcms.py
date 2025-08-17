import time
import json
import re
from pathlib import Path
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'device_config_manager.settings')
django.setup()
from device_manager.models import MeterReading

# --- Original DB_readings logic for fetching readings ---
# All code related to PostgresHelper and old DB removed.
# This script is now deprecated and can be deleted or archived.

def strip_jsonc_comments(text):
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text

config_path = Path(__file__).parent.absolute() / "config.jsonc"
with open(config_path, 'r') as f:
    config = json.loads(strip_jsonc_comments(f.read()))

try:
    while True:
        print("\n--- Waiting for new data ---\n")
        time.sleep(5)  # Check every 5 seconds
except KeyboardInterrupt:
    print("Stopped monitoring.")
