# Step-by-Step Safe Cleanup Guide

**Date:** January 6, 2026  
**Purpose:** Carefully clean iot_scripts, test after each step

---

## 🎯 What Django App Actually Needs from iot_scripts

### ✅ MUST KEEP (Used by Django):
1. **config.json** - Database configuration (imported in settings.py)
2. **failure_modes.json** - Alert thresholds (imported in views.py, api_views.py)
3. **alerting/** - Celery alert tasks (imported in 4 files)
4. **mqtt_to_db_ingest.py** - Referenced in SSH deployment commands
5. **offline_rpi_dashboard_db.py** - Referenced in SSH deployment commands

### ❌ CAN REMOVE (Device-only scripts):
- elmeasure_*.py (5 files) - Modbus meter drivers for devices
- meter_device.py - Device meter management
- meter_manager.py - Device manager
- mosquitto_setup.py - MQTT broker setup for devices
- mqtt_client.py - MQTT client for devices
- postgre_setup.py - Database setup script for devices
- macros.py - Device macros
- venv_utils.py - Virtual environment utilities
- el_meters/ - Meter definitions
- systemd/ - Systemd service files
- tests/ - Device tests
- csv_data/ - Old CSV data
- logs/ - Old log files
- DB_Setup_README - Device setup docs
- TEMP_README_ALERT_ARCHITECTURE.md - Temp docs
- alerts.log - Old log file
- current_alerts.json - Old alert state (now using Redis)

---

## 📋 Step-by-Step Cleanup Process

Execute these steps ONE AT A TIME, testing after each:

### Step 1: Test Application Before Cleanup
```bash
cd /home/isha/opt/simple-meter-dashboard
docker-compose up -d
# Visit http://localhost:8000
# Verify meter readings, device config, alerts all work
docker-compose down
```

### Step 2: Remove Device Meter Drivers (Safe)
```bash
cd iot_scripts
rm -f elmeasure_*.py
echo "Removed 5 device meter drivers"
```

**Test:**
```bash
cd /home/isha/opt/simple-meter-dashboard
docker-compose up -d
# Check http://localhost:8000 - should still work
docker-compose logs app | grep -i error
```

### Step 3: Remove Device Management Scripts (Safe)
```bash
cd iot_scripts
rm -f meter_device.py meter_manager.py macros.py
echo "Removed device management scripts"
```

**Test:** Same as Step 2

### Step 4: Remove MQTT/Setup Scripts (Safe)
```bash
cd iot_scripts
rm -f mosquitto_setup.py mqtt_client.py postgre_setup.py venv_utils.py
echo "Removed MQTT and setup scripts"
```

**Test:** Same as Step 2

### Step 5: Remove Directories (Safe)
```bash
cd iot_scripts
rm -rf el_meters/ systemd/ tests/ csv_data/ logs/
echo "Removed device directories"
```

**Test:** Same as Step 2

### Step 6: Remove Documentation and Logs (Safe)
```bash
cd iot_scripts
rm -f DB_Setup_README TEMP_README_ALERT_ARCHITECTURE.md alerts.log current_alerts.json
echo "Removed old docs and logs"
```

**Test:** Same as Step 2

### Step 7: Final Verification
```bash
cd iot_scripts
ls -la
# Should only see:
# - alerting/
# - config.json
# - failure_modes.json
# - mqtt_to_db_ingest.py
# - offline_rpi_dashboard_db.py
```

**Full application test:**
```bash
cd /home/isha/opt/simple-meter-dashboard
docker-compose down
docker-compose build
docker-compose up -d

# Test all features:
# 1. http://localhost:8000/meter_readings/latest/
# 2. http://localhost:8000/device-config/
# 3. http://localhost:8000/alerts/
# 4. http://localhost:8000/api/
# 5. http://localhost:3000 (Grafana)
```

---

## 🔍 Files to Keep - Details

### config.json
```json
{
  "DB_SERVER_IP": "192.168.112.106",
  "DB_PORT": 5432,
  "DB_NAME": "mfmdb",
  "DB_USER": "mfmuser",
  "DB_PASSWORD": "devi",
  "MQTT_BROKER": "localhost",
  "MQTT_PORT": 1883
}
```
**Used in:** settings.py line 90-91

### failure_modes.json
```json
{
  "voltage_min": 200,
  "voltage_max": 250,
  "current_max": 100,
  "frequency_min": 49,
  "frequency_max": 51
}
```
**Used in:**
- meter_readings/views.py line 196-198
- meter_dashboard/api_views.py line 11

### alerting/
Contains Celery tasks for alert processing.
**Used in:**
- meter_readings/views.py line 58
- meter_dashboard/celery.py line 17
- meter_dashboard/api_views.py line 43
- meter_dashboard/views.py line 38

### mqtt_to_db_ingest.py
MQTT subscriber that ingests data to database.
**Used in:** ssh_api.py line 93 (SSH deployment commands)

### offline_rpi_dashboard_db.py
Offline dashboard for Raspberry Pi.
**Used in:** ssh_api.py line 96 (SSH deployment commands)

---

## ⚠️ Important Notes

1. **Don't remove mqtt_to_db_ingest.py and offline_rpi_dashboard_db.py** even though they're device scripts - they're referenced in SSH deployment code for remote Raspberry Pis

2. **config.json is critical** - If removed, Django won't start (settings.py will fail)

3. **failure_modes.json is critical** - Alert system depends on it

4. **alerting/ directory is critical** - Celery tasks for real-time alerts

5. **Test after EACH step** - Don't proceed if errors appear

---

## 🚨 If Something Breaks

### Error: "No module named 'iot_scripts.alerting'"
**Cause:** Deleted alerting/ directory  
**Fix:** Restore from backup

### Error: "config.json not found"
**Cause:** Deleted config.json  
**Fix:** Restore from backup

### Error: "failure_modes.json not found"
**Cause:** Deleted failure_modes.json  
**Fix:** Restore from backup

### Application won't start
```bash
# Check logs
docker-compose logs app

# Restore from backup if needed
cp DEEP_CLEANUP_BACKUP_*/iot_scripts/[filename] iot_scripts/
```

---

## ✅ Expected Final State

```
iot_scripts/
├── alerting/                    # ✓ KEEP - Celery alert tasks
│   ├── __init__.py
│   ├── celery_alert_tasks.py
│   └── ...
├── config.json                  # ✓ KEEP - Database config
├── failure_modes.json           # ✓ KEEP - Alert thresholds
├── mqtt_to_db_ingest.py         # ✓ KEEP - Data ingestion (SSH deployment)
└── offline_rpi_dashboard_db.py  # ✓ KEEP - Offline dashboard (SSH deployment)
```

Everything else removed = cleaner codebase!

---

**Ready to proceed?** Follow steps 1-7 in order, testing after each step.
