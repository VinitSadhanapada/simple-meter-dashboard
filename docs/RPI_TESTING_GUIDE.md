# 🍓 Raspberry Pi Auto-Startup Testing Guide

## 📋 **Step-by-Step Setup Order**

### **🔐 Sudo Requirements Explained**

**NO SUDO NEEDED:**
- Environment setup, package installation, running dashboard
- Commands: `--setup`, `--run`, `--status`, `--logs`, `--start`, `--stop`, `--restart`

**SUDO REQUIRED:**
- Creating systemd service files (writes to `/etc/systemd/system/`)
- Commands: `--create-service`, `--install`, `--uninstall`

### **Phase 1: Initial Setup (No Sudo Required)**
```bash
# 1. Transfer files to RPi
# Copy all project files to RPi (e.g., via scp, git clone, or USB)

# 2. Navigate to project directory
cd /path/to/your/project/first_deployv2/

# 3. Setup environment and dependencies (NO SUDO NEEDED)
python3 simple_rpi_dashboard.py --setup
```

**What this does:**
- ✅ Creates Python virtual environment
- ✅ Installs all required packages from requirements.txt
- ✅ Creates necessary directories (csv_files/, error_logs/)
- ✅ Sets up proper permissions
- ✅ **No sudo required for this step!**

### **Phase 2: Service Installation (SUDO REQUIRED - One Time Only)**
```bash
# 4. Create auto-startup service (REQUIRES SUDO)
sudo python3 simple_rpi_dashboard.py --create-service
```

