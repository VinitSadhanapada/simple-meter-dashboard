# Meter Reading Dashboard System

A comprehensive electrical meter reading system with multiple deployment options for different use cases.

## 🎯 Choose Your Use Case

### 📱 **Desktop/Manual Operation** 
**For interactive use on Windows/Linux desktops**
- Interactive console dashboard
- Manual start/stop control  
- Real-time monitoring and debugging
- ➡️ **Use:** `print_dashboard2.py`

### 🤖 **Raspberry Pi Auto-Startup**
**For unattended RPi deployments**
- Automatic startup on boot
- Headless operation
- Systemd service management
- CSV logging with device names
- ➡️ **Use:** `simple_rpi_dashboard.py`

### 🌐 **Offline/Air-Gapped Deployment**
**For systems without internet connectivity**
- Pre-downloaded packages
- Offline installation support
- Works with both desktop and RPi modes
- ➡️ **See:** `docs/OFFLINE_INSTALLATION.md`

---

## 📱 Desktop/Manual Operation

### Quick Start
```bash
# Basic usage (auto-installs dependencies if needed)
python print_dashboard2.py

# With virtual environment setup
python print_dashboard2.py --setup-venv

# Check if virtual environment is working
python print_dashboard2.py --check-venv

# Offline installation (if offline packages available)
python print_dashboard2.py --setup-venv --offline
```

### Features
- **Real-time meter reading** from Modbus RTU devices
- **Interactive console dashboard** with live data display
- **MQTT integration** for real-time data publishing  
- **CSV data logging** for historical data storage
- **Auto-refresh display** with configurable intervals
- **Cross-platform** support (Windows/Linux/RPi)
- **Optional virtual environment** management

### Hardware Configuration
Edit `print_dashboard2.py` and set your COM port:
```python
# Windows
PORT = "COM7"  # Change to your actual COM port

# Linux/RPi  
PORT = "/dev/ttyUSB0"  # Change to your actual device
```

### Configuration Options
```python
SIMULATION_MODE = False  # Set True for testing without hardware
READING_INTERVAL = 10   # Seconds between meter readings
PUBLISH_MQTT = True     # Enable/disable MQTT publishing
REFRESH_INTERVAL = 5    # Dashboard refresh rate

# Device Configuration - Easily customize your meters
DEVICE_CONFIG = [
    {"name": "Main Panel", "address": 1, "model": "LG6400"},
    {"name": "Generator Set", "address": 2, "model": "LG6400"},
    {"name": "UPS System", "address": 3, "model": "LG6400"},
    # Add more devices as needed
]
```

**📖 For detailed device configuration guide, see [docs/DEVICE_CONFIG.md](docs/DEVICE_CONFIG.md)**

---

## 🤖 Raspberry Pi Auto-Startup

### Manual Setup (Recommended for Production)

**📖 For complete step-by-step manual setup, see [docs/MANUAL_SETUP.md](docs/MANUAL_SETUP.md)**

**Step 1: Check Prerequisites**
```bash
# Check if system is ready for installation
python3 simple_rpi_dashboard.py --check-prereq
```

**Step 2: Manual Prerequisites (Run with sudo if needed)**
```bash
# Only if --check-prereq found issues:
sudo apt update
sudo apt install python3-venv python3-pip -y
sudo usermod -a -G dialout $USER
sudo reboot
```

**Step 3: Automated Environment Setup (No sudo required)**
```bash
# This creates venv, installs packages, creates directories
python3 simple_rpi_dashboard.py --setup
```

**Step 4: Service Creation (One-time sudo)**
```bash
# This creates and enables the systemd service
python3 simple_rpi_dashboard.py --create-service
```

**Step 5: Verify Installation (No sudo required)**
```bash
# Check service status
python3 simple_rpi_dashboard.py --status

# View logs
python3 simple_rpi_dashboard.py --logs
```

### Automated Setup (Quick but requires sudo prompts)

If you prefer the automated approach with sudo prompts:

```bash
# 1. Initial setup (creates venv, installs dependencies)
python3 simple_rpi_dashboard.py --setup

# 2. Install auto-startup service (will prompt for sudo)
python3 simple_rpi_dashboard.py --install

# 3. Check if it's working
python3 simple_rpi_dashboard.py --status
```

### Management Commands
```bash
# Start service manually
python3 simple_rpi_dashboard.py --start

# Stop service
python3 simple_rpi_dashboard.py --stop

# Restart service
python3 simple_rpi_dashboard.py --restart

# View logs
python3 simple_rpi_dashboard.py --logs

# Uninstall service
python3 simple_rpi_dashboard.py --uninstall
```

### Features
- **Automatic startup** on RPi boot using systemd
- **Headless operation** suitable for unattended deployment
- **CSV logging** with files named after meter devices
- **Comprehensive logging** for debugging and monitoring
- **Graceful shutdown** handling with signal management
- **Automatic hardware detection** with fallback to simulation
- **Offline package support** (auto-detects offline packages)

