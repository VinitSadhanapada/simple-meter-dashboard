# 🚀 RPi Auto-Startup Quick Reference

## **🔐 Sudo Requirements**
- **NO SUDO:** `--setup`, `--run`, `--status`, `--logs`, `--start`, `--stop`, `--restart`
- **SUDO REQUIRED:** `--create-service`, `--install`, `--uninstall`

## **Setup Order (First Time)**

### **🎯 Recommended: Two-Phase Method**
```bash
# 1. Setup environment (NO sudo needed)
python3 simple_rpi_dashboard.py --setup

# 2. Test manually (optional but recommended)
python3 simple_rpi_dashboard.py --run

# 3. Create service (REQUIRES sudo)
sudo python3 simple_rpi_dashboard.py --create-service
```

### **Alternative: One-Command (Less Safe)**
```bash
# One command install (REQUIRES sudo)
sudo python3 simple_rpi_dashboard.py --install
```

## **Verification Commands**
```bash
# Check if working
python3 simple_rpi_dashboard.py --status

# View logs
python3 simple_rpi_dashboard.py --logs

# Check CSV files
ls -la csv_files/ && tail csv_files/*.csv
```

## **After Reboot Check**
```bash
# ONLY do this AFTER service is created and running!
# Wait 2-3 minutes after reboot, then:
python3 simple_rpi_dashboard.py --status
tail -n 3 csv_files/*.csv  # Look for new timestamps
```

## **Service Control**
```bash
python3 simple_rpi_dashboard.py --start    # Start
python3 simple_rpi_dashboard.py --stop     # Stop  
python3 simple_rpi_dashboard.py --restart  # Restart
python3 simple_rpi_dashboard.py --uninstall # Remove
```

## **Success Indicators**
- ✅ Status shows "Active (running)"
- ✅ CSV files have recent timestamps  
- ✅ Service starts automatically after reboot
- ✅ New data appears every 10 seconds

## **Troubleshooting**
```bash
# Service issues
sudo journalctl -u meter-dashboard --no-pager

# Re-setup if needed
python3 simple_rpi_dashboard.py --setup

# Fix permissions
chmod 755 csv_files/ error_logs/
```
