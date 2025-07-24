# ✅ RPi Service Verification Checklist

## **Pre-Reboot Verification (Do This First)**

### **🔍 Step 1: Service Status Check**
```bash
sudo systemctl is-enabled meter-dashboard
```
**✅ Expected Result:** `enabled`  
**❌ If you see:** `disabled` → Run: `sudo python3 simple_rpi_dashboard.py --create-service`

```bash
sudo systemctl status meter-dashboard
```
**✅ Expected Result:** `Active: active (running)`  
**❌ If you see:** `inactive` or `failed` → Check service logs for errors

### **🔍 Step 2: Dashboard Status Check**
```bash
python3 simple_rpi_dashboard.py --status
```
**✅ Expected Output:**
```
🟢 Service Status: Active (running)
📊 Dashboard running in background mode  
📁 CSV files: csv_files/
📝 Error logs: error_logs/
🔄 Reading interval: 10 seconds
```

**❌ If you see errors:** Check the troubleshooting section

### **🔍 Step 3: CSV File Verification**
```bash
# Check files exist
ls -la csv_files/
```
**✅ Expected:** Files like `Main_Panel_readings.csv`, `Generator_Set_readings.csv`

```bash
# Check recent data
tail -n 3 csv_files/*.csv
```
**✅ Expected:** Timestamps within the last 30 seconds
**❌ If timestamps are old:** Service may not be writing data

### **🔍 Step 4: Document Current State**
```bash
# Note current time (write this down!)
date

# Note service start time
sudo systemctl show meter-dashboard --property=ActiveEnterTimestamp
```

---

## **Post-Reboot Verification (After sudo reboot)**

**⏰ Wait 2-3 minutes after RPi boots, then:**

### **🔍 Step 1: Auto-Start Verification**
```bash
python3 simple_rpi_dashboard.py --status
```
**✅ Expected:** Same output as pre-reboot
**❌ If service not running:** Auto-startup failed

### **🔍 Step 2: New Data Verification**
```bash
tail -n 5 csv_files/*.csv
```
**✅ Expected:** NEW timestamps after your noted reboot time
**❌ If no new data:** Service may have started but not collecting data

### **🔍 Step 3: Boot Sequence Verification**
```bash
# Check service started at boot
sudo journalctl -u meter-dashboard --since "10 minutes ago" | head -20
```
**✅ Expected:** Service start messages after boot time

### **🔍 Step 4: Timing Verification**
```bash
# Check system uptime
uptime

# Check when service started  
sudo systemctl show meter-dashboard --property=ActiveEnterTimestamp
```
**✅ Expected:** Service start time should be close to boot time

---

## **🚨 Common Issues & Solutions**

### **Issue: Service Enabled but Not Running**
```bash
# Check why it failed
sudo journalctl -u meter-dashboard --no-pager
# Look for error messages
```

### **Issue: Service Running but No CSV Data**
```bash
# Check if files are being created
ls -la csv_files/

# Check error logs
cat error_logs/*.log

# Test device configuration
grep -A 5 "DEVICE_CONFIG" simple_rpi_dashboard.py
```

### **Issue: CSV Files Old Timestamps**
```bash
# Check if service is actually collecting data
python3 simple_rpi_dashboard.py --logs

# Restart service manually
python3 simple_rpi_dashboard.py --restart
```

---

## **✅ Success Confirmation**

**Your auto-startup is working correctly when ALL of these are true:**

1. ✅ `sudo systemctl is-enabled meter-dashboard` returns `enabled`
2. ✅ `python3 simple_rpi_dashboard.py --status` shows `Active (running)`
3. ✅ CSV files exist in `csv_files/` directory
4. ✅ CSV files have timestamps within last 30 seconds
5. ✅ After reboot, service automatically starts without manual intervention
6. ✅ After reboot, CSV files show NEW data with post-reboot timestamps
7. ✅ No critical errors in `sudo journalctl -u meter-dashboard`

**🎯 If all 7 items are ✅, your auto-startup is working perfectly!**