### File Structure After Setup
```
project_directory/
├── simple_rpi_dashboard.py   # Main script
├── dashboard_venv/           # Virtual environment
├── logs/                     # System logs
│   ├── dashboard_YYYYMMDD.log
│   └── error_YYYYMMDD.log
└── csv_data/                 # CSV data files
    └── Device_1_YYYYMMDD.csv
```

---

## 🌐 Offline/Air-Gapped Installation

For systems without internet connectivity, see the comprehensive offline installation guide:

**📖 [docs/OFFLINE_INSTALLATION.md](docs/OFFLINE_INSTALLATION.md)**

### Quick Overview
```bash
# 1. On internet-connected machine - prepare packages
python prepare_offline.py

# 2. Transfer files to target system

# 3. On target system - install offline
python print_dashboard2.py --setup-venv --offline
# OR
python3 simple_rpi_dashboard.py  # (auto-detects offline packages)
```

---

## 📋 Common Configuration

### Hardware Setup
The system supports various Modbus RTU devices via USB-to-Serial adapters:

**Supported Devices:**
- Elmeasure EN8410 series
- Elmeasure iELR300 series  
- Elmeasure LG5220/LG5310/LG6400 series

**Connection:**
- Use USB-to-Serial RS485 adapter
- Connect A/B terminals to meter's RS485 port
- Set meter address and communication parameters

### MQTT Configuration
```python
# MQTT settings (in both scripts)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "meter/data"
MQTT_USERNAME = None  # Set if authentication required
MQTT_PASSWORD = None  # Set if authentication required
```

### Dependencies
All required packages are automatically managed:
- **pymodbus**: Modbus RTU communication
- **pyserial**: Serial port communication  
- **paho-mqtt**: MQTT messaging
- **termcolor**: Colored terminal output
- **numpy**: Numerical operations
- **pandas**: Data manipulation

---

## 🔧 Troubleshooting

### Common Issues

**Desktop Dashboard Not Starting:**
```bash
# Check dependencies
python print_dashboard2.py --setup-venv

# Run with error output
python print_dashboard2.py
```

**RPi Service Issues:**
```bash
# Check service status
python3 simple_rpi_dashboard.py --status
# OR manually:
systemctl status meter-dashboard

# View detailed logs
python3 simple_rpi_dashboard.py --logs
# OR manually:
journalctl -u meter-dashboard -f

# Restart service (requires sudo)
sudo systemctl restart meter-dashboard
```

**Manual Service Management:**
```bash
# Start service
sudo systemctl start meter-dashboard

# Stop service
sudo systemctl stop meter-dashboard

# Restart service
sudo systemctl restart meter-dashboard

# Remove service (if needed)
sudo systemctl stop meter-dashboard
sudo systemctl disable meter-dashboard
sudo rm /etc/systemd/system/meter-dashboard.service
sudo systemctl daemon-reload
```

**Serial Port Issues:**
```bash
# Linux: Check available ports
ls /dev/tty*

# Linux: Add user to dialout group
sudo usermod -a -G dialout $USER

# Windows: Check Device Manager for correct COM port
```

**Virtual Environment Issues:**
```bash
# Force recreate venv
python print_dashboard2.py --setup-venv
# OR for RPi
python3 simple_rpi_dashboard.py --setup
```

---

## 📊 Performance & Monitoring

### Resource Usage
- **Memory**: ~50MB typical usage
- **CPU**: <5% on modern systems
- **Storage**: ~1MB per day per device (CSV data)
- **Network**: Minimal (MQTT publishing only)

### Monitoring Options
- **Console Output**: Real-time data display (desktop mode)
- **Log Files**: Comprehensive system logging
- **CSV Files**: Historical data storage
- **MQTT**: Real-time data streaming

---

## 🚀 Quick Reference

### Permission Requirements

| Operation | Sudo Required? | Command |
|-----------|----------------|---------|
| **Desktop/Interactive** | `print_dashboard2.py` | No | `python print_dashboard2.py` |
| **Setup Virtual Environment** | No | `python3 -m venv dashboard_venv` |
| **Install Python Packages** | No | `pip install package` (in venv) |
| **Create Service File** | **Yes** | `sudo tee /etc/systemd/system/...` |
| **Enable/Start Service** | **Yes** | `sudo systemctl enable/start` |
| **Check Service Status** | No | `systemctl status meter-dashboard` |
| **View Service Logs** | No | `journalctl -u meter-dashboard` |
| **Add User to Group** | **Yes** | `sudo usermod -a -G dialout $USER` |

### Quick Start Summary

| Use Case | Script | Quick Start |
|----------|--------|-------------|
| **Desktop/Interactive** | `print_dashboard2.py` | `python print_dashboard2.py` |
| **RPi Manual Setup** | `simple_rpi_dashboard.py` | `--check-prereq` → fix issues → `--setup` → `--create-service` |
| **RPi Automated** | `simple_rpi_dashboard.py` | `python3 simple_rpi_dashboard.py --install` (requires sudo) |
| **Offline Installation** | Both + `prepare_offline.py` | `python prepare_offline.py` → transfer → `--offline` |

Choose the approach that best fits your deployment scenario!
