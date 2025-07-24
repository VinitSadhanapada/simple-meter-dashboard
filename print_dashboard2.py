"""
Continuous Meter Reading Dashboard with MQTT Integration.

This module provides a console-based dashboard that continuously reads data from
multiple meter devices, displays the readings in a tabular format, logs to CSV files,
and optionally publishes data to MQTT brokers.

Features:
    - Real-time meter data reading (simulation or hardware)
    - Continuous console dashboard with auto-refresh
    - MQTT publishing integration
    - CSV data logging
    - Configurable reading and refresh intervals
    - Clean shutdown handling

Usage:
    python print_dashboard2.py

Configuration:
    Modify the configuration variables at the top of the file:
    - SIMULATION_MODE: Enable/disable simulation mode
    - READING_INTERVAL: Time between meter readings
    - PUBLISH_MQTT: Enable/disable MQTT publishing
    - REFRESH_INTERVAL: Dashboard refresh rate

Author: Selvakumar Sadhanapada
Date: 21/07/25
Version: 1.0
"""

"""
Required module imports for meter reading dashboard functionality.

Standard Library:
    time: For timing control and timestamps
    os: For cross-platform console clearing

Project Modules:
    meter_manager: Core meter management and data collection
    meter_device: Individual meter device communication
    macros: Device names, parameters, and configuration constants
    mqtt_client: MQTT publishing functionality
"""
from meter_manager import MeterManager
from meter_device import MeterDevice
from macros import DEVICE_NAMES, PARAMETERS
import mqtt_client as mqtt
import time
import os
import platform
from datetime import datetime

# Try to import venv utilities (optional - for advanced setup)
try:
    from venv_utils import setup_complete_venv_environment
    VENV_UTILS_AVAILABLE = True
except ImportError:
    VENV_UTILS_AVAILABLE = False

# Modbus imports for hardware communication (same as legacy version)
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

# Configuration Section
"""
Dashboard Configuration Parameters.

These constants control the behavior of the meter reading dashboard.
Modify these values to customize the system behavior for your specific setup.

Constants:
    SIMULATION_MODE (bool): If True, generates simulated meter data instead of
                           reading from actual hardware. Useful for testing
                           and development. Default: False.
    
    READING_INTERVAL (int): Time interval in seconds between meter reading cycles.
                           This determines how often data is collected from all meters.
                           Default: 10 seconds.
    
    PUBLISH_MQTT (bool): Enable or disable MQTT message publishing. When True,
                        meter readings are published to configured MQTT topics.
                        Default: False.
    
    REFRESH_INTERVAL (int): Dashboard display refresh interval in seconds.
                           Controls how often the console display is updated.
                           Should be <= READING_INTERVAL for optimal display.
                           Default: 5 seconds.
    
    DEVICE_CONFIG (list): Configuration for all meter devices to monitor.
                         Each device is defined as a dictionary with:
                         - name: Display name for the device
                         - address: Modbus device address (1-247)
                         - model: Device model (LG6400, EN8410, etc.)
                         
                         Example:
                         DEVICE_CONFIG = [
                             {"name": "Main Panel", "address": 1, "model": "LG6400"},
                             {"name": "Generator", "address": 2, "model": "LG6400"},
                         ]
"""

# Configuration
SIMULATION_MODE = False  # Set False for real measurements
READING_INTERVAL = 10   # Interval in seconds
PUBLISH_MQTT = False     # Toggle MQTT publishing
REFRESH_INTERVAL = 5    # Dashboard refresh interval

# Device Configuration - Customize your meters here
DEVICE_CONFIG = [
    {"name": "Main Panel", "address": 1, "model": "LG6400"},
    {"name": "Generator Set", "address": 2, "model": "LG6400"},
    {"name": "UPS System", "address": 3, "model": "LG6400"},
    # Add more devices as needed:
    # {"name": "Your Device Name", "address": 4, "model": "LG6400"},
    # {"name": "Another Device", "address": 5, "model": "EN8410"},
]

# Extract device names for compatibility with existing code
DEVICE_NAMES = [device["name"] for device in DEVICE_CONFIG]

# Optional: Override the imported DEVICE_NAMES from macros
import macros
macros.DEVICE_NAMES = DEVICE_NAMES

