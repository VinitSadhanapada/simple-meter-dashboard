#!/usr/bin/env python3
"""
Offline RPi Dashboard - DB Version
Writes meter readings to both CSV and PostgreSQL DB for all locations/devices.
"""
from pathlib import Path
from datetime import datetime
import logging
import time
import sys
import os
import argparse
from postgres_helper import PostgresHelper, create_meter_table, insert_meter_reading
from macros import PARAMETERS
from meter_manager import MeterManager
from meter_device import MeterDevice
from collections import defaultdict
import csv
import json

# --- Config ---
DB_CONFIG = {
    'dbname': 'mfmdb',
    'user': 'mfmuser',
    'password': 'devi',
    'host': '172.20.10.2',  # or your DB server IP
    'port': 5432
}

script_dir = Path(__file__).parent.absolute()
CONFIG_PATH = script_dir / "config.jsonc"
DEVICE_CONFIG_PATH = script_dir / "device_config.jsonc"
CSV_DIR = script_dir / "csv_data"
CSV_DIR.mkdir(exist_ok=True)

# --- Load config ---


def strip_jsonc_comments(text):
    import re
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def load_jsonc_config(path):
    with open(path, 'r') as f:
        content = f.read()
        return json.loads(strip_jsonc_comments(content))


CONFIG = load_jsonc_config(CONFIG_PATH)
DEVICE_CONFIG = load_jsonc_config(DEVICE_CONFIG_PATH)

# --- Setup logging ---
log_dir = script_dir / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"dashboard_db_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dashboard_db")

# --- Setup DB ---
db = PostgresHelper(**DB_CONFIG)
db.connect()
create_meter_table(db)

# --- Main ---


def main():
    logger.info("Starting dashboard DB version...")
    # Setup pymodbus ModbusSerialClient
    from pymodbus.client.sync import ModbusSerialClient as ModbusClient
    client = None
    port_exists = os.path.exists(CONFIG["PORT"])
    simulation_mode = CONFIG["SIMULATION_MODE"]
    use_default = False
    if not simulation_mode:
        if port_exists:
            try:
                client = ModbusClient(
                    method="rtu", port=CONFIG["PORT"],
                    stopbits=1, bytesize=8, parity='E',
                    baudrate=9600, timeout=0.5
                )
                if client.connect():
                    logger.info(f"Connected to {CONFIG['PORT']}")
                else:
                    logger.warning(
                        "Failed to connect, will use default value -1 for all readings.")
                    use_default = True
            except Exception as e:
                logger.error(
                    f"Hardware error: {e}, will use default value -1 for all readings.")
                use_default = True
        else:
            logger.warning(
                f"Port {CONFIG['PORT']} not found, will use default value -1 for all readings.")
            use_default = True
    # Setup meters by location
    location_meters = defaultdict(list)
    for device_config in DEVICE_CONFIG:
        location = device_config.get("location", "Unknown")
        meter = MeterDevice(
            name=device_config["name"],
            model=device_config["model"],
            parameters=PARAMETERS,
            client=client,
            error_file=None,
            simulation_mode=simulation_mode,
            device_address=device_config["address"]
        )
        # Patch: If not simulation_mode and use_default, override meter to always return -1 for all params
        if not simulation_mode and use_default:
            def always_minus_one(*args, **kwargs):
                return [-1 for _ in PARAMETERS]
            meter.read_parameters = always_minus_one
        location_meters[location].append(meter)

    managers = []
    for location, meters in location_meters.items():
        clean_location = "".join(
            c for c in location if c.isalnum() or c in ('-', '_'))
        csv_file = CSV_DIR / f"{clean_location}.csv"
        manager = MeterManager(
            meters, PARAMETERS, [str(csv_file)],
            location=location,
            mqtt_client=None,  # Add MQTT if needed
            publish_mqtt=False
        )
        managers.append((location, manager, csv_file, meters))
        logger.info(
            f"Location '{location}': {len(meters)} devices, CSV: {csv_file}")

    # Main loop
    try:
        while True:
            for location, manager, csv_file, meters in managers:
                # Generate a single timestamp for all meters in this reading cycle
                reading_time = datetime.now().isoformat()
                meter_data_list = manager.read_all(
                    inter_device_delay=CONFIG["INTER_DEVICE_DELAY"],
                    reading_time=reading_time
                )
                for meter_data in meter_data_list:
                    meter_data["Location"] = location
                    meter_data["Time"] = reading_time
                    print(f"DEBUG: meter_data before DB insert: {meter_data}")
                    # Handle On Hours for different meter models
                    on_hours_val = meter_data.get("On Hours")
                    if meter_data.get("Model") == "LG+5220" and (on_hours_val in [None, "", "00:00:00"]):
                        on_hours_val = None
                    insert_meter_reading(
                        db,
                        meter_data.get("Location"),
                        meter_data.get("Device_ID"),
                        meter_data.get("Meter_Name"),
                        meter_data.get("Time"),
                        meter_data.get("Model"),
                        float_or_none(meter_data.get("Watts Total")),
                        float_or_none(meter_data.get("Watts R Ph")),
                        float_or_none(meter_data.get("Watts Y Ph")),
                        float_or_none(meter_data.get("Watts B Ph")),
                        float_or_none(meter_data.get("PF Ave")),
                        float_or_none(meter_data.get("PF R Ph")),
                        float_or_none(meter_data.get("PF Y Ph")),
                        float_or_none(meter_data.get("PF B Ph")),
                        float_or_none(meter_data.get("VLN average")),
                        float_or_none(meter_data.get("V R Ph")),
                        float_or_none(meter_data.get("V Y Ph")),
                        float_or_none(meter_data.get("V B Ph")),
                        float_or_none(meter_data.get("A average")),
                        float_or_none(meter_data.get("A R Ph")),
                        float_or_none(meter_data.get("A Y Ph")),
                        float_or_none(meter_data.get("A B Ph")),
                        float_or_none(meter_data.get("Frequency")),
                        float_or_none(meter_data.get("Wh received")),
                        float_or_none(meter_data.get("Load Hours Delivered")),
                        float_or_none(meter_data.get("No of interruption")),
                        on_hours_val,
                        float_or_none(meter_data.get("V R Harmonics")),
                        float_or_none(meter_data.get("V Y Harmonics")),
                        float_or_none(meter_data.get("V B Harmonics")),
                        float_or_none(meter_data.get("A R Harmonics")),
                        float_or_none(meter_data.get("A Y Harmonics")),
                        float_or_none(meter_data.get("A B Harmonics"))
                    )
            time.sleep(CONFIG["READING_INTERVAL"])
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user.")
    finally:
        db.close()


def float_or_none(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
