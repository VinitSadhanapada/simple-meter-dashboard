# Simple Meter Dashboard

**Real-time electrical meter monitoring and alerting system for industrial environments.**

[![Django](https://img.shields.io/badge/Django-5.2.5-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)

---

## 🚀 Quick Start

```bash
# 1. Clone and enter directory
cd /home/isha/opt/simple-meter-dashboard

# 2. Start the application
docker compose up -d

# 3. Access the dashboard
open http://localhost:8000
```

**That's it!** See [docs/QUICK_START.md](docs/QUICK_START.md) for detailed setup.

---

## 📚 Complete Documentation

All documentation has been organized into the **docs/** folder:

### Essential Reading
- **[00_DOCUMENTATION_INDEX.md](docs/00_DOCUMENTATION_INDEX.md)** - Documentation hub (start here)
- **[QUICK_START.md](docs/QUICK_START.md)** - 5-minute setup guide
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - One-page cheat sheet
- **[PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md)** - Complete system architecture

### For Deployment
- **[DEPLOYMENT_SECURITY_CHECKLIST.md](docs/DEPLOYMENT_SECURITY_CHECKLIST.md)** - Critical security issues ⚠️
- **[README_DEPLOY_USB.md](docs/README_DEPLOY_USB.md)** - Offline deployment guide
- **[README_UBUNTU_HOST_SETUP.md](docs/README_UBUNTU_HOST_SETUP.md)** - Ubuntu host setup

### For Maintenance
- **[FILE_CLEANUP_GUIDE.md](docs/FILE_CLEANUP_GUIDE.md)** - Legacy file identification
- **[CLEANUP_COMPLETED.md](docs/CLEANUP_COMPLETED.md)** - Recent cleanup report
- **[SAFE_CLEANUP_STEPS.md](docs/SAFE_CLEANUP_STEPS.md)** - How cleanup was done
- **[HANDOVER_SUMMARY.md](docs/HANDOVER_SUMMARY.md)** - Status summary

---

## 🎯 What This System Does

### Real-Time Monitoring
- **277K+ meter readings** from 5 devices
- **Live data ingestion** via MQTT protocol
- **Web dashboard** at http://localhost:8000
- **Grafana analytics** at http://localhost:3000

### Alert System
- Real-time voltage/current/power factor monitoring
- Celery + Redis for async alert processing
- Email notifications (configured in .env.grafana)
- Alert history and event tracking

### Device Management (DCMS)
- SSH-based device configuration
- Remote script deployment to Raspberry Pis
- Device health monitoring
- Configuration export/import

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         IoT Devices (Raspberry Pi)          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Meter 1  │  │ Meter 2  │  │ Meter 3  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │ Modbus      │ Modbus      │ Modbus  │
│       ▼             ▼             ▼         │
│  ┌────────────────────────────────────────┐ │
│  │        MQTT Publisher (Mosquitto)      │ │
│  └──────────────────┬─────────────────────┘ │
└─────────────────────┼───────────────────────┘
                      │ MQTT over network
                      ▼
┌─────────────────────────────────────────────┐
│        Simple Meter Dashboard (Server)      │
│  ┌──────────────────────────────────────┐   │
│  │    Django Web App (Port 8000)        │   │
│  │  - REST API                          │   │
│  │  - Web UI                            │   │
│  │  - MQTT Subscriber                   │   │
│  │  - Celery Workers (Alerts)           │   │
│  └────┬────────────┬──────────────┬─────┘   │
│       │            │              │          │
│       ▼            ▼              ▼          │
│  ┌─────────┐  ┌────────┐    ┌──────────┐   │
│  │PostgreSQL│  │ Redis  │    │ Grafana  │   │
│  │(External)│  │(Host)  │    │(Port3000)│   │
│  └──────────┘  └────────┘    └──────────┘   │
└─────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

- **Backend:** Django 5.2.5, Python 3.10
- **Database:** PostgreSQL 14+ (external: 192.168.112.106)
- **Cache/Queue:** Redis (host: host.docker.internal:6379)
- **Task Queue:** Celery
- **MQTT:** Paho MQTT client
- **Monitoring:** Grafana + Loki
- **Containerization:** Docker Compose

---

## 📊 Current Status

| Metric | Value |
|--------|-------|
| Total Readings | 277,000+ |
| Active Devices | 5 |
| Database Size | External PostgreSQL |
| Uptime | 43+ hours |
| Last Cleanup | Jan 6, 2026 |
| Space Freed | 1.52 GB |

See [docs/CLEANUP_COMPLETED.md](docs/CLEANUP_COMPLETED.md) for recent cleanup details.

---

## ⚙️ Common Operations

### Start the system
```bash
docker compose up -d
```

### View logs
```bash
docker compose logs -f app
```

### Stop the system
```bash
docker compose down
```

### Rebuild after changes
```bash
docker compose down
docker compose build
docker compose up -d
```

### Access database
```bash
# From inside container
docker exec -it meter_dashboard python meter_dashboard/manage.py dbshell
```

---

## 🔐 Security Notes

⚠️ **10 CRITICAL security issues identified** - See [docs/DEPLOYMENT_SECURITY_CHECKLIST.md](docs/DEPLOYMENT_SECURITY_CHECKLIST.md)

Before production deployment:
1. Change SECRET_KEY
2. Set DEBUG=False
3. Configure ALLOWED_HOSTS
4. Change default database passwords
5. Set up HTTPS
6. Enable CSRF protection
7. Configure proper CORS
8. Set up authentication
9. Review FIELD_ENCRYPTION_KEY
10. Enable security headers

---

## 📁 Project Structure

```
simple-meter-dashboard/
├── README.md                    # This file
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # App container definition
├── requirements.txt             # Python dependencies
│
├── docs/                        # 📚 All documentation
│   ├── 00_DOCUMENTATION_INDEX.md
│   ├── PROJECT_OVERVIEW.md
│   ├── QUICK_START.md
│   ├── DEPLOYMENT_SECURITY_CHECKLIST.md
│   └── ... (see docs/ folder)
│
├── iot_scripts/                 # Server essentials only
│   ├── alerting/                # Celery alert tasks
│   ├── config.json              # DB configuration
│   ├── failure_modes.json       # Alert thresholds
│   ├── mqtt_to_db_ingest.py     # MQTT subscriber
│   └── offline_rpi_dashboard_db.py
│
├── meter_dashboard/             # Django project
│   ├── meter_dashboard/         # Project settings
│   ├── meter_readings/          # Meter readings app
│   ├── templates/               # HTML templates
│   ├── static/                  # CSS/JS/images
│   └── manage.py                # Django management
│
├── scripts/                     # Utility scripts
│   └── cleanup.sh               # Cleanup automation
│
├── device_config_exports/       # DCMS exports
├── grafana/                     # Grafana dashboards
└── .env.grafana                 # Grafana config
```

---

## 🤝 For IT Team / Handover

This project has been cleaned and documented for easy handover:

1. **Start here:** [docs/00_DOCUMENTATION_INDEX.md](docs/00_DOCUMENTATION_INDEX.md)
2. **Quick setup:** [docs/QUICK_START.md](docs/QUICK_START.md)
3. **Security review:** [docs/DEPLOYMENT_SECURITY_CHECKLIST.md](docs/DEPLOYMENT_SECURITY_CHECKLIST.md)
4. **Architecture:** [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md)

All device-specific code has been removed from this server repository. Only server-essential files remain.

See [docs/CLEANUP_COMPLETED.md](docs/CLEANUP_COMPLETED.md) for details on what was cleaned (1.52GB freed).

---

## 📞 Support

For questions or issues:
1. Check [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) for common solutions
2. Review logs: `docker compose logs -f app`
3. Check [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) for architecture details

---

## 📄 License

Internal project for electrical meter monitoring.

---

**Last Updated:** January 6, 2026  
**Status:** ✅ Production-ready (after security hardening)  
**Cleaned:** Yes (1.52GB freed, device code removed)

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

## � Security

### SSH Password Encryption
SSH passwords for Raspberry Pi devices are encrypted using **Fernet encryption** (AES-128) via `django-encrypted-model-fields`. Ensure the `FIELD_ENCRYPTION_KEY` environment variable is set in production deployments.

---

## �🚀 Quick Reference

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
