
# ...existing code...
def strip_jsonc_comments(text):
    import re
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text
def load_jsonc_config(path):
    with open(path, 'r') as f:
        content = f.read()
        return json.loads(strip_jsonc_comments(content))


# ...existing code...

def run_dashboard():

    # Import dependencies only after venv and package install
    import requests
    import paho.mqtt.client as mqtt
    from pymodbus.client.sync import ModbusSerialClient as ModbusClient
    from macros import PARAMETERS
    from meter_manager import MeterManager
    from meter_device import MeterDevice
    from collections import defaultdict
    import socket
    import os
    import json
    from pathlib import Path
    from datetime import datetime
    import logging
    import time

    # Load configs
    script_dir = Path(__file__).parent.absolute()
    CONFIG_PATH = script_dir / "config.json"
    DEVICE_CONFIG_PATH = Path("/home/pi/meter_config/device_config.json")
    CSV_DIR = script_dir / "csv_data"
    CSV_DIR.mkdir(exist_ok=True)

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

    # Setup logging
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

    # Simple Pi details extraction from existing configs
    pi_name = socket.gethostname()
    pi_ip = "10.146.184.59"  # default; will be overridden by device_config if present
    pi_location = 'Unknown'
    if DEVICE_CONFIG and len(DEVICE_CONFIG) > 0:
        first_device = DEVICE_CONFIG[0]
        pi_location = first_device.get('location', pi_location)
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
            publish_mqtt=False,
            enable_csv_write=ENABLE_CSV_WRITE
        )
        managers.append((location, manager, csv_file, meters))
        logger.info(
            f"Location '{location}': {len(meters)} devices, CSV: {csv_file if ENABLE_CSV_WRITE else 'DISABLED'}")

    # MQTT Config (set your broker IP/credentials)
    MQTT_BROKER = os.environ.get('MQTT_BROKER', CONFIG.get('MQTT_BROKER_IP', 'localhost') or 'localhost')
    MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
    MQTT_USER = os.environ.get('MQTT_USER', 'myuser')
    MQTT_PASS = os.environ.get('MQTT_PASS', 'Mahadev@123')
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
                    # DB expects lowercase 'time'
                    meter_data["time"] = reading_time
                    meter_data["pi_name"] = pi_name
                    meter_data["pi_ip"] = pi_ip
                    meter_data["location"] = location
                    meter_data["device_id"] = meter_data.get("Device_ID", None)
                    meter_data["meter_name"] = meter_data.get("Meter_Name", None)
                    meter_data["model"] = meter_data.get("Model", "")
                    meter_data["watts_total"] = meter_data.get("Watts Total", None)
                    meter_data["watts_r_ph"] = meter_data.get("Watts R Ph", None)
                    meter_data["watts_y_ph"] = meter_data.get("Watts Y Ph", None)
                    meter_data["watts_b_ph"] = meter_data.get("Watts B Ph", None)
                    meter_data["pf_ave"] = meter_data.get("PF Ave", None)
                    meter_data["pf_r_ph"] = meter_data.get("PF R Ph", None)
                    meter_data["pf_y_ph"] = meter_data.get("PF Y Ph", None)
                    meter_data["pf_b_ph"] = meter_data.get("PF B Ph", None)
                    meter_data["vln_average"] = meter_data.get("VLN average", None)
                    meter_data["v_r_ph"] = meter_data.get("V R Ph", None)
                    meter_data["v_y_ph"] = meter_data.get("V Y Ph", None)
                    meter_data["v_b_ph"] = meter_data.get("V B Ph", None)
                    meter_data["a_average"] = meter_data.get("A average", None)
                    meter_data["a_r_ph"] = meter_data.get("A R Ph", None)
                    meter_data["a_y_ph"] = meter_data.get("A Y Ph", None)
                    meter_data["a_b_ph"] = meter_data.get("A B Ph", None)
                    meter_data["frequency"] = meter_data.get("Frequency", None)
                    meter_data["wh_received"] = meter_data.get("Wh received", None)
                    meter_data["load_hours_delivered"] = meter_data.get("Load Hours Delivered", None)
                    meter_data["no_of_interruption"] = meter_data.get("No of interruption", None)
                    meter_data["on_hours"] = meter_data.get("On Hours", None)
                    meter_data["v_r_harmonics"] = meter_data.get("V R Harmonics", None)
                    meter_data["v_y_harmonics"] = meter_data.get("V Y Harmonics", None)
                    meter_data["v_b_harmonics"] = meter_data.get("V B Harmonics", None)
                    meter_data["a_r_harmonics"] = meter_data.get("A R Harmonics", None)
                    meter_data["a_y_harmonics"] = meter_data.get("A Y Harmonics", None)
                    meter_data["a_b_harmonics"] = meter_data.get("A B Harmonics", None)
                    print(f"DEBUG: meter_data before MQTT publish: {meter_data}")
                    publish_meter_reading_mqtt(meter_data)
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
        # Set this variable to True to install and setup Mosquitto broker, False to skip broker setup
        setup_broker = False  # Change to True if you want to setup the broker

        if setup_broker:
            def is_deb_installed(pkg):
                result = subprocess.run(['dpkg', '-s', pkg], capture_output=True)
                return result.returncode == 0

            need_mosquitto = not is_deb_installed('mosquitto')
            need_clients = not is_deb_installed('mosquitto-clients')

            if need_mosquitto or need_clients:
                debs_dir = Path(__file__).parent.parent / 'packages_folder' / 'debs'
                if debs_dir.exists():
                    deb_files = list(debs_dir.glob('*.deb'))
                    if deb_files:
                        print(f"Installing .deb packages from {debs_dir}...")
                        deb_paths = [str(deb) for deb in deb_files]
                        result = subprocess.run(['sudo', 'dpkg', '-i'] + deb_paths)
                        if result.returncode == 0:
                            print("✅ All .deb packages installed.")
                        else:
                            print(f"❌ Error installing .deb packages: {result.stderr}")
                    else:
                        print(f"No .deb files found in {debs_dir}.")
                else:
                    print(f"No debs directory found at {debs_dir}.")
            else:
                print("Mosquitto and mosquitto-clients already installed. Skipping .deb installation.")

            # Run Mosquitto setup after dependencies are installed
            print("Running Mosquitto setup...")
            subprocess.run(['sudo', 'python3', 'mosquitto_setup.py'])
        else:
            print("Skipping Mosquitto broker setup. Only installing MQTT client dependencies.")

        # --- Begin merged environment setup logic ---
        print("🔧 Setting up Python virtual environment and installing dependencies (offline)...")
        import sys, os
        from pathlib import Path
        parent_dir = Path(__file__).parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        from venv_utils import setup_complete_venv_environment
        req_path = parent_dir / "requirements.txt"
        with open(req_path, 'r') as f:
            required_packages = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        venv_dir = parent_dir / "venv"
        packages_folder = parent_dir / "packages_folder"
        success, python_exe = setup_complete_venv_environment(
            venv_dir=venv_dir,
            packages=required_packages,
            force_recreate=False,
            offline_dir=str(packages_folder)
        )
        if not success:
            print("❌ Environment setup failed (offline mode)")
            sys.exit(1)
        print("✅ Offline environment setup complete")

        # --- Force install critical packages from wheels (first step) ---
        def force_install_package(package_name, wheel_dir, python_exe):
            import subprocess
            result = subprocess.run([
                str(python_exe), "-m", "pip", "install", "--force-reinstall", "--no-index",
                "--find-links", str(wheel_dir), package_name
            ], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {package_name} force-installed from {wheel_dir}")
            else:
                print(f"❌ Failed to force-install {package_name}: {result.stderr}")

        force_install_package("requests", packages_folder, python_exe)
        force_install_package("psycopg2-binary", packages_folder, python_exe)
        force_install_package("paho-mqtt", packages_folder, python_exe)
        force_install_package("paramiko", packages_folder, python_exe)

        # --- Call PostgreSQL setup script (before broker/MQTT logic) ---
        print("🔧 Running PostgreSQL setup and schema restore...")
        postgre_setup_path = str(Path(__file__).parent / "postgre_setup.py")
        # Suppress stdout, only show summary and critical errors
        import subprocess
        result = subprocess.run([str(python_exe), postgre_setup_path], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ PostgreSQL setup completed.")
        else:
            print(f"❌ PostgreSQL setup failed:")
            # Show only last 10 lines of error output for brevity
            err_lines = result.stderr.splitlines()
            print("\n".join(err_lines[-10:]))

        # --- End merged environment setup logic ---
        # Broker/MQTT logic can be added after DB setup if needed
        sys.exit(0)
    elif '--run' in sys.argv or len(sys.argv) == 1:
        run_dashboard()
    else:
        print("Unknown argument. Use --install or --run.")