# Hardware Configuration - Auto-detect platform
import platform
if platform.system() == "Linux":
    # Linux/Raspberry Pi - try common serial ports
    PORT = "/dev/ttyUSB0"  # Most common for USB-to-Serial adapters
    if not os.path.exists(PORT):
        alternative_ports = ["/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyAMA0"]
        for alt_port in alternative_ports:
            if os.path.exists(alt_port):
                PORT = alt_port
                break
else:
    # Windows
    PORT = "COM7"           # For Windows - Change this to your actual COM port (COM3, COM6, COM7, etc.)

# Initialize MQTT
mqtt.mqtt_main()

# Setup Modbus client for hardware communication (same approach as legacy)
client = None
error_file = None

if not SIMULATION_MODE:
    client = ModbusClient(method="rtu", port=PORT, stopbits=1, bytesize=8, parity='E', baudrate=9600, timeout=0.5)
    
    try:
        client.connect()
        print(f"✓ Successfully connected to {PORT}")
        error_file = open("error_log.txt", "a")
    except:
        print(f"✗ Unable to connect to {PORT}")
        print("Falling back to simulation mode...")
        SIMULATION_MODE = True
        client = None

# Create CSV data directory and generate filenames based on device names
import os
from datetime import datetime

csv_dir = "csv_data"
os.makedirs(csv_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d")
csv_filenames = []
for device in DEVICE_CONFIG:
    # Clean device name for filename (remove spaces, special chars)
    clean_name = "".join(c for c in device["name"] if c.isalnum() or c in ('-', '_'))
    filename = f"{csv_dir}/{clean_name}_{timestamp}.csv"
    csv_filenames.append(filename)

# Setup meters and manager using the new device configuration
meters = []
for i, device in enumerate(DEVICE_CONFIG):
    meter = MeterDevice(
        name=device["name"], 
        model=device["model"], 
        parameters=PARAMETERS, 
        client=client,
        error_file=error_file,
        simulation_mode=SIMULATION_MODE,
        device_address=device["address"]  # Pass the device address
    )
    meters.append(meter)
manager = MeterManager(
    meters,
    PARAMETERS,
    csv_filenames,
    mqtt_client=mqtt,
    publish_mqtt=PUBLISH_MQTT
)

"""
Main Dashboard Execution Loop.

This section initializes the meter reading system and runs the continuous
dashboard display loop until interrupted by the user.

Process Flow:
    1. Initialize MQTT client connection
    2. Create MeterDevice instances for each configured device
    3. Initialize MeterManager with devices and configuration
    4. Start continuous reading and display loop
    5. Handle graceful shutdown on keyboard interrupt

The loop performs the following actions each cycle:
    - Clear the console display
    - Read data from all configured meters
    - Display current readings in tabular format
    - Show system status and timing information
    - Wait for next refresh cycle

Error Handling:
    - KeyboardInterrupt: Graceful shutdown with cleanup
    - Meter reading errors: Logged and handled by MeterManager
    - MQTT connection issues: Handled by mqtt_client module
"""

def setup_venv_if_requested():
    """
    Optional venv setup for print_dashboard2.py
    
    This function can be called with special command line arguments to set up
    a virtual environment with all required dependencies.
    
    Usage:
        python print_dashboard2.py --setup-venv           # Online installation
        python print_dashboard2.py --setup-venv --offline # Offline installation
        python print_dashboard2.py --check-venv           # Check if venv exists and is working
    """
    import sys
    from pathlib import Path
    
    if '--setup-venv' in sys.argv:
        if not VENV_UTILS_AVAILABLE:
            print("❌ venv_utils not available. Make sure venv_utils.py is in the same directory.")
            return False
        
        # Check if offline mode is requested
        offline_mode = '--offline' in sys.argv
        offline_dir = None
        
        if offline_mode:
            offline_dir = "offline_packages"
            offline_path = Path(offline_dir)
            if not offline_path.exists():
                print(f"❌ Offline packages directory not found: {offline_path}")
                print("💡 To prepare offline packages, run: python prepare_offline.py")
                return False
            print(f"🔧 Setting up virtual environment offline from: {offline_path}")
        else:
            print("🔧 Setting up virtual environment online...")
        
        # Required packages for the dashboard
        required_packages = [
            "pymodbus==2.5.3",
            "pyserial==3.5", 
            "paho-mqtt==2.1.0",
            "termcolor==3.1.0",
            "numpy==1.24.3",
            "pandas==2.0.3"
        ]
        
        script_dir = Path(__file__).parent.absolute()
        venv_dir = script_dir / "dashboard_venv"
        
        success, python_exe = setup_complete_venv_environment(
            venv_dir=venv_dir,
            packages=required_packages,
            force_recreate=False,
            offline_dir=offline_dir
        )
        
        if success:
            mode_str = "offline" if offline_mode else "online"
            print(f"✅ Virtual environment setup complete ({mode_str})!")
            print(f"📍 Virtual environment location: {venv_dir}")
            print(f"🐍 Python executable: {python_exe}")
            print("")
            print("To use the virtual environment:")
            if os.name == 'nt':  # Windows
                print(f"   {venv_dir}\\Scripts\\activate")
                print(f"   python print_dashboard2.py")
            else:  # Linux/macOS
                print(f"   source {venv_dir}/bin/activate")
                print(f"   python print_dashboard2.py")
        else:
            print("❌ Virtual environment setup failed!")
        
        return success
    
    elif '--check-venv' in sys.argv:
        script_dir = Path(__file__).parent.absolute()
        venv_dir = script_dir / "dashboard_venv"
        
        print("🔍 Checking virtual environment status...")
        
        if venv_dir.exists():
            print(f"✅ Virtual environment exists: {venv_dir}")
            
            # Check if python executable exists
            if os.name == 'nt':
                python_exe = venv_dir / "Scripts" / "python.exe"
            else:
                python_exe = venv_dir / "bin" / "python"
            
            if python_exe.exists():
                print(f"✅ Python executable found: {python_exe}")
                
                # Try to check installed packages
                try:
                    import subprocess
                    result = subprocess.run([str(python_exe), "-m", "pip", "list"], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print("✅ pip is working in venv")
                        print("📦 Installed packages:")
                        for line in result.stdout.split('\n')[:10]:  # Show first 10 packages
                            if line.strip() and not line.startswith('Package'):
                                print(f"   {line}")
                    else:
                        print("⚠️ pip not working properly in venv")
                except Exception as e:
                    print(f"⚠️ Error checking packages: {e}")
            else:
                print("❌ Python executable not found in venv")
        else:
            print("❌ Virtual environment not found")
            print("Run: python print_dashboard2.py --setup-venv")
        
        return True
    
    return None  # No venv setup requested

# Check for venv setup commands before normal execution
venv_result = setup_venv_if_requested()
if venv_result is not None:
    # If venv setup was requested, exit after handling it
    exit(0 if venv_result else 1)

print("Starting Meter Reading Dashboard...")
print("Press Ctrl+C to stop")
print("=" * 80)

try:
    next_time = time.time()
    while True:
        # Clear the screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Read new data (this also publishes to MQTT if enabled)
        manager.read_all()
        
        # Print header with status
        print(f"Meter Reading Dashboard - Cycle: {manager.TotalReadings}")
        print(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"MQTT Publishing: {'Enabled' if PUBLISH_MQTT else 'Disabled'}")
        print(f"Simulation Mode: {'Enabled' if SIMULATION_MODE else 'Disabled'}")
        print("=" * 80)
        
        # Data Display Section
        """
        Format and display meter readings in tabular format.
        
        The display shows:
        - Header row with device name and all parameter names
        - One row per device with current readings
        - Values are converted to strings for consistent display formatting
        """

        # Print table header
        header = ["Device"] + PARAMETERS
        print("\t".join(header))
        print("-" * 120)  # separator line
        
        # Print each device's readings
        for i, values in enumerate(manager.allRegValues):
            row = [DEVICE_NAMES[i]] + [str(val) for val in values]
            print("\t".join(row))
        
        print("=" * 80)
        print(f"Next update in {REFRESH_INTERVAL} seconds... (Press Ctrl+C to exit)")
        
        

        # Calculate precise sleep time
        next_time += REFRESH_INTERVAL
        sleep_time = max(0, next_time - time.time())
        time.sleep(sleep_time)
        
except KeyboardInterrupt:
    print("\nShutting down dashboard...")
    manager.close()
    mqtt.mqtt_close()
    
    # Close Modbus connection and error file
    if client and hasattr(client, 'close'):
        client.close()
        print("✓ Modbus connection closed")
    
    if error_file:
        error_file.close()
        print("✓ Error log file closed")
    
    print("Dashboard stopped.")