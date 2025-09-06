# SSH Deployment Troubleshooting Guide

## If you don't see the deployment buttons:

### 1. Clear browser cache and refresh
```bash
Ctrl+F5 (or Cmd+Shift+R on Mac)
```

### 2. Check if template was updated
```bash
cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
python3 manage.py collectstatic --noinput
```

### 3. Restart Django server
```bash
cd /home/isha/deepak/MFM_offline_setup/meter_dashboard
python3 manage.py runserver 0.0.0.0:8000
```

### 4. Check browser console for errors
- Press F12 -> Console tab
- Look for any JavaScript errors

## If deployment fails:

### 1. Install paramiko
```bash
pip install paramiko
```

### 2. Check SSH connectivity manually
```bash
ssh pi@192.168.1.100
```

### 3. Verify Pi credentials in device config

### 4. Check firewall settings on Pi

## Expected deployment process:
1. Click "Test SSH" -> Should show connection details
2. Click "Deploy Config" -> Should show success message
3. Check Pi: `/home/pi/MFM_offline_setup/device_config.json` should exist
