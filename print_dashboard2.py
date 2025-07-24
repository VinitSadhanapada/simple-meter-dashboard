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
                           and development. Default: True.
    
    READING_INTERVAL (int): Time interval in seconds between meter reading cycles.
                           This determines how often data is collected from all meters.
                           Default: 10 seconds.
    
    PUBLISH_MQTT (bool): Enable or disable MQTT message publishing. When True,
                        meter readings are published to configured MQTT topics.
                        Default: True.
    
    REFRESH_INTERVAL (int): Dashboard display refresh interval in seconds.
                           Controls how often the console display is updated.
                           Should be <= READING_INTERVAL for optimal display.
                           Default: 5 seconds.
"""

# Configuration
SIMULATION_MODE = False  # Set False for real measurements
READING_INTERVAL = 10   # Interval in seconds
PUBLISH_MQTT = True     # Toggle MQTT publishing
REFRESH_INTERVAL = 5    # Dashboard refresh interval

# Hardware Configuration (same as legacy version)
#PORT = "/dev/ttyUSB0"  # For Linux/Raspberry Pi
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

# Setup meters and manager
meters = [
    MeterDevice(
        name=DEVICE_NAMES[i], 
        model="LG6400", 
        parameters=PARAMETERS, 
        client=client,
        error_file=error_file,
        simulation_mode=SIMULATION_MODE
    ) for i in range(1)
]
manager = MeterManager(
    meters,
    PARAMETERS,
    ["Device_1.csv"],
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