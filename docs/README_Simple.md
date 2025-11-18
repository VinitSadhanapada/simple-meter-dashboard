# Raspberry Pi Auto-Startup Guide

**📖 For complete documentation and desktop usage, see [README.md](README.md)**

This guide focuses specifically on setting up the Raspberry Pi for automatic startup with the simple single-script approach.

## 🤖 Quick RPi Setup

**Much simpler than the old multi-script approach!** Everything is handled by a single Python script.

```bash
# 1. Initial setup (creates venv, installs dependencies)
python3 simple_rpi_dashboard.py --setup

# 2. Install auto-startup service
python3 simple_rpi_dashboard.py --install

# 3. Check if it's working
python3 simple_rpi_dashboard.py --status
```

That's it! The dashboard will now start automatically on boot.

## What This Single Script Does

✅ **Automatic venv creation and dependency installation**  
✅ **Uses systemd service (more reliable than crontab)**  
✅ **CSV logging with device names**  
✅ **Headless operation**  
✅ **Proper error handling and logging**  
✅ **Offline package support** (auto-detects if available)

## 🔧 Management Commands

```bash
# Manual control
python3 simple_rpi_dashboard.py --start    # Start service manually
python3 simple_rpi_dashboard.py --stop     # Stop service
python3 simple_rpi_dashboard.py --restart  # Restart service

# Monitoring
python3 simple_rpi_dashboard.py --status   # Check service status
python3 simple_rpi_dashboard.py --logs     # View logs

# Maintenance
python3 simple_rpi_dashboard.py --uninstall # Remove service
```

## 🌐 Offline Installation Support

The script automatically detects offline packages:

```bash
# If you have offline_packages/ directory, the script will use it automatically
python3 simple_rpi_dashboard.py --setup
```

For preparing offline packages, see [OFFLINE_INSTALLATION.md](OFFLINE_INSTALLATION.md)

## 📁 File Structure After Setup

```
project_directory/
├── simple_rpi_dashboard.py   # Main script
├── dashboard_venv/           # Virtual environment  
├── logs/                     # System logs
│   ├── dashboard_20250724.log
│   └── error_20250724.log
└── csv_data/                 # CSV data files
    └── Device_1_20250724.csv
```

## 🔍 Troubleshooting

### Service Not Starting
```bash
# Check service status
python3 simple_rpi_dashboard.py --status

# View detailed logs
python3 simple_rpi_dashboard.py --logs

# Try manual start to see errors
python3 simple_rpi_dashboard.py --start
```

### Dependencies Issues
```bash
# Re-run setup to fix dependencies
python3 simple_rpi_dashboard.py --setup

# Check if venv was created properly
ls -la dashboard_venv/
```

### Hardware Detection
```bash
# Check available serial ports
ls /dev/tty*

# Add user to dialout group
sudo usermod -a -G dialout $USER
# Then reboot
```

## 🆚 Why This Approach vs Old Method?

| Feature | **New Simple Script** | Old Multi-Script |
|---------|----------------------|------------------|
| **Setup Commands** | 3 commands | 6+ shell scripts |
| **Startup Method** | systemd service | crontab |
| **Reliability** | High | Medium |
| **Error Handling** | Comprehensive | Basic |
| **Maintenance** | Single script | Multiple files |
| **Offline Support** | Auto-detection | Manual setup |

## 🚀 Advanced Usage

### Custom Configuration
Edit the configuration section in `simple_rpi_dashboard.py`:
```python
# Hardware settings
PORT = "/dev/ttyUSB0"  # Your serial port
BAUD_RATE = 9600

# Timing settings  
READING_INTERVAL = 10  # Seconds between readings
STARTUP_DELAY = 60     # Delay after boot before starting

# Logging
LOG_LEVEL = "INFO"     # DEBUG, INFO, WARNING, ERROR
```

### Integration with Other Services
The systemd service can be configured to depend on other services:
```bash
# Edit the service file (advanced users)
sudo systemctl edit meter-dashboard.service
```

For complete documentation including desktop usage and offline installation, see **[README.md](README.md)**

## What This Single Script Does

✅ **Automatic venv creation and dependency installation**  
✅ **Uses systemd service (more reliable than crontab)**  
✅ **CSV logging with device names**  
✅ **Headless operation**  
✅ **Proper error handling and logging**  

## Available Commands

```bash
python3 simple_rpi_dashboard.py --setup      # One-time setup
python3 simple_rpi_dashboard.py --install    # Install auto-startup
python3 simple_rpi_dashboard.py --run        # Run manually (for testing)
python3 simple_rpi_dashboard.py --status     # Check status
python3 simple_rpi_dashboard.py --stop       # Stop service
```

## Configuration

Edit the `CONFIG` section in `simple_rpi_dashboard.py`:

```python
CONFIG = {
    "SIMULATION_MODE": False,     # Set True for testing
    "READING_INTERVAL": 10,       # Seconds between readings
    "PORT": "/dev/ttyUSB0",       # Your serial port
    "ENABLE_MQTT": True,          # Enable MQTT publishing
    "LOG_LEVEL": "INFO"           # Logging level
}
```

## File Structure (Much Cleaner!)

```
project_directory/
├── simple_rpi_dashboard.py    # THE ONLY SCRIPT YOU NEED!
├── venv/                      # Auto-created virtual environment
├── logs/                      # Auto-created log files
├── csv_data/                  # Auto-created CSV files
└── (your existing meter files: meter_device.py, etc.)
```

## Why This Is Better

| Old Approach | New Approach |
|--------------|--------------|
| 5+ shell scripts | 1 Python script |
| Manual crontab | Systemd service |
| Complex setup | 3 simple commands |
| Hard to debug | Integrated logging |
| Platform-specific | Cross-platform |

## Troubleshooting

```bash
# Check what's happening
python3 simple_rpi_dashboard.py --status

# View logs
tail -f logs/dashboard_*.log

# Stop and restart
python3 simple_rpi_dashboard.py --stop
python3 simple_rpi_dashboard.py --install
```

## Remove Auto-Startup

```bash
sudo systemctl disable meter-dashboard
sudo systemctl stop meter-dashboard  
sudo rm /etc/systemd/system/meter-dashboard.service
```

**This approach is much cleaner and easier to maintain!** 🎉
