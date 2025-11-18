# Offline Package Installation Guide

This guide explains how to deploy the meter dashboard on systems without internet connectivity (air-gapped systems).

## Overview

The meter dashboard supports offline installation by pre-downloading all required Python packages on a machine with internet connectivity, then transferring and installing them on the target system.

## Process Overview

1. **Preparation** (on internet-connected machine)
2. **Transfer** (copy files to target system)  
3. **Installation** (on target air-gapped system)

---

## Step 1: Preparation (Internet-Connected Machine)

### 1.1 Download Required Files

Ensure you have these files:
```
meter_dashboard/
├── print_dashboard2.py
├── simple_rpi_dashboard.py
├── venv_utils.py
├── prepare_offline.py
├── meter_manager.py
├── meter_device.py
├── macros.py
├── mqtt_client.py
├── elmeasure_*.py
└── requirements.txt
```

### 1.2 Prepare Offline Packages

Run the preparation script:
```bash
python prepare_offline.py
```

This will:
- Download all required packages and dependencies
- Create an `offline_packages/` directory
- Generate installation scripts
- Create a requirements file

### 1.3 Verify Downloaded Packages

Check the created directory:
```bash
ls offline_packages/
```

You should see:
- `.whl` files (Python wheels)
- `.tar.gz` files (source distributions)
- `offline_requirements.txt`
- `install_offline.py`

---

## Step 2: Transfer to Target System

Copy the entire project directory to your target system:

### Option A: USB/External Drive
```bash
# Copy entire directory
cp -r meter_dashboard/ /media/usb/
```

### Option B: Network Transfer (if available)
```bash
# Using scp
scp -r meter_dashboard/ user@target:/home/user/

# Using rsync
rsync -av meter_dashboard/ user@target:/home/user/meter_dashboard/
```

### Option C: Archive Transfer
```bash
# Create archive
tar -czf meter_dashboard.tar.gz meter_dashboard/

# Transfer and extract on target
tar -xzf meter_dashboard.tar.gz
```

---

## Step 3: Installation (Air-Gapped System)

### 3.1 Navigate to Project Directory
```bash
cd meter_dashboard/
```

### 3.2 Install Using Dashboard Scripts

#### Option A: Interactive Dashboard (print_dashboard2.py)
```bash
# Setup virtual environment offline
python print_dashboard2.py --setup-venv --offline

# Check installation
python print_dashboard2.py --check-venv

# Run dashboard
python print_dashboard2.py
```

#### Option B: RPi Auto-Startup (simple_rpi_dashboard.py)
```bash
# This will auto-detect offline packages
python simple_rpi_dashboard.py
```

### 3.3 Manual Installation (if needed)
```bash
# Create virtual environment manually
python -m venv dashboard_venv

# Activate virtual environment
source dashboard_venv/bin/activate  # Linux/Mac
# OR
dashboard_venv\Scripts\activate     # Windows

# Install packages offline
cd offline_packages/
python install_offline.py ../dashboard_venv/bin/python
```

---

## Package List

The following packages are included for offline installation:

| Package | Version | Purpose |
|---------|---------|---------|
| pymodbus | 2.5.3 | Modbus RTU communication |
| pyserial | 3.5 | Serial port communication |
| paho-mqtt | 2.1.0 | MQTT messaging |
| termcolor | 3.1.0 | Colored terminal output |
| numpy | 1.24.3 | Numerical operations |
| pandas | 2.0.3 | Data manipulation |

---

## Troubleshooting

### Problem: "No package files found"
**Solution:** Ensure `offline_packages/` directory contains `.whl` or `.tar.gz` files

### Problem: "Failed to install package X"
**Solutions:**
1. Check if package file exists in `offline_packages/`
2. Try manual installation:
   ```bash
   pip install --no-index --find-links offline_packages/ package_name
   ```

### Problem: "Virtual environment creation failed"
**Solutions:**
1. Install python3-venv:
   ```bash
   sudo apt-get install python3-venv python3-dev
   ```
2. Use system Python if venv unavailable

### Problem: "Permission denied"
**Solutions:**
1. Check file permissions:
   ```bash
   chmod +x *.py
   ```
2. Run with appropriate user privileges

---

## Advanced Usage

### Custom Offline Package Directory
```bash
# Use custom directory name
python print_dashboard2.py --setup-venv --offline custom_packages/
```

### Force Recreate Virtual Environment
```bash
# This will delete and recreate the venv
python print_dashboard2.py --setup-venv --offline --force
```

### Check Package Dependencies
```bash
# List installed packages in venv
dashboard_venv/bin/python -m pip list
```

---

## File Structure After Installation

```
meter_dashboard/
├── dashboard_venv/              # Virtual environment
│   ├── bin/python              # Python executable (Linux)
│   ├── Scripts/python.exe      # Python executable (Windows)
│   └── lib/python3.x/site-packages/  # Installed packages
├── offline_packages/           # Downloaded packages
│   ├── *.whl                  # Package wheels
│   ├── *.tar.gz               # Source packages
│   ├── offline_requirements.txt
│   └── install_offline.py
├── logs/                      # Application logs
├── csv_data/                  # CSV data files
└── *.py                       # Python scripts
```

---

## Security Considerations

1. **Package Integrity**: Downloaded packages should be verified on the source system
2. **Transfer Security**: Use secure transfer methods for sensitive environments
3. **System Updates**: Keep the base Python installation updated on target systems
4. **Access Control**: Restrict access to dashboard files and data directories

---

## Performance Notes

- Offline installation is typically faster than online installation
- No network timeouts or connectivity issues
- Consistent package versions across deployments
- Reduced bandwidth usage in production environments

This offline installation method ensures reliable deployment of the meter dashboard in air-gapped or network-restricted environments.
