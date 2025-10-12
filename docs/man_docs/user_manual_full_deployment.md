# Meter Dashboard User Manual: Complete Site Deployment

---
## 1. Raspberry Pi OS Installation & First Boot
- Download Raspberry Pi OS and flash to SD card using Raspberry Pi Imager.
- Insert SD card, power on Pi.
- On first boot, set username to `pi` and password to `devi`.
- Connect Pi to network (Ethernet or WiFi).
- Note Pi's IP address (use `hostname -I` or check router).

---
## 2. Network & SSH Setup
- Ensure Pi is reachable from your server (ping Pi's IP).
- Enable SSH on Pi (`sudo raspi-config` > Interface Options > SSH > Enable).
- Test SSH from server:
  ```bash
  ssh pi@<pi_ip>
  # Password: devi
  ```

---
## 3. Register Devices in Django Admin
- Log in to Django admin on your server.
- Go to Device Config > Raspberry Pi > Add new Pi:
  - Enter Pi name, IP, username (`pi`), password (`devi`), SSH port (default 22).
- Add Meter Devices and assign to Pi.

---
## 4. SSH Key Setup (Recommended)
- In Django admin, select Pi(s) and use "Set up SSH keys" action.
- This will copy your server's public key to Pi for passwordless access.
- Test SSH connection using "Test SSH connections" action.

---
## 5. OTA Deployment
- Go to OTADeployment in Django admin.
- Add new OTADeployment:
  - Select Pi, set source_dir (local folder to deploy), exclude_file (optional), status.
- Select the entry and run "Deploy selected OTA scripts to Raspberry Pi" action.
- Deployment runs in background (Celery). Status updates to IN_PROGRESS, then SUCCESS/FAILED.
- Refresh admin to see completed status and timestamp.

---
## 6. Troubleshooting
- If deployment fails, check:
  - Pi is powered on and reachable.
  - SSH credentials are correct.
  - Celery worker and Redis server are running.
  - Server has `sshpass` and `rsync` installed.
- For file sync issues, ensure correct source/destination paths and use `--delete` for perfect sync.
- Use admin messages and status fields for feedback.

---
## 7. Maintenance & Best Practices
- Use SSH keys for secure, automated access.
- Keep Pi and server software updated.
- Regularly check deployment status and logs.
- Store sensitive info in environment variables.

---
## 8. Quick Reference
- Pi username: `pi`, password: `devi`
- Default SSH port: 22
- Django admin: http://<server_ip>:8000/admin/
- Celery worker: `celery -A meter_dashboard worker --loglevel=info`
- Redis server: `sudo systemctl start redis-server`

---
## 9. Support
- For advanced troubleshooting, see FAQ in docs folder.
- Contact system administrator for network or hardware issues.

---
