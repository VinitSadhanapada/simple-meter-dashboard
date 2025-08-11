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
import requests

# --- Config ---
DB_CONFIG = {
    'dbname': 'mfmdb',
    'user': 'mfmuser',
    'password': 'devi',
    'host': '192.168.43.127',  # or your DB server IP
    'port': 5432
}

# Server config for posting data
SERVER_CONFIG = {
    'url': 'http://192.168.43.127:8000/api/meter/',
    'enabled': True,  # Set to False to disable server posting
    'timeout': 10,    # Request timeout in seconds
    'retry_attempts': 3
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
                    
                    # Insert into database
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
                    
                    # Post to server
                    post_to_server(meter_data)
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


def post_to_server(meter_data):
    """Post meter data to the server API endpoint."""
    if not SERVER_CONFIG['enabled']:
        return
    
    try:
        # Prepare data in the format expected by the server
        server_data = {
            'device_id': str(meter_data.get("Device_ID", "")),
            'location': meter_data.get("Location", ""),
            'meter_name': meter_data.get("Meter_Name", ""),
            'time': meter_data.get("Time", ""),
            'model': meter_data.get("Model", ""),
            'watts_total': float_or_none(meter_data.get("Watts Total")),
            'watts_r_ph': float_or_none(meter_data.get("Watts R Ph")),
            'watts_y_ph': float_or_none(meter_data.get("Watts Y Ph")),
            'watts_b_ph': float_or_none(meter_data.get("Watts B Ph")),
            'pf_ave': float_or_none(meter_data.get("PF Ave")),
            'pf_r_ph': float_or_none(meter_data.get("PF R Ph")),
            'pf_y_ph': float_or_none(meter_data.get("PF Y Ph")),
            'pf_b_ph': float_or_none(meter_data.get("PF B Ph")),
            'vln_average': float_or_none(meter_data.get("VLN average")),
            'v_r_ph': float_or_none(meter_data.get("V R Ph")),
            'v_y_ph': float_or_none(meter_data.get("V Y Ph")),
            'v_b_ph': float_or_none(meter_data.get("V B Ph")),
            'a_average': float_or_none(meter_data.get("A average")),
            'a_r_ph': float_or_none(meter_data.get("A R Ph")),
            'a_y_ph': float_or_none(meter_data.get("A Y Ph")),
            'a_b_ph': float_or_none(meter_data.get("A B Ph")),
            'frequency': float_or_none(meter_data.get("Frequency")),
            'wh_received': float_or_none(meter_data.get("Wh received")),
            'load_hours_delivered': float_or_none(meter_data.get("Load Hours Delivered")),
            'no_of_interruption': float_or_none(meter_data.get("No of interruption")),
            'on_hours': meter_data.get("On Hours"),
            'v_r_harmonics': float_or_none(meter_data.get("V R Harmonics")),
            'v_y_harmonics': float_or_none(meter_data.get("V Y Harmonics")),
            'v_b_harmonics': float_or_none(meter_data.get("V B Harmonics")),
            'a_r_harmonics': float_or_none(meter_data.get("A R Harmonics")),
            'a_y_harmonics': float_or_none(meter_data.get("A Y Harmonics")),
            'a_b_harmonics': float_or_none(meter_data.get("A B Harmonics"))
        }
        
        # Remove None values to reduce payload size
        server_data = {k: v for k, v in server_data.items() if v is not None}
        
        for attempt in range(SERVER_CONFIG['retry_attempts']):
            try:
                response = requests.post(
                    SERVER_CONFIG['url'],
                    json=server_data,
                    timeout=SERVER_CONFIG['timeout']
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    logger.info(f"Successfully posted data to server for {meter_data.get('Meter_Name', 'unknown')}")
                    return
                else:
                    logger.warning(f"Server returned status {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout posting to server (attempt {attempt + 1}/{SERVER_CONFIG['retry_attempts']})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error posting to server (attempt {attempt + 1}/{SERVER_CONFIG['retry_attempts']})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error posting to server (attempt {attempt + 1}/{SERVER_CONFIG['retry_attempts']}): {e}")
            
            if attempt < SERVER_CONFIG['retry_attempts'] - 1:
                time.sleep(2)  # Wait 2 seconds before retry
                
        logger.error(f"Failed to post data to server after {SERVER_CONFIG['retry_attempts']} attempts")
        
    except Exception as e:
        logger.error(f"Unexpected error posting to server: {e}")


if __name__ == "__main__":
    main()
