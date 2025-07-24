# Print Dashboard v2 - Meter Reading System

A simplified, standalone meter reading dashboard for electrical meters with MQTT integration.

## Features

-  **Real-time meter reading** from Modbus RTU devices
-  **Console dashboard** with continuous data display
-  **MQTT integration** for real-time data publishing
-  **CSV data logging** for historical data storage
-  **Auto-refresh display** with configurable intervals
-  **Cross-platform** support (Windows/Linux/RPi)
-  **Easy configuration** via simple variables

## Quick Start

### 1. Install Dependencies

`ash
pip install -r requirements.txt
`

### 2. Configure Hardware

Edit print_dashboard2.py and set your COM port:

`python
# For Windows
PORT = "COM7"  # Change to your actual COM port

# For Linux/Raspberry Pi
# PORT = "/dev/ttyUSB0"
`

### 3. Run the Dashboard

`ash
python print_dashboard2.py
`

## Configuration

Edit the configuration variables in print_dashboard2.py:

`python
SIMULATION_MODE = False  # Set True for testing without hardware
READING_INTERVAL = 10   # Seconds between meter readings
PUBLISH_MQTT = True     # Enable/disable MQTT publishing
REFRESH_INTERVAL = 5    # Dashboard refresh rate
`

## Supported Meters

- **LG6400** - 3-Phase Energy Meter
- **LG5220** - Single Phase Energy Meter  
- **LG5310** - 3-Phase Energy Meter
- **EN8410** - Power Quality Analyzer
- **iELR300** - Energy Logger

## File Structure

`
first_deployv2/
 print_dashboard2.py    # Main application
 meter_manager.py       # Multi-meter management
 meter_device.py        # Individual meter communication
 macros.py             # Device definitions and parameters
 mqtt_client.py        # MQTT publishing functionality
 elmeasure_*.py        # Device-specific implementations
 requirements.txt      # Python dependencies
 README.md            # This file
`

## Data Output

### Console Display
Real-time tabular display of all meter parameters with timestamps and system status.

### CSV Logging
Data is automatically saved to CSV files with timestamps:
- Device_1.csv - Contains all meter readings with timestamps

### MQTT Publishing
Real-time data published to MQTT broker (if enabled) for integration with other systems.

## Hardware Requirements

- **RS-485 to USB converter** for meter communication
- **Electrical meters** with Modbus RTU support
- **Python 3.7+** environment

## Development

This is a simplified version focused on core functionality:
- Removed web interface and complex setup
- Streamlined configuration
- Essential features only
- Easy to understand and modify

## Troubleshooting

### Connection Issues
1. Check COM port assignment in Device Manager
2. Verify meter wiring and RS-485 converter
3. Test with SIMULATION_MODE = True first

### MQTT Issues
1. Check MQTT broker configuration in mqtt_client.py
2. Verify network connectivity
3. Disable with PUBLISH_MQTT = False if not needed

## License

Open source - feel free to modify and distribute.

## Author

Selvakumar Sadhanapada  
Date: 2025-07-24  
Version: 2.0
