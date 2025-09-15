#!/usr/bin/env python3
"""
Offline RPi Dashboard - DB Version (Modularized)
Writes meter readings to both CSV and PostgreSQL DB for all locations/devices.
"""
from pathlib import Path
from datetime import datetime
import logging
import time
import sys
import os
import csv
import json
import paho.mqtt.client as mqtt

# --- Config ---
# DB_CONFIG = {
#     'dbname': 'mfmdb',
#     'user': 'mfmuser',
#     'password': 'devi',
#     'host': '172.20.10.3',  # will be set after config load
#     'port': '5432',
# }

# Server config for posting data
SERVER_CONFIG = {
    'url': None,  # will be set after config load
    'enabled': False,  # Set to False to disable server posting
    'timeout': 10,    # Request timeout in seconds
    'retry_attempts': 3
}

script_dir = Path(__file__).parent.absolute()
CONFIG_PATH = script_dir / "config.json"
DEVICE_CONFIG_PATH = script_dir / "device_config.json"
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
# Remove DB_CONFIG['host'] assignment since DB_CONFIG is not used anymore
# SERVER_CONFIG['url'] and SERVER_CONFIG['enabled'] lines remain
SERVER_CONFIG['url'] = f"http://{CONFIG.get('SERVER_API_IP', 'localhost')}:8000/api/meter/"
# Ensure server posting is disabled to avoid connection errors
SERVER_CONFIG['enabled'] = False
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

# --- Main Dashboard Logic ---


