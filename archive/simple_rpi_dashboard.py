#!/usr/bin/env python3
"""
Simple RPi Auto-Startup Dashboard - All-in-One Solution

This single script handles:
- Automatic venv setup and dependency installation
- Auto-startup configuration (systemd service)
- Headless operation with CSV logging
- Status monitoring and control

Usage:
    python3 simple_rpi_dashboard.py --setup      # Initial setup
    python3 simple_rpi_dashboard.py --install    # Install auto-startup
    python3 simple_rpi_dashboard.py --run        # Run dashboard
    python3 simple_rpi_dashboard.py --status     # Check status
    python3 simple_rpi_dashboard.py --stop       # Stop dashboard

Author: Simplified approach
Date: 24/07/25
"""

import os
import sys
import subprocess
import argparse
import json
import time
import signal
import logging
from pathlib import Path
from datetime import datetime

# Import shared venv utilities
from venv_utils import setup_complete_venv_environment


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
        # Check if this is a run command
        if len(sys.argv) > 1 and any(arg in ['--run', '--run-service'] for arg in sys.argv):
            print("🔄 Auto-switching to virtual environment...")
            print(f"   Using: {venv_python}")
            # Re-execute with venv python
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)

    return False  # Not using venv or venv doesn't exist


def check_sudo_available():
    """Check if sudo is available and user has sudo access."""
    # If we're already running as root, we don't need sudo
    if os.geteuid() == 0:
        return True

    try:
        result = subprocess.run(["sudo", "-n", "true"],
                                capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def require_sudo_for_command(command_name):
    """Check if running with appropriate permissions for systemd operations."""
    if os.geteuid() != 0 and not check_sudo_available():
        print(
            f"❌ Error: '{command_name}' requires sudo access for systemd operations.")
        print("")
        print("💡 Solutions:")
        print("1. Run with sudo:")
        print(f"   sudo python3 {os.path.basename(__file__)} {command_name}")
        print("")
        print("2. Add user to sudo group:")
        print("   sudo usermod -aG sudo $USER")
        print("   # Then logout and login again")
        print("")
        print("3. For passwordless sudo (optional):")
        print("   sudo visudo")
        print("   # Add line: pi ALL=(ALL) NOPASSWD: /bin/systemctl")
        print("")
        return False
    return True


def check_user_permissions():
    """Check and display current user permissions."""
    user = os.getenv('USER', 'unknown')
    uid = os.getuid()

    print(f"👤 Current user: {user} (UID: {uid})")

    # Check if user is in dialout group (needed for serial ports)
    try:
        import grp
        dialout_group = grp.getgrnam('dialout')
        if user in dialout_group.gr_mem:
            print("✅ User is in 'dialout' group (serial port access)")
        else:
            print("⚠️ User NOT in 'dialout' group - serial ports may not work")
            print("   Fix: sudo usermod -aG dialout $USER")
    except KeyError:
        print("⚠️ 'dialout' group not found on this system")

    # Check sudo access
    if check_sudo_available():
        print("✅ Sudo access available")
    else:
        print("⚠️ No sudo access - service management will require manual sudo")

    print("")


# Configuration
CONFIG = {
    "SIMULATION_MODE": False,
    # Match legacy script (10 seconds between reading cycles)
    "READING_INTERVAL": 10,
    # Delay between device reads (seconds) - matches legacy intervalBwMeter
    "INTER_DEVICE_DELAY": 0.1,
    "PORT": "/dev/ttyUSB0",
    "ENABLE_MQTT": False,
    "ENABLE_RTC": True,  # Enable RTC for offline time keeping
    "LOG_LEVEL": "INFO"
}

# Device Configuration - Customize your meters here
DEVICE_CONFIG = [
    {"name": "SP3 UPS", "address": 1, "model": "LG6400"},
    {"name": "Suryakund UPS", "address": 2, "model": "LG+5220"},
    # {"name": "BP", "address": 3, "model": "EN8410"},
    # Add more devices as needed:
    # {"name": "Your Device Name", "address": 4, "model": "LG6400"},
    # {"name": "Another Device", "address": 5, "model": "EN8410"},
]

REQUIRED_PACKAGES = [
    "pymodbus==2.5.3",
    "pyserial==3.5",
    "paho-mqtt==2.1.0",
    "termcolor==3.1.0",
    "numpy==1.24.3",
    "pandas==2.0.3"
]


class SimpleDashboard:
    """All-in-one dashboard manager."""

    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.venv_dir = self.script_dir / "venv"
        self.log_dir = self.script_dir / "logs"
        self.csv_dir = self.script_dir / "csv_data"
        self.service_name = "meter-dashboard"

    def setup_logging(self):
        """Setup logging."""
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
        """Run a system command."""
        try:
            if isinstance(cmd, str) and not shell:
                cmd = cmd.split()
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=check, shell=shell)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr

    def check_prerequisites(self):
        """Check system prerequisites and provide guidance."""
        print("🔍 Checking System Prerequisites...")
        print("=" * 50)

        issues_found = False

        # Check if running on Linux
        if os.name != 'posix':
            print("⚠️  This script is designed for Linux/Raspberry Pi systems")
            print("   Current OS detected:", os.name)
            issues_found = True
        else:
            print("✅ Running on Linux/Unix system")

        # Check Python version
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 7:
            print(
                f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            print(
                f"⚠️  Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
            print("   Recommended: Python 3.7 or higher")
            issues_found = True

        # Check if user is in dialout group
        current_user = os.getenv('USER', 'unknown')
        print(f"👤 Current user: {current_user}")

        try:
            # grp module is only available on Unix-like systems
            if os.name == 'posix':
                import grp
                dialout_group = grp.getgrnam('dialout')
                if current_user in dialout_group.gr_mem:
                    print("✅ User is in 'dialout' group (serial port access)")
                else:
                    print("❌ User NOT in 'dialout' group")
                    print("   Fix: sudo usermod -a -G dialout $USER")
                    print("   Then: sudo reboot")
                    issues_found = True
            else:
                print("ℹ️  Group checking not available on this platform")
        except (KeyError, ImportError):
            print("⚠️  'dialout' group not found or grp module unavailable")

        # Check for required system packages
        required_packages = ['python3-venv', 'python3-pip']
        print("\n🔍 Checking system packages...")

        for package in required_packages:
            success, stdout, stderr = self.run_command(
                ['dpkg', '-l', package], check=False)
            if success and package in stdout:
                print(f"✅ {package} is installed")
            else:
                print(f"❌ {package} is NOT installed")
                print(f"   Fix: sudo apt install {package} -y")
                issues_found = True

        # Check systemd
        if Path('/etc/systemd/system').exists():
            print("✅ systemd is available")
        else:
            print("⚠️  systemd not found - will use crontab fallback")

        # Check venv module
        success, stdout, stderr = self.run_command(
            [sys.executable, '-m', 'venv', '--help'], check=False)
        if success:
            print("✅ venv module is available")
        else:
            print("❌ venv module not available")
            print("   Fix: sudo apt install python3-venv")
            issues_found = True

        # Check pip availability
        success, stdout, stderr = self.run_command(
            [sys.executable, '-m', 'pip', '--version'], check=False)
        if success:
            print("✅ pip is available")
        else:
            print("❌ pip not available")
            print("   Fix: sudo apt install python3-pip")
            issues_found = True

        print("\n" + "=" * 50)

        if issues_found:
            print("❌ Issues found! Please fix the above problems before proceeding.")
            print("\n📋 Quick fix commands:")
            print("sudo apt update")
            print("sudo apt install python3-venv python3-pip -y")
            print("sudo usermod -a -G dialout $USER")
            print("sudo reboot")
            return False
        else:
            print("✅ All prerequisites met! You can proceed with setup.")
            print("\n🚀 Next steps:")
            print("1. python3 simple_rpi_dashboard.py --setup")
            print("2. python3 simple_rpi_dashboard.py --create-service")
            return True

    def create_service_only(self):
        """Create systemd service file only (requires sudo)."""
        print("🔧 Creating systemd service file...")

        if not self.venv_dir.exists():
            print("❌ Virtual environment not found.")
            print("   Run: python3 simple_rpi_dashboard.py --setup")
            return False

        # Check if running with appropriate permissions
        if os.geteuid() != 0 and not check_sudo_available():
            print("❌ This operation requires sudo access.")
            print("💡 Run with sudo or ensure user has sudo privileges:")
            print(
                f"   sudo python3 {os.path.basename(__file__)} --create-service")
            return False

        return self.create_systemd_service()

    def setup_environment(self):
        """Setup virtual environment and install dependencies using shared utilities."""
        print("🔧 Setting up environment...")

        # Check if offline packages are available
        offline_dir = None
        offline_path = Path("offline_packages")
        if offline_path.exists() and list(offline_path.glob("*.whl")):
            print(f"🔍 Found offline packages at: {offline_path}")
            offline_dir = "offline_packages"

        # Use shared venv utility for complete setup
        success, python_exe = setup_complete_venv_environment(
            venv_dir=self.venv_dir,
            packages=REQUIRED_PACKAGES,
            force_recreate=False,
            offline_dir=offline_dir
        )

        if not success:
            print("❌ Environment setup failed")
            return False

        # Create additional directories
        self.log_dir.mkdir(exist_ok=True)
        self.csv_dir.mkdir(exist_ok=True)

        print("✅ Environment setup complete")
        return True

    def create_systemd_service(self):
        """Create systemd service for auto-startup."""
        service_content = f"""[Unit]
Description=Meter Reading Dashboard
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory={self.script_dir}
ExecStart={self.venv_dir}/bin/python {__file__} --run
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

        service_file = f"/etc/systemd/system/{self.service_name}.service"

        try:
            # Write service file directly if running as root, otherwise use sudo
            if os.geteuid() == 0:
                # Running as root - write directly
                with open(service_file, "w") as f:
                    f.write(service_content)
                success = True
                stderr = ""
            else:
                # Not root - use sudo
                with open("/tmp/dashboard.service", "w") as f:
                    f.write(service_content)

                success, stdout, stderr = self.run_command([
                    "sudo", "cp", "/tmp/dashboard.service", service_file
                ])

            if not success:
                print(f"❌ Failed to create service file: {stderr}")
                return False

            # Enable and start service (use sudo if not root)
            if os.geteuid() == 0:
                self.run_command(["systemctl", "daemon-reload"])
                self.run_command(["systemctl", "enable", self.service_name])
            else:
                self.run_command(["sudo", "systemctl", "daemon-reload"])
                self.run_command(
                    ["sudo", "systemctl", "enable", self.service_name])

            print(
                f"✅ Systemd service '{self.service_name}' created and enabled")
            print("   The dashboard will start automatically on boot")
            return True

        except Exception as e:
            print(f"❌ Error creating systemd service: {e}")
            return False

    def install_auto_startup(self):
        """Install auto-startup service."""
        if not self.venv_dir.exists():
            print("❌ Virtual environment not found. Run --setup first.")
            return False

        print("🚀 Installing auto-startup service...")

        # Check if we're on a systemd system
        if Path("/etc/systemd/system").exists():
            return self.create_systemd_service()
        else:
            # Fallback to crontab
            return self.install_crontab()

    def install_crontab(self):
        """Fallback: Install crontab entry."""
        cron_entry = f"@reboot sleep 60 && cd {self.script_dir} && {self.venv_dir}/bin/python {__file__} --run"

        # Get current crontab
        success, current_cron, _ = self.run_command(
            ["crontab", "-l"], check=False)

        if not success or cron_entry not in current_cron:
            # Add new entry
            new_cron = current_cron + "\n" + cron_entry if success else cron_entry

            # Write to temp file and install
            with open("/tmp/new_crontab", "w") as f:
                f.write(new_cron)

            success, stdout, stderr = self.run_command(
                ["crontab", "/tmp/new_crontab"])
            os.unlink("/tmp/new_crontab")

            if success:
                print("✅ Crontab entry added")
                return True
            else:
                print(f"❌ Failed to add crontab entry: {stderr}")
                return False
        else:
            print("✅ Crontab entry already exists")
            return True

    def run_dashboard(self):
        """Run the main dashboard."""
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
            # Import modules (they should be available in venv)
            sys.path.insert(0, str(self.script_dir))

            from meter_manager import MeterManager
            from meter_device import MeterDevice
            from macros import PARAMETERS  # Only import PARAMETERS, not DEVICE_NAMES
            import mqtt_client as mqtt
            from pymodbus.client.sync import ModbusSerialClient as ModbusClient

            self.logger.info("Modules imported successfully")

            # Initialize RTC for offline time keeping
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

            # Initialize hardware
            client = None
            if not CONFIG["SIMULATION_MODE"]:
                if os.path.exists(CONFIG["PORT"]):
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
                                "Failed to connect, using simulation mode")
                            CONFIG["SIMULATION_MODE"] = True
                    except Exception as e:
                        self.logger.error(
                            f"Hardware error: {e}, using simulation mode")
                        CONFIG["SIMULATION_MODE"] = True
                else:
                    self.logger.warning(
                        f"Port {CONFIG['PORT']} not found, using simulation mode")
                    CONFIG["SIMULATION_MODE"] = True

            # Initialize MQTT
            if CONFIG["ENABLE_MQTT"]:
                mqtt.mqtt_main()

            # Create devices and manager
            timestamp = datetime.now().strftime("%Y%m%d")
            csv_files = []
            meters = []

            # Use DEVICE_CONFIG instead of DEVICE_NAMES
            for i, device_config in enumerate(DEVICE_CONFIG):
                device_name = device_config["name"]
                device_address = device_config["address"]
                device_model = device_config["model"]

                clean_name = "".join(
                    c for c in device_name if c.isalnum() or c in ('-', '_'))
                csv_file = self.csv_dir / f"{clean_name}_{timestamp}.csv"
                csv_files.append(str(csv_file))

                meter = MeterDevice(
                    name=device_name,
                    model=device_model,
                    parameters=PARAMETERS,
                    client=client,
                    error_file=None,
                    simulation_mode=CONFIG["SIMULATION_MODE"],
                    device_address=device_address  # Pass the configurable address
                )
                meters.append(meter)

            manager = MeterManager(
                meters, PARAMETERS, csv_files,
                mqtt_client=mqtt if CONFIG["ENABLE_MQTT"] else None,
                publish_mqtt=CONFIG["ENABLE_MQTT"]
            )

            self.logger.info(f"Dashboard started with {len(meters)} devices")

            # Main loop
            while True:
                manager.read_all(
                    inter_device_delay=CONFIG["INTER_DEVICE_DELAY"])

                if manager.TotalReadings % 10 == 0:
                    self.logger.info(
                        f"Completed {manager.TotalReadings} reading cycles")

                time.sleep(CONFIG["READING_INTERVAL"])

        except Exception as e:
            import traceback
            self.logger.error(f"Dashboard error: {e}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def check_status(self):
        """Check dashboard status."""
        print("📊 Dashboard Status")
        print("=" * 40)

        # Check if service is running
        success, stdout, stderr = self.run_command(
            ["systemctl", "is-active", self.service_name], check=False)
        if success and "active" in stdout:
            print("✅ Service: Running")
        else:
            print("❌ Service: Not running")

        # Check for manually running processes
        success, stdout, stderr = self.run_command(
            ["pgrep", "-f", "simple_rpi_dashboard.py --run"], check=False)
        if success and stdout.strip():
            pids = stdout.strip().split('\n')
            print(f"🔄 Manual processes: {len(pids)} running")
            for pid in pids:
                if pid.strip():
                    print(f"   PID: {pid.strip()}")
        else:
            print("⭕ Manual processes: None running")

        # Check venv
        if self.venv_dir.exists():
            print("✅ Virtual environment: Ready")
        else:
            print("❌ Virtual environment: Not found")

        # Check logs
        if self.log_dir.exists():
            log_files = list(self.log_dir.glob("*.log"))
            print(f"📁 Log files: {len(log_files)} found")
            if log_files:
                latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                print(f"   Latest: {latest_log.name}")

        # Check CSV data
        if self.csv_dir.exists():
            csv_files = list(self.csv_dir.glob("*.csv"))
            print(f"📈 CSV files: {len(csv_files)} found")

        print("=" * 40)

    def stop_dashboard(self):
        """Stop the dashboard service and any running processes."""
        print("🛑 Stopping dashboard...")

        # First, try to stop the systemd service
        success, stdout, stderr = self.run_command(
            ["sudo", "systemctl", "stop", self.service_name], check=False)
        if success:
            print("✅ Dashboard service stopped")
        else:
            print(f"⚠️ Service stop result: {stderr}")

        # Also kill any manually running dashboard processes
        print("🔍 Checking for running dashboard processes...")
        success, stdout, stderr = self.run_command(
            ["pgrep", "-f", "simple_rpi_dashboard.py --run"], check=False)

        if success and stdout.strip():
            print("🔄 Found running dashboard processes, stopping them...")
            pids = stdout.strip().split('\n')
            for pid in pids:
                if pid.strip():
                    print(f"   Stopping process {pid.strip()}")
                    self.run_command(
                        ["kill", "-TERM", pid.strip()], check=False)

            # Wait a moment, then force kill if still running
            time.sleep(2)
            success2, stdout2, stderr2 = self.run_command(
                ["pgrep", "-f", "simple_rpi_dashboard.py --run"], check=False)
            if success2 and stdout2.strip():
                print("🔨 Force stopping remaining processes...")
                pids2 = stdout2.strip().split('\n')
                for pid in pids2:
                    if pid.strip():
                        self.run_command(
                            ["kill", "-KILL", pid.strip()], check=False)

            print("✅ All dashboard processes stopped")
        else:
            print("ℹ️ No running dashboard processes found")

    def view_logs(self):
        """View recent dashboard logs."""
        print("📋 Recent Dashboard Logs")
        print("=" * 40)

        if not self.log_dir.exists():
            print("❌ No log directory found")
            return

        log_files = list(self.log_dir.glob("*.log"))
        if not log_files:
            print("❌ No log files found")
            return

        # Get the most recent log file
        latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 Showing last 50 lines from: {latest_log.name}")
        print("-" * 40)

        try:
            with open(latest_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-50:]:  # Show last 50 lines
                    print(line.rstrip())
        except Exception as e:
            print(f"❌ Error reading log file: {e}")

    def start_service(self):
        """Start the dashboard service."""
        print("🚀 Starting dashboard service...")

        success, stdout, stderr = self.run_command(
            ["sudo", "systemctl", "start", self.service_name], check=False)
        if success:
            print("✅ Dashboard service started")
            time.sleep(2)  # Wait a moment
            self.check_status()
        else:
            print(f"❌ Failed to start service: {stderr}")

    def restart_service(self):
        """Restart the dashboard service."""
        print("🔄 Restarting dashboard service...")

        success, stdout, stderr = self.run_command(
            ["sudo", "systemctl", "restart", self.service_name], check=False)
        if success:
            print("✅ Dashboard service restarted")
            time.sleep(2)  # Wait a moment
            self.check_status()
        else:
            print(f"❌ Failed to restart service: {stderr}")

    def uninstall_service(self):
        """Uninstall the dashboard service."""
        print("🗑️ Uninstalling dashboard service...")

        # Stop and disable service
        self.run_command(["sudo", "systemctl", "stop",
                         self.service_name], check=False)
        self.run_command(["sudo", "systemctl", "disable",
                         self.service_name], check=False)

        # Remove service file
        service_file = f"/etc/systemd/system/{self.service_name}.service"
        success, stdout, stderr = self.run_command(
            ["sudo", "rm", "-f", service_file], check=False)

        if success:
            self.run_command(
                ["sudo", "systemctl", "daemon-reload"], check=False)
            print("✅ Dashboard service uninstalled")
        else:
            print(f"❌ Failed to remove service file: {stderr}")


def main():
    """Main entry point."""
    # Auto-switch to venv if needed for --run commands
    auto_use_venv_if_needed()

    parser = argparse.ArgumentParser(
        description="Simple RPi Dashboard Manager")
    parser.add_argument("--check-prereq", action="store_true",
                        help="Check prerequisites and permissions")
    parser.add_argument("--setup", action="store_true",
                        help="Setup environment (venv + packages + directories)")
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

    args = parser.parse_args()
    dashboard = SimpleDashboard()

    if args.check_prereq:
        dashboard.check_prerequisites()
    elif args.setup:
        dashboard.setup_environment()
    elif args.create_service:
        dashboard.create_service_only()
    elif args.install:
        # Full installation: setup + service creation
        print("🚀 Full installation starting...")
        if dashboard.setup_environment():
            dashboard.create_service_only()
    elif args.run or args.run_service:
        # Both --run and --run-service do the same thing
        script_dir = Path(__file__).parent.absolute()
        venv_dir = script_dir / "venv"

        if not venv_dir.exists():
            print("❌ Virtual environment not found!")
            print("🔧 Please run setup first:")
            print("   python3 simple_rpi_dashboard.py --setup")
            print("   python3 simple_rpi_dashboard.py --create-service")
            print("")
            print("💡 Or use the quick install:")
            print("   python3 simple_rpi_dashboard.py --install")
            sys.exit(1)

        dashboard.run_dashboard()
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
        print("🔌 Simple RPi Dashboard Manager")
        print("\n📋 Prerequisites Check:")
        print("  python3 simple_rpi_dashboard.py --check-prereq   # Check system prerequisites")
        print("\n🔧 Setup Commands:")
        print("  python3 simple_rpi_dashboard.py --setup          # Setup environment only (no sudo)")
        print("  python3 simple_rpi_dashboard.py --create-service # Create service file (requires sudo)")
        print("  python3 simple_rpi_dashboard.py --install        # Full setup + service (requires sudo)")
        print("\n▶️  Running:")
        print("  python3 simple_rpi_dashboard.py --run            # Run dashboard manually (auto-uses venv)")
        print("  python3 simple_rpi_dashboard.py --status         # Check service status")
        print("")
        print("💡 Note: --run automatically uses virtual environment if available")
        print("\n🔧 Service Management:")
        print("  python3 simple_rpi_dashboard.py --start          # Start service")
        print("  python3 simple_rpi_dashboard.py --stop           # Stop service")
        print("  python3 simple_rpi_dashboard.py --restart        # Restart service")
        print("  python3 simple_rpi_dashboard.py --logs           # View logs")
        print("  python3 simple_rpi_dashboard.py --uninstall      # Remove service")
        print("\n📖 For manual setup without sudo prompts, see: docs/MANUAL_SETUP.md")


if __name__ == "__main__":
    main()
