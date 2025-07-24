# 🚀 RPi Manual Setup - Quick Guide

**Complete manual setup without sudo prompts during script execution**

## 🔍 Quick Prerequisites Check

```bash
# Check if your system is ready
python3 simple_rpi_dashboard.py --check-prereq
```

If all checks pass, you can use the **automated approach** below. If issues are found, follow the **manual approach**.

## 🤖 Automated Approach (After Prerequisites)

If `--check-prereq` shows all green checkmarks:

```bash
# 1. Setup environment (venv, packages, directories)
python3 simple_rpi_dashboard.py --setup

# 2. Create service (requires sudo)
sudo python3 simple_rpi_dashboard.py --create-service

# 3. Check status
python3 simple_rpi_dashboard.py --status
```

## 📋 Manual Approach (Step by Step)

### Prerequisites (One-time, requires sudo)

```bash
# 1. System packages and permissions
sudo apt update
sudo apt install python3-venv python3-pip -y
sudo usermod -a -G dialout $USER

# 2. Reboot to apply changes
sudo reboot
```

## Environment Setup (No sudo required)

```bash
# 1. Create and activate virtual environment
python3 -m venv dashboard_venv
source dashboard_venv/bin/activate

# 2. Install all dependencies
pip install pymodbus==2.5.3 pyserial==3.5 paho-mqtt==2.1.0 termcolor==3.1.0 numpy==1.24.3 pandas==2.0.3

# 3. Create required directories
mkdir -p logs csv_data

# 4. Test dashboard (should work without errors)
python3 simple_rpi_dashboard.py
```

## Service Installation (One-time, requires sudo)

```bash
# Create systemd service file
sudo tee /etc/systemd/system/meter-dashboard.service > /dev/null <<EOF
[Unit]
Description=Meter Reading Dashboard  
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)  
Environment=PATH=$(pwd)/dashboard_venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$(pwd)/dashboard_venv/bin/python $(pwd)/simple_rpi_dashboard.py --run-service
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable meter-dashboard
sudo systemctl start meter-dashboard
```

## Verification (No sudo required)

```bash
# Check service status
systemctl status meter-dashboard

# View real-time logs
journalctl -u meter-dashboard -f

# Check if CSV files are being created
ls -la csv_data/
```

## Management Commands

### No Sudo Required:
```bash
systemctl status meter-dashboard          # Check status
journalctl -u meter-dashboard            # View logs
journalctl -u meter-dashboard -f         # Follow logs
ls logs/ csv_data/                       # Check output files
```

### Requires Sudo:
```bash
sudo systemctl start meter-dashboard     # Start service
sudo systemctl stop meter-dashboard      # Stop service  
sudo systemctl restart meter-dashboard   # Restart service
```

## Troubleshooting

### Service won't start:
```bash
# Check detailed status
systemctl status meter-dashboard -l

# Check recent logs
journalctl -u meter-dashboard --since "10 minutes ago"

# Test script manually
source dashboard_venv/bin/activate
python3 simple_rpi_dashboard.py
```

### Permission issues:
```bash
# Verify user is in dialout group
groups $USER

# If not in dialout group, add and reboot:
# sudo usermod -a -G dialout $USER
# sudo reboot
```

### Hardware not detected:
```bash
# Check available serial ports
ls /dev/tty*

# Look for USB devices
lsusb
```

**After this manual setup, the dashboard will start automatically on every boot!**
