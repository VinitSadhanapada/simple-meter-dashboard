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

# --- Config ---
DB_CONFIG = {
    'dbname': 'mfmdb',
    'user': 'mfmuser',
    'password': 'devi',
    'host': '172.20.10.3',  # will be set after config load
    'port': '5432',
}

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
# Use PSQL_SERVER_ADDRESS from config if present, else fallback to DB_SERVER_IP, else localhost
DB_CONFIG['host'] = CONFIG.get(
    'PSQL_SERVER_ADDRESS', CONFIG.get('DB_SERVER_IP', 'localhost'))
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


# Simple table creation function
def create_pi_setup_table_simple(db):
    """Create dcms_pi_setup table with essential fields only"""
    query = """
    CREATE TABLE IF NOT EXISTS dcms_pi_setup (
        id SERIAL PRIMARY KEY,
        pi_name VARCHAR(100) UNIQUE NOT NULL,
        pi_ip INET UNIQUE NOT NULL,
        location VARCHAR(100) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        last_connected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_location ON dcms_pi_setup(location);
    """

    try:
        cursor = db.conn.cursor()
        cursor.execute(query)
        db.conn.commit()
        logger.info("✅ dcms_pi_setup table ready")
    except Exception as e:
        logger.error(f"❌ Error creating dcms_pi_setup table: {e}")


def register_pi_simple(db, pi_name, pi_ip, location):
    """Register/update this Pi in the database with all required DCMS fields"""

    query = """
    INSERT INTO dcms_pi_setup (
        pi_name, pi_ip, location, ssh_username, ssh_password, 
        ssh_key_path, config_path, is_active, last_connected
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (pi_name) 
    DO UPDATE SET 
        pi_ip = EXCLUDED.pi_ip,
        location = EXCLUDED.location,
        ssh_username = EXCLUDED.ssh_username,
        ssh_password = EXCLUDED.ssh_password,
        ssh_key_path = EXCLUDED.ssh_key_path,
        config_path = EXCLUDED.config_path,
        is_active = EXCLUDED.is_active,
        last_connected = CURRENT_TIMESTAMP
    RETURNING id;
    """

    try:
        cursor = db.conn.cursor()

        # Provide all required fields including config_path
        values = (
            pi_name,                                    # pi_name
            pi_ip,                                     # pi_ip
            location,                                  # location
            'pi',                                      # ssh_username
            # ssh_password (empty string)
            '',
            '/home/pi/.ssh/id_rsa',                   # ssh_key_path
            '/home/isha/deepak/MFM_offline_setup',    # config_path (required!)
            True                                       # is_active
        )

        cursor.execute(query, values)
        pi_setup_id = cursor.fetchone()[0]
        db.conn.commit()
        logger.info(f"✅ Pi registered: {pi_name}")
        return pi_setup_id

    except Exception as e:
        logger.error(f"❌ Error registering Pi: {e}")
        return None