def run_dashboard():
    from macros import PARAMETERS
    from meter_manager import MeterManager
    from meter_device import MeterDevice
    from collections import defaultdict
    import requests
    import socket
    from pymodbus.client.sync import ModbusSerialClient as ModbusClient

    # Simple Pi details extraction from existing configs
    pi_name = socket.gethostname()  # Get Pi hostname
    pi_location = "Unknown"
    pi_ip = "10.252.27.59"

    # Extract Pi details from device_config.json (first device)
    if DEVICE_CONFIG and len(DEVICE_CONFIG) > 0:
        first_device = DEVICE_CONFIG[0]
        pi_location = first_device.get('location', 'Unknown')
        pi_name = first_device.get('pi_name', pi_name)
        pi_ip = first_device.get('pi_ip', pi_ip)

    logger.info("Starting dashboard DB version (MQTT only)...")
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
        meter_name = device_config.get(
            "meter_name", device_config.get("name", "Unknown"))
        meter_address = device_config.get(
            "meter_address", device_config.get("address", 1))
        meter_model = device_config.get(
            "meter_model", device_config.get("model", "LG6400"))

        meter = MeterDevice(
            name=meter_name,
            model=meter_model,
            parameters=PARAMETERS,
            client=client,
            error_file=None,
            simulation_mode=simulation_mode,
            device_address=meter_address
        )

        if not simulation_mode and use_default:
            def always_minus_one(*args, **kwargs):
                return [-1 for _ in PARAMETERS]
            meter.read_data = always_minus_one

        location_meters[location].append(meter)

    ENABLE_CSV_WRITE = CONFIG.get("ENABLE_CSV_WRITE", False)
    managers = []
    for location, meters in location_meters.items():
        clean_location = "".join(
            c for c in location if c.isalnum() or c in ('-', '_'))
        csv_file = CSV_DIR / f"{clean_location}.csv"
        csv_file_arg = [str(csv_file)] if ENABLE_CSV_WRITE else ["/dev/null"]
        manager = MeterManager(
            meters, PARAMETERS, csv_file_arg,
            location=location,
            mqtt_client=None,  # Add MQTT if needed
            publish_mqtt=False
        )
        managers.append((location, manager, csv_file, meters))
        logger.info(
            f"Location '{location}': {len(meters)} devices, CSV: {csv_file if ENABLE_CSV_WRITE else 'DISABLED'}")

    # MQTT Config (set your broker IP/credentials)
    MQTT_BROKER = CONFIG.get('MQTT_BROKER_IP', 'localhost')
    MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
    MQTT_USER = 'myuser'
    MQTT_PASS = 'Mahadev@123'
    MQTT_TOPIC = 'meter/readings'

    def publish_meter_reading_mqtt(meter_data):
        client = mqtt.Client()
        if MQTT_USER and MQTT_PASS:
            client.username_pw_set(MQTT_USER, MQTT_PASS)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        payload = json.dumps(meter_data)
        client.publish(MQTT_TOPIC, payload)
        client.disconnect()

    # Main loop
    try:
        while True:
            for location, manager, csv_file, meters in managers:
                reading_time = datetime.now().isoformat()
                meter_data_list = manager.read_all(
                    inter_device_delay=CONFIG["INTER_DEVICE_DELAY"]
                )

                for meter_data in meter_data_list:
                    # Remove the capital-L Location field, only use lowercase for DB
                    # meter_data["Location"] = location  # Removed
                    # DB expects lowercase 'time'
                    meter_data["time"] = reading_time
                    meter_data["pi_name"] = pi_name
                    meter_data["pi_ip"] = pi_ip
                    meter_data["location"] = location
                    meter_data["device_id"] = meter_address
                    meter_data["meter_name"] = meter_name
                    meter_data["model"] = meter_data.get("Model", "")
                    meter_data["watts_total"] = meter_data.get(
                        "Watts Total", None)
                    meter_data["watts_r_ph"] = meter_data.get(
                        "Watts R Ph", None)
                    meter_data["watts_y_ph"] = meter_data.get(
                        "Watts Y Ph", None)
                    meter_data["watts_b_ph"] = meter_data.get(
                        "Watts B Ph", None)
                    meter_data["pf_ave"] = meter_data.get("PF Ave", None)
                    meter_data["pf_r_ph"] = meter_data.get("PF R Ph", None)
                    meter_data["pf_y_ph"] = meter_data.get("PF Y Ph", None)
                    meter_data["pf_b_ph"] = meter_data.get("PF B Ph", None)
                    meter_data["vln_average"] = meter_data.get(
                        "VLN average", None)
                    meter_data["v_r_ph"] = meter_data.get("V R Ph", None)
                    meter_data["v_y_ph"] = meter_data.get("V Y Ph", None)
                    meter_data["v_b_ph"] = meter_data.get("V B Ph", None)
                    meter_data["a_average"] = meter_data.get("A average", None)
                    meter_data["a_r_ph"] = meter_data.get("A R Ph", None)
                    meter_data["a_y_ph"] = meter_data.get("A Y Ph", None)
                    meter_data["a_b_ph"] = meter_data.get("A B Ph", None)
                    meter_data["frequency"] = meter_data.get("Frequency", None)
                    meter_data["wh_received"] = meter_data.get(
                        "Wh received", None)
                    meter_data["load_hours_delivered"] = meter_data.get(
                        "Load Hours Delivered", None)
                    meter_data["no_of_interruption"] = meter_data.get(
                        "No of interruption", None)
                    meter_data["on_hours"] = meter_data.get("On Hours", None)
                    meter_data["v_r_harmonics"] = meter_data.get(
                        "V R Harmonics", None)
                    meter_data["v_y_harmonics"] = meter_data.get(
                        "V Y Harmonics", None)
                    meter_data["v_b_harmonics"] = meter_data.get(
                        "V B Harmonics", None)
                    meter_data["a_r_harmonics"] = meter_data.get(
                        "A R Harmonics", None)
                    meter_data["a_y_harmonics"] = meter_data.get(
                        "A Y Harmonics", None)
                    meter_data["a_b_harmonics"] = meter_data.get(
                        "A B Harmonics", None)
                    print(
                        f"DEBUG: meter_data before MQTT publish: {meter_data}")

                    on_hours_val = meter_data.get("On Hours")
                    if meter_data.get("Model") == "LG+5220" and (on_hours_val in [None, "", "00:00:00"]):
                        on_hours_val = None

                    publish_meter_reading_mqtt(meter_data)

            logger.info(
                f"💤 Waiting {CONFIG['READING_INTERVAL']} seconds for next reading cycle...")
            time.sleep(CONFIG["READING_INTERVAL"])

    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user.")
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    import sys
    import subprocess
    if '--install' in sys.argv:
        print("Delegating --install to offline_rpi_dashboard.py...")
        script_dir = Path(__file__).parent.absolute()
        dashboard_script = script_dir / 'offline_rpi_dashboard.py'
        result = subprocess.run(
            [sys.executable, str(dashboard_script), '--install'])
        sys.exit(result.returncode)
    elif '--run' in sys.argv or len(sys.argv) == 1:
        run_dashboard()
    else:
        print("Unknown argument. Use --install or --run.")
