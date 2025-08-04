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
    'host': 'localhost',  # or your DB server IP
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
    # Setup meters by location
    location_meters = defaultdict(list)
    for device_config in DEVICE_CONFIG:
        location = device_config.get("location", "Unknown")
        meter = MeterDevice(
            name=device_config["name"],
            model=device_config["model"],
            parameters=PARAMETERS,
            client=None,  # Set up Modbus client as needed
            error_file=None,
            simulation_mode=CONFIG["SIMULATION_MODE"],
            device_address=device_config["address"]
        )
        location_meters[location].append(meter)

    managers = []
    for location, meters in location_meters.items():
        clean_location = "".join(
            c for c in location if c.isalnum() or c in ('-', '_'))
        csv_file = CSV_DIR / f"{clean_location}.csv"
        manager = MeterManager(
            meters, PARAMETERS, [str(csv_file)],
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
                # Read all meters for this location
                manager.read_all(
                    inter_device_delay=CONFIG["INTER_DEVICE_DELAY"])
                # Get latest row for each meter and write to DB
                with open(csv_file, "r") as f:
                    reader = list(csv.reader(f))
                    if len(reader) < 2:
                        continue  # No data yet
                    header = reader[0]
                    for row in reader[-len(meters):]:
                        row_dict = dict(zip(header, row))
                        # Map CSV columns to DB insert
                        insert_meter_reading(
                            db,
                            row_dict.get("Device_ID"),
                            row_dict.get("Meter_Name"),
                            row_dict.get("Time"),
                            row_dict.get("Model"),
                            float_or_none(row_dict.get("Watts Total")),
                            float_or_none(row_dict.get("Watts R Ph")),
                            float_or_none(row_dict.get("Watts Y Ph")),
                            float_or_none(row_dict.get("Watts B Ph")),
                            float_or_none(row_dict.get("PF Ave")),
                            float_or_none(row_dict.get("PF R Ph")),
                            float_or_none(row_dict.get("PF Y Ph")),
                            float_or_none(row_dict.get("PF B Ph")),
                            float_or_none(row_dict.get("VLN average")),
                            float_or_none(row_dict.get("V R Ph")),
                            float_or_none(row_dict.get("V Y Ph")),
                            float_or_none(row_dict.get("V B Ph")),
                            float_or_none(row_dict.get("A average")),
                            float_or_none(row_dict.get("A R Ph")),
                            float_or_none(row_dict.get("A Y Ph")),
                            float_or_none(row_dict.get("A B Ph")),
                            float_or_none(row_dict.get("Frequency")),
                            float_or_none(row_dict.get("Wh received")),
                            float_or_none(row_dict.get(
                                "Load Hours Delivered")),
                            float_or_none(row_dict.get("No of interruption")),
                            float_or_none(row_dict.get("On Hours")),
                            float_or_none(row_dict.get("V R Harmonics")),
                            float_or_none(row_dict.get("V Y Harmonics")),
                            float_or_none(row_dict.get("V B Harmonics")),
                            float_or_none(row_dict.get("A R Harmonics")),
                            float_or_none(row_dict.get("A Y Harmonics")),
                            float_or_none(row_dict.get("A B Harmonics"))
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