def insert_meter_reading_with_pi_simple(db, pi_setup_id, location, device_id, meter_name, reading_time,
                                        model, watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
                                        pf_ave, pf_r_ph, pf_y_ph, pf_b_ph, vln_average, v_r_ph,
                                        v_y_ph, v_b_ph, a_average, a_r_ph, a_y_ph, a_b_ph,
                                        frequency, wh_received, load_hours_delivered,
                                        no_of_interruption, on_hours, v_r_harmonics, v_y_harmonics,
                                        v_b_harmonics, a_r_harmonics, a_y_harmonics, a_b_harmonics,
                                        pi_name=None, pi_ip=None):
    """Insert meter reading with Pi setup relationship and Pi details"""

    # First try to add columns if they don't exist
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'meter_readings' AND column_name = 'pi_setup_id') THEN
                    ALTER TABLE meter_readings ADD COLUMN pi_setup_id INTEGER;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'meter_readings' AND column_name = 'pi_name') THEN
                    ALTER TABLE meter_readings ADD COLUMN pi_name VARCHAR(100);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'meter_readings' AND column_name = 'pi_ip') THEN
                    ALTER TABLE meter_readings ADD COLUMN pi_ip INET;
                END IF;
            END $$;
        """)
        db.conn.commit()
    except Exception as e:
        logger.warning(f"⚠️  Could not add Pi columns: {e}")

    # Insert the reading with pi_setup_id and Pi details
    query = """
    INSERT INTO meter_readings (
        pi_setup_id, pi_name, pi_ip, location, device_id, meter_name, time, model,
        watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
        pf_ave, pf_r_ph, pf_y_ph, pf_b_ph,
        vln_average, v_r_ph, v_y_ph, v_b_ph,
        a_average, a_r_ph, a_y_ph, a_b_ph,
        frequency, wh_received, load_hours_delivered, no_of_interruption, on_hours,
        v_r_harmonics, v_y_harmonics, v_b_harmonics,
        a_r_harmonics, a_y_harmonics, a_b_harmonics
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """

    try:
        cursor = db.conn.cursor()
        cursor.execute(query, (
            pi_setup_id, pi_name, pi_ip, location, device_id, meter_name, reading_time, model,
            watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
            pf_ave, pf_r_ph, pf_y_ph, pf_b_ph,
            vln_average, v_r_ph, v_y_ph, v_b_ph,
            a_average, a_r_ph, a_y_ph, a_b_ph,
            frequency, wh_received, load_hours_delivered, no_of_interruption, on_hours,
            v_r_harmonics, v_y_harmonics, v_b_harmonics,
            a_r_harmonics, a_y_harmonics, a_b_harmonics
        ))
        db.conn.commit()
        logger.debug(f"✅ Inserted reading for Pi: {pi_name} ({pi_ip})")
    except Exception as e:
        logger.error(f"❌ Error inserting meter reading: {e}")
        db.conn.rollback()


def float_or_none(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def post_to_server(meter_data):
    import requests
    if not SERVER_CONFIG['enabled']:
        # Silently skip if disabled
        return True

    try:
        server_data = {k: v for k, v in {
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
        }.items() if v is not None}

        # Add server posting logic here if needed
        return True

    except Exception as e:
        logger.error(f"Unexpected error posting to server: {e}")
        return False


# Simple table creation function
def run_dashboard():
    # Import runtime dependencies only when running dashboard
    from postgres_helper import PostgresHelper, create_meter_table, insert_meter_reading
    from macros import PARAMETERS
    from meter_manager import MeterManager
    from meter_device import MeterDevice
    from collections import defaultdict
    import requests
    import socket
    from pymodbus.client.sync import ModbusSerialClient as ModbusClient

    # --- Setup DB ---
    logger.info(
        f"🔗 Connecting to PostgreSQL: {DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    db = PostgresHelper(**DB_CONFIG)
    db.connect()
    create_meter_table(db)

    # Simple Pi details extraction from existing configs
    pi_name = socket.gethostname()  # Get Pi hostname
    pi_location = "Unknown"
    pi_ip = "127.0.0.1"

    # Extract Pi details from device_config.jsonc (first device)
    if DEVICE_CONFIG and len(DEVICE_CONFIG) > 0:
        first_device = DEVICE_CONFIG[0]
        pi_location = first_device.get('location', 'Unknown')
        pi_name = first_device.get('pi_name', pi_name)
        pi_ip = first_device.get('pi_ip', pi_ip)

    # Create dcms_pi_setup table and register this Pi
    create_pi_setup_table_simple(db)
    pi_setup_id = register_pi_simple(db, pi_name, pi_ip, pi_location)

    logger.info("✅ PostgreSQL connection established and table ready")
    logger.info(f"🏷️  Pi registered: {pi_name} ({pi_ip}) in {pi_location}")

    logger.info("Starting dashboard DB version...")
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

        # Map the device config fields to what MeterDevice expects
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

        # Patch: If not simulation_mode and use_default, override meter to always return -1 for all params
        if not simulation_mode and use_default:
            def always_minus_one(*args, **kwargs):
                return [-1 for _ in PARAMETERS]
            meter.read_data = always_minus_one

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
                    inter_device_delay=CONFIG["INTER_DEVICE_DELAY"]
                )

                for meter_data in meter_data_list:
                    meter_data["Location"] = location
                    meter_data["Time"] = reading_time
                    print(f"DEBUG: meter_data before DB insert: {meter_data}")

                    # Handle On Hours for different meter models
                    on_hours_val = meter_data.get("On Hours")
                    if meter_data.get("Model") == "LG+5220" and (on_hours_val in [None, "", "00:00:00"]):
                        on_hours_val = None

                    # Insert into database with Pi relationship
                    logger.info(
                        f"💾 Inserting data into PostgreSQL for {meter_data.get('Meter_Name', 'unknown')} (Pi: {pi_name})")
                    insert_meter_reading_with_pi_simple(
                        db,
                        pi_setup_id,  # Link to this Pi
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
                        float_or_none(meter_data.get("A B Harmonics")),
                        pi_name=pi_name,  # Add Pi name
                        pi_ip=pi_ip       # Add Pi IP
                    )

                    # Post to server (if enabled)
                    post_to_server(meter_data)

            # Wait for next reading cycle
            logger.info(
                f"💤 Waiting {CONFIG['READING_INTERVAL']} seconds for next reading cycle...")
            time.sleep(CONFIG["READING_INTERVAL"])

    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user.")
    finally:
        if client:
            client.close()
        db.close()


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
