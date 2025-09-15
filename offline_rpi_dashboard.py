
#!/usr/bin/env python3

# Add delay at startup to allow system and hardware to initialize (important for cron @reboot)
from venv_utils import setup_complete_venv_environment
from datetime import datetime
import logging
import signal
import time
import json
import argparse
from pathlib import Path
import sys
import subprocess
import os
import re
import time as _time

# Set RTC time at startup if running as 'pi' user

try:
    user = os.getenv('USER', 'unknown')
    if user in ('pi', 'root'):
        rtc_script = Path(__file__).parent / 'rtc_new.py'
        if rtc_script.exists():
            # Check for internet connectivity
            import socket

            def has_internet(host="8.8.8.8", port=53, timeout=2):
                try:
                    socket.setdefaulttimeout(timeout)
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                        (host, port))
                    return True
                except Exception:
                    return False
            if has_internet():
                print(
                    "⏰ Internet detected. RTC time updated from internet (rtc_new.py --set-rtc)...")
                result = subprocess.run([sys.executable, str(
                    rtc_script), '--set-rtc'], capture_output=True, text=True)
            else:
                print(
                    "⏰ No internet detected. Correcting system time from RTC IC (rtc_new.py)...")
                result = subprocess.run([sys.executable, str(
                    rtc_script)], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ RTC time set successfully.")
            else:
                print(f"⚠️ RTC set failed: {result.stderr.strip()}")
        else:
            print("⚠️ rtc_new.py not found, skipping RTC set.")
except Exception as e:
    print(f"⚠️ RTC set error: {e}")
"""
Offline RPi Auto-Startup Dashboard - All-in-One Solution (No Internet Required)

This script is a copy of simple_rpi_dashboard.py, but it only installs Python packages from the local 'packages_folder' directory. It will not attempt to download packages from the internet.

Usage:
    python3 offline_rpi_dashboard.py --setup      # Initial setup (offline)
    python3 offline_rpi_dashboard.py --install    # Install auto-startup
    python3 offline_rpi_dashboard.py --run        # Run dashboard
    python3 offline_rpi_dashboard.py --status     # Check status
    python3 offline_rpi_dashboard.py --stop       # Stop dashboard

Author: Simplified approach (offline version)
Date: 24/07/30
"""


# Import shared venv utilities


def strip_jsonc_comments(text):
    # Remove // and /* */ comments for JSONC
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def load_jsonc_config(path):
    with open(path, 'r') as f:
        content = f.read()
        return json.loads(strip_jsonc_comments(content))


def load_device_config(config_path):
    return load_jsonc_config(config_path)


def load_main_config(config_path):
    return load_jsonc_config(config_path)


def load_required_packages(req_path):
    with open(req_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]


script_dir = Path(__file__).parent.absolute()
CONFIG = load_main_config(script_dir / "config.json")
DEVICE_CONFIG = load_device_config(script_dir / "device_config.json")
REQUIRED_PACKAGES = load_required_packages(
    script_dir / "requirements.txt")


def auto_use_venv_if_needed():
    """
    Automatically restart with venv Python if:
    1. We're not already running in venv
    2. venv exists
    3. We're trying to run the dashboard (--run)
    """
    script_dir = Path(__file__).parent.absolute()
    venv_python = script_dir / "venv" / "bin" / "python"
    # Check if we're already in venv by checking sys.executable
    if venv_python.exists() and str(venv_python) != sys.executable:
        # Check if this is a run or print-readings command
        if len(sys.argv) > 1 and any(arg in ['--run', '--run-service', '--print-readings'] for arg in sys.argv):
            print("🔄 Auto-switching to virtual environment...")
            print(f"   Using: {venv_python}")
            # Re-execute with venv python
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    return False  # Not using venv or venv doesn't exist
# --- END: Copied from simple_rpi_dashboard.py ---


class OfflineDashboard:
    def run_dashboard(self):
        """
        Main dashboard loop: sets up logging, meters, and manager, then reads meters in a loop and logs data.
        """
        if not self.venv_dir.exists():
            print("❌ Virtual environment not found. Run --setup first.")
            return False
        self.setup_logging()
        self.logger.info("Starting dashboard in headless mode...")
        # Setup signal handlers

        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}. Shutting down...")
            sys.exit(0)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        try:
            sys.path.insert(0, str(self.script_dir))
            from meter_manager import MeterManager
            from meter_device import MeterDevice
            from macros import PARAMETERS
            import mqtt_client as mqtt
            from pymodbus.client.sync import ModbusSerialClient as ModbusClient
            self.logger.info("Modules imported successfully")
            # RTC (optional)
            if CONFIG["ENABLE_RTC"]:
                self.logger.info(
                    "Initializing RTC system for offline time keeping...")
                try:
                    from rtc_manager import RTCManager
                    rtc_manager = RTCManager(logger=self.logger)
                    if rtc_manager.initialize_for_offline_operation():
                        self.logger.info(
                            "✅ RTC system ready for offline operation")
                    else:
                        self.logger.warning(
                            "⚠️ RTC initialization failed - using system time only")
                except Exception as e:
                    self.logger.warning(
                        f"⚠️ RTC initialization error: {e} - using system time only")
            else:
                self.logger.info("RTC disabled - using system time only")

            # Hardware/Simulation logic
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
                            self.logger.info(f"Connected to {CONFIG['PORT']}")
                        else:
                            self.logger.warning(
                                "Failed to connect, will use default value -1 for all readings.")
                            use_default = True
                    except Exception as e:
                        self.logger.error(
                            f"Hardware error: {e}, will use default value -1 for all readings.")
                        use_default = True
                else:
                    self.logger.warning(
                        f"Port {CONFIG['PORT']} not found, will use default value -1 for all readings.")
                    use_default = True
            # If simulation_mode is true, always generate random values as before

            # MQTT
            if CONFIG["ENABLE_MQTT"]:
                mqtt.mqtt_main()

            # Devices and manager
            from collections import defaultdict
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

            # For each location, create a single CSV file and MeterManager
            managers = []
            for location, meters in location_meters.items():
                clean_location = "".join(
                    c for c in location if c.isalnum() or c in ('-', '_'))
                csv_file = self.csv_dir / f"{clean_location}.csv"
                manager = MeterManager(
                    meters, PARAMETERS, [str(csv_file)],
                    mqtt_client=mqtt if CONFIG["ENABLE_MQTT"] else None,
                    publish_mqtt=CONFIG["ENABLE_MQTT"]
                )
                managers.append(manager)
                self.logger.info(
                    f"Dashboard started for location '{location}' with {len(meters)} devices, writing to {csv_file}")
                # Print simulation mode, interval, and device info summary
                print("="*80)
                print(f"Dashboard started for location: {location}")
                print(
                    f"  Simulation Mode: {'ON' if simulation_mode else 'OFF'}")
                print(
                    f"  Reading Interval: {CONFIG['READING_INTERVAL']} seconds")
                print(
                    f"  Inter-device Delay: {CONFIG.get('INTER_DEVICE_DELAY', 0)} seconds")
                print(
                    f"  MQTT Enabled: {'Yes' if CONFIG['ENABLE_MQTT'] else 'No'}")
                print(f"  Output CSV: {csv_file}")
                print("  Devices:")
                for meter in meters:
                    print(
                        f"    - Name: {meter.name}, Model: {meter.model}, Address: {getattr(meter, 'device_address', 'N/A')}, Simulation: {meter.simulation_mode}")
                print("="*80)

            # Main loop
            while True:
                for manager in managers:
                    manager.read_all(
                        inter_device_delay=CONFIG["INTER_DEVICE_DELAY"])
                    if manager.TotalReadings % 10 == 0:
                        self.logger.info(
                            f"Completed {manager.TotalReadings} reading cycles for location {manager.csv_file.name}")
                time.sleep(CONFIG["READING_INTERVAL"])
        except Exception as e:
            import traceback
            self.logger.error(f"Dashboard error: {e}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def ensure_venv_and_packages(self):
        """
        Check if venv exists and all required packages are installed. If not, install missing packages from packages_folder.
        """
        venv_python = self.venv_dir / "bin" / "python"
        pip_exe = self.venv_dir / "bin" / "pip"
        packages_dir = self.script_dir / "packages_folder"
        # 1. Check if venv exists
        if not venv_python.exists():
            print(
                "🔧 Virtual environment not found. Creating and installing all packages from local folder...")
            self.setup_environment()
            return
        # 2. Check installed packages in venv
        try:
            result = subprocess.run(
                [str(pip_exe), 'freeze'], capture_output=True, text=True, check=True)
            installed = set()
            for line in result.stdout.splitlines():
                pkg = line.split('==')[0].lower()
                installed.add(pkg)
        except Exception as e:
            print(f"⚠️ Could not check installed packages: {e}")
            print("🔧 Reinstalling all packages from local folder...")
            self.setup_environment()
            return
        # 3. Find missing packages
        missing = []
        for req in REQUIRED_PACKAGES:
            pkg = req.split('==')[0].lower()
            if pkg not in installed:
                missing.append(req)
        if not missing:
            print("✅ All required packages are already installed in venv.")
            return
        # 4. Install missing packages from packages_folder
        print(f"🔧 Installing missing packages: {missing}")
        if not packages_dir.exists() or not list(packages_dir.glob("*.whl")):
            print(
                "❌ No offline packages found in 'packages_folder'. Cannot install missing packages.")
            return
        for req in missing:
            pkg_name = req.split('==')[0].replace('_', '-').lower()
            found = False
            for whl in packages_dir.glob(f"{pkg_name}-*.whl"):
                print(f"📦 Installing {whl.name} ...")
                result = subprocess.run([str(pip_exe), 'install', '--no-index', '--find-links', str(
                    packages_dir), str(whl)], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Installed {whl.name}")
                    found = True
                    break
                else:
                    print(f"❌ Failed to install {whl.name}: {result.stderr}")
            if not found:
                print(f"❌ Could not find wheel for {req} in packages_folder.")
        print("🔄 Package check complete.")

    def print_all_meter_readings(self, manager):
        """
        Print all meter readings, device IDs, and parameter values to the shell.
        """
        readings = manager.get_all_meter_readings()
        print("\n===== Current Meter Readings =====")
        for meter in readings:
            print(f"Device ID: {meter['device_id']}")
            print(f"Device Name: {meter['device_name']}")
            print(f"Model: {meter['model']}")
            print("Readings:")
            for param, value in zip(manager.parameters, meter['readings']):
                print(f"  {param}: {value}")
            print("-----------------------------")
        print("=================================\n")
    """All-in-one dashboard manager (offline package install)."""

    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.venv_dir = self.script_dir / "venv"
        self.log_dir = self.script_dir / "logs"
        self.csv_dir = self.script_dir / "csv_data"
        self.service_name = "meter-dashboard-offline"

    def setup_logging(self):
        # ...same as SimpleDashboard...
        self.log_dir.mkdir(exist_ok=True)
        log_file = self.log_dir / \
            f"dashboard_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=getattr(logging, CONFIG["LOG_LEVEL"]),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def run_command(self, cmd, check=True, shell=False):
        # ...same as SimpleDashboard...
        try:
            if isinstance(cmd, str) and not shell:
                cmd = cmd.split()
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=check, shell=shell)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr

    def setup_environment(self):
        """Setup virtual environment and install dependencies from local packages_folder only."""
        print("🔧 Setting up environment (offline mode)...")
        packages_dir = self.script_dir / "packages_folder"
        if not packages_dir.exists() or not list(packages_dir.glob("*.whl")):
            print("❌ No offline packages found in 'packages_folder'. Aborting setup.")
            return False
        # Use shared venv utility for complete setup, but force offline_dir
        success, python_exe = setup_complete_venv_environment(
            venv_dir=self.venv_dir,
            packages=REQUIRED_PACKAGES,
            force_recreate=False,
            offline_dir=str(packages_dir)
        )
        if not success:
            print("❌ Environment setup failed (offline mode)")
            return False
        self.log_dir.mkdir(exist_ok=True)
        self.csv_dir.mkdir(exist_ok=True)
        print("✅ Offline environment setup complete")
        return True

    # ...all other methods are identical to SimpleDashboard, except use self.service_name = 'meter-dashboard-offline'...
    # You can copy the rest of the methods from SimpleDashboard here, or import them if you refactor.

# ...main() function, identical to simple_rpi_dashboard.py but using OfflineDashboard...


def main():
    auto_use_venv_if_needed()
    parser = argparse.ArgumentParser(
        description="Offline RPi Dashboard Manager")
    parser.add_argument("--check-prereq", action="store_true",
                        help="Check prerequisites and permissions")
    parser.add_argument("--setup", action="store_true",
                        help="Setup environment (venv + packages + directories, offline)")
    parser.add_argument("--create-service", action="store_true",
                        help="Create systemd service file (requires sudo)")
    parser.add_argument("--install", action="store_true",
                        help="Full install: setup + create service (requires sudo)")
    parser.add_argument("--run", action="store_true", help="Run dashboard")
    parser.add_argument("--run-service", action="store_true",
                        help="Run dashboard as service (used by systemd)")
    parser.add_argument("--status", action="store_true", help="Check status")
    parser.add_argument("--stop", action="store_true", help="Stop dashboard")
    parser.add_argument("--logs", action="store_true", help="View logs")
    parser.add_argument("--start", action="store_true", help="Start service")
    parser.add_argument("--restart", action="store_true",
                        help="Restart service")
    parser.add_argument("--uninstall", action="store_true",
                        help="Uninstall service")
    parser.add_argument("--print-readings", action="store_true",
                        help="Print all meter readings and device IDs to shell (debug)")
    args = parser.parse_args()
    dashboard = OfflineDashboard()
    if args.check_prereq:
        dashboard.check_prerequisites()
    elif args.setup:
        dashboard.ensure_venv_and_packages()
    # elif args.create_service:
    #     pass
    elif args.install:
        print("🚀 Full installation starting (offline)...")
        dashboard.setup_environment()
        # Removed call to dashboard.create_service_only()
    elif args.run or args.run_service:
        script_dir = Path(__file__).parent.absolute()
        venv_dir = script_dir / "venv"
        if not venv_dir.exists():
            print("❌ Virtual environment not found!")
            print("🔧 Please run setup first:")
            print("   python3 offline_rpi_dashboard.py --setup")
            print("   python3 offline_rpi_dashboard.py --create-service")
            print("")
            print("💡 Or use the quick install:")
            print("   python3 offline_rpi_dashboard.py --install")
            sys.exit(1)
        dashboard.run_dashboard()
    elif args.print_readings:
        # Print the latest data being written to CSVs by --run, in a loop (per-location CSVs)
        from macros import PARAMETERS
        import time
        import csv
        script_dir = Path(__file__).parent.absolute()
        csv_dir = script_dir / "csv_data"
        # Find all location-based CSV files
        csv_files = sorted(csv_dir.glob("*.csv"))
        print("\nLive meter readings from CSV (Ctrl+C to stop):\n")
        try:
            while True:
                print("===== Current Meter Readings (from CSV) =====")
                for csv_path in csv_files:
                    print(f"CSV File: {csv_path}")
                    try:
                        with open(csv_path, "r") as f:
                            reader = list(csv.reader(f))
                            if len(reader) < 2:
                                print("  No data yet.")
                            else:
                                header = reader[0]
                                # Group by Device_ID or Meter_Name
                                device_id_idx = None
                                device_name_idx = None
                                for idx, col in enumerate(header):
                                    if col.strip().lower() == 'device_id':
                                        device_id_idx = idx
                                    if col.strip().lower() == 'meter_name' or col.strip().lower() == 'device_name':
                                        device_name_idx = idx
                                device_latest = {}
                                for row in reader[1:]:
                                    key = None
                                    if device_id_idx is not None:
                                        key = row[device_id_idx]
                                    elif device_name_idx is not None:
                                        key = row[device_name_idx]
                                    else:
                                        key = 'Unknown'
                                    device_latest[key] = row
                                for device, row in device_latest.items():
                                    print(f"  --- Device: {device} ---")
                                    for h, v in zip(header, row):
                                        print(f"    {h}: {v}")
                    except FileNotFoundError:
                        print("  CSV file not found.")
                    except Exception as e:
                        print(f"  Error reading CSV: {e}")
                    print("-----------------------------")
                print("=================================\n")
                time.sleep(CONFIG["READING_INTERVAL"])
        except KeyboardInterrupt:
            print("\nStopped live meter readings from CSV.\n")
    elif args.status:
        dashboard.check_status()
    elif args.stop:
        dashboard.stop_dashboard()
    elif args.logs:
        dashboard.view_logs()
    elif args.start:
        dashboard.start_service()
    elif args.restart:
        dashboard.restart_service()
    elif args.uninstall:
        dashboard.uninstall_service()
    else:
        print("🔌 Offline RPi Dashboard Manager")
        print("\n📋 Prerequisites Check:")
        print("  python3 offline_rpi_dashboard.py --check-prereq   # Check system prerequisites")
        print("\n🔧 Setup Commands:")
        print("  python3 offline_rpi_dashboard.py --setup          # Setup environment only (offline)")
        print("  python3 offline_rpi_dashboard.py --create-service # Create service file (requires sudo)")
        print("  python3 offline_rpi_dashboard.py --install        # Full setup + service (requires sudo)")
        print("\n▶️  Running:")
        print("  python3 offline_rpi_dashboard.py --run            # Run dashboard manually (auto-uses venv)")
        print("  python3 offline_rpi_dashboard.py --print-readings # Print all meter readings and device IDs")
        print("  python3 offline_rpi_dashboard.py --status         # Check service status")
        print("")
        print("💡 Note: --run automatically uses virtual environment if available")
        print("\n🔧 Service Management:")
        print("  python3 offline_rpi_dashboard.py --start          # Start service")
        print("  python3 offline_rpi_dashboard.py --stop           # Stop service")
        print("  python3 offline_rpi_dashboard.py --restart        # Restart service")
        print("  python3 offline_rpi_dashboard.py --logs           # View logs")
        print("  python3 offline_rpi_dashboard.py --uninstall      # Remove service")
        print("\n📖 For manual setup without sudo prompts, see: docs/MANUAL_SETUP.md")


if __name__ == "__main__":
    main()