**What this does:**
- ✅ Creates systemd service file (`/etc/systemd/system/meter-dashboard.service`)
- ✅ Enables service to start on boot
- ✅ Starts service immediately
- ⚠️ **Requires sudo because it writes to /etc/systemd/system/**

### **Alternative: One-Command Install (SUDO REQUIRED)**
```bash
# Quick install: setup + service creation in one command (REQUIRES SUDO)
sudo python3 simple_rpi_dashboard.py --install
```

**Note:** The `--install` command requires sudo because it includes the `--create-service` step.

### **🎯 Recommended Approach**

**Use the Two-Phase Method** for better control and troubleshooting:

1. **Phase 1 first** - lets you verify environment setup works
2. **Test manually** - run `python3 simple_rpi_dashboard.py --run` to verify functionality  
3. **Phase 2 second** - only create service after confirming everything works

**Use One-Command Install** only if you're confident and want convenience over safety.

---

## � **Complete Testing Timeline**

### **Setup Phase (Do This First)**
1. **Phase 1:** `python3 simple_rpi_dashboard.py --setup`
2. **Manual Test:** `python3 simple_rpi_dashboard.py --run` (optional but recommended)
3. **Phase 2:** `sudo python3 simple_rpi_dashboard.py --create-service`
4. **Verify Service:** `python3 simple_rpi_dashboard.py --status`

### **Reboot Test Phase (Do This After Setup)**
5. **Pre-reboot checks** (document current state)
6. **Perform reboot** (`sudo reboot`)
7. **Post-reboot verification** (check auto-startup worked)

**🎯 Key Point:** Only do the reboot test AFTER the service is created and running successfully.

---

## �🔍 **Verification Steps After Setup**

### **1. Check Service Status**
```bash
# Check if service is running
python3 simple_rpi_dashboard.py --status

# Alternative systemd command
sudo systemctl status meter-dashboard
```

**✅ Expected Output:**
```
🟢 Service Status: Active (running)
📊 Dashboard running in background mode
📁 CSV files: csv_files/
📝 Error logs: error_logs/
🔄 Reading interval: 10 seconds
```

### **2. Check Log Files**
```bash
# View recent service logs
python3 simple_rpi_dashboard.py --logs

# View real-time logs
sudo journalctl -u meter-dashboard -f

# Check CSV output files
ls -la csv_files/
tail csv_files/*.csv
```

### **3. Verify File Creation**
```bash
# Check that CSV files are being created
ls -la csv_files/
# Should see files like: Main_Panel_readings.csv, Generator_Set_readings.csv

# Check for recent data
tail -n 5 csv_files/*.csv
# Should show recent timestamps and data
```

---

## 🔄 **Reboot Testing Procedure**

**⚠️ IMPORTANT: Only perform reboot test AFTER service is created and running!**

**Prerequisites:**
- ✅ Phase 1 completed (`--setup`)
- ✅ Phase 2 completed (`--create-service`)  
- ✅ Service status shows "Active (running)"
- ✅ CSV files are being created with recent timestamps

### **Before Reboot - Pre-Check**

**These checks confirm the service is working properly BEFORE you reboot:**

```bash
# 1. Verify service is running and enabled for boot
sudo systemctl is-enabled meter-dashboard
# ✅ Expected: "enabled"

sudo systemctl status meter-dashboard
# ✅ Expected: "Active: active (running)"

# 2. Check service has been running and creating data
python3 simple_rpi_dashboard.py --status
# ✅ Expected: "🟢 Service Status: Active (running)"

# 3. Verify CSV files exist and have recent data
ls -la csv_files/
# ✅ Expected: Files like Main_Panel_readings.csv with recent timestamps

tail -n 3 csv_files/*.csv
# ✅ Expected: Recent timestamps (within last 30 seconds)

# 4. Document current time for comparison after reboot
date
# Write down this time - you'll check for data AFTER this time post-reboot

# 5. Check how long service has been running
sudo systemctl show meter-dashboard --property=ActiveEnterTimestamp
# Note this time - service should restart after reboot
```

**🎯 What You're Looking For:**
- Service status: "enabled" and "active (running)"
- CSV files with data timestamps from the last minute
- No error messages in status output

### **Perform Reboot**
```bash
sudo reboot
```

### **After Reboot - Verification**
**Wait 2-3 minutes after RPi boots up, then:**

```bash
# 1. Check service started automatically (most important!)
python3 simple_rpi_dashboard.py --status
# ✅ Expected: "🟢 Service Status: Active (running)"

# 2. Verify service auto-started at boot
sudo journalctl -u meter-dashboard --since "5 minutes ago" | grep -i "started"
# ✅ Expected: Log entry showing service started after boot

# 3. Check for NEW CSV entries created after reboot
tail -n 5 csv_files/*.csv
# ✅ Expected: Timestamps NEWER than the time you noted before reboot

# 4. Verify service uptime vs system uptime
uptime
# Shows how long system has been up

sudo systemctl show meter-dashboard --property=ActiveEnterTimestamp
# Shows when service started - should be AFTER boot time

# 5. Quick health check
ls -la csv_files/  # Files should be growing in size
wc -l csv_files/*.csv  # Line count should be increasing
```

**🎯 Success Criteria:**
- Service status shows "Active (running)" 
- CSV files contain data with timestamps AFTER your reboot
- Service started automatically without manual intervention
- No error messages in logs

---

## ✅ **Success Indicators**

### **Service is Working Correctly When:**
1. **Service Status:** `Active (running)` 
2. **CSV Files:** New entries every 10 seconds (or your configured interval)
3. **Timestamps:** Recent timestamps in CSV files
4. **No Errors:** Clean service logs without critical errors
5. **Auto-Start:** Service automatically starts after reboot

### **Sample Successful Output:**
```bash
pi@raspberrypi:~/first_deployv2 $ python3 simple_rpi_dashboard.py --status
🟢 Service Status: Active (running)
📊 Dashboard running in background mode
📁 CSV files: csv_files/
📝 Error logs: error_logs/
🔄 Reading interval: 10 seconds
💾 Latest CSV entries:
   Main_Panel_readings.csv: 2025-01-21 15:30:45
   Generator_Set_readings.csv: 2025-01-21 15:30:45
   UPS_System_readings.csv: 2025-01-21 15:30:45
```

---

## 🚨 **Troubleshooting Common Issues**

### **Service Not Starting**
```bash
# Check service logs for errors
sudo journalctl -u meter-dashboard --no-pager

# Check if service file exists
ls -la /etc/systemd/system/meter-dashboard.service

# Reload systemd and restart
sudo systemctl daemon-reload
sudo systemctl restart meter-dashboard
```

### **Virtual Environment Issues**
```bash
# Check if venv exists
ls -la meter_dashboard_venv/

# Re-run setup if needed
python3 simple_rpi_dashboard.py --setup
```

### **Permission Issues**
```bash
# Check file permissions
ls -la csv_files/ error_logs/

# Fix permissions if needed
chmod 755 csv_files/ error_logs/
chmod 644 csv_files/*.csv error_logs/*.log
```

### **CSV Files Not Created**
```bash
# Check device configuration
grep -A 10 "DEVICE_CONFIG" simple_rpi_dashboard.py

# Check error logs
cat error_logs/*.log

# Test in simulation mode
python3 simple_rpi_dashboard.py --run --simulation
```

---

## 🎯 **Quick Verification Commands**

```bash
# All-in-one status check
echo "=== Service Status ===" && \
python3 simple_rpi_dashboard.py --status && \
echo -e "\n=== Recent CSV Data ===" && \
tail -n 2 csv_files/*.csv && \
echo -e "\n=== Service Uptime ===" && \
sudo systemctl show meter-dashboard --property=ActiveEnterTimestamp
```

---

## 📱 **Remote Monitoring**

### **SSH Access for Remote Checking**
```bash
# Connect via SSH
ssh pi@your-rpi-ip

# Quick status check
python3 ~/first_deployv2/simple_rpi_dashboard.py --status

# Download CSV files for analysis
scp pi@your-rpi-ip:~/first_deployv2/csv_files/*.csv .
```

### **Service Control Commands**
```bash
# Start service manually
python3 simple_rpi_dashboard.py --start

# Stop service
python3 simple_rpi_dashboard.py --stop

# Restart service
python3 simple_rpi_dashboard.py --restart

# View real-time logs
python3 simple_rpi_dashboard.py --logs
```

---

## 🔧 **Service Management**

### **Remove Auto-Startup** (if needed)
```bash
# Uninstall the service
python3 simple_rpi_dashboard.py --uninstall
```

### **Update Service** (after code changes)
```bash
# Stop service, update code, restart
python3 simple_rpi_dashboard.py --stop
# ... make your code changes ...
python3 simple_rpi_dashboard.py --start
```

---

## 📊 **Expected File Structure After Setup**

```
first_deployv2/
├── simple_rpi_dashboard.py          # Main script
├── meter_device.py                  # Device communication
├── requirements.txt                 # Dependencies
├── meter_dashboard_venv/            # Virtual environment
├── csv_files/                       # CSV output files
│   ├── Main_Panel_readings.csv
│   ├── Generator_Set_readings.csv
│   └── UPS_System_readings.csv
├── error_logs/                      # Error log files
│   └── dashboard_errors.log
└── docs/                           # Documentation
```

---

**🎯 Summary:** Follow the setup order, verify after each step, and use the reboot test to confirm auto-startup works. The service should start automatically and begin logging data within 2-3 minutes of boot.
