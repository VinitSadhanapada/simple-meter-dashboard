# Meter Dashboard Features & Setup Guide

---
## 1. Device Configuration Management
- Manage Raspberry Pi devices, meter devices, and system configuration via Django admin.
- Add, edit, activate/deactivate devices and meters.
- View device status, meter count, and last updated info.

**How to Use:**
- Go to Django admin > Device Config > Add/Edit Raspberry Pi or Meter Device.
- Use admin actions to activate/deactivate devices and meters.

---
## 2. SSH Key Setup & Testing
- Set up SSH keys for secure, passwordless Pi access.
- Test SSH connection from admin.
- Regenerate keys if needed.

**How to Use:**
- Select Pis in admin, use "Set up SSH keys" or "Test SSH connections" actions.

---
## 3. OTA Script Deployment (with Perfect Sync)
- Deploy scripts/packages to Raspberry Pi using rsync over SSH.
- Uses `sshpass` for password-based SSH.
- **Perfect sync:** Uses `rsync --delete` to remove obsolete files from Pi.
- Exclude files using a custom exclude file.

**How to Use:**
- Add OTADeployment entry in admin.
- Select and run "Deploy selected OTA scripts to Raspberry Pi" action.
- Status updates: IN_PROGRESS, SUCCESS, FAILED.

---
## 4. Background Task Processing (Celery)
- OTA deployments run as background tasks using Celery.
- Status updates automatically on completion or failure.
- 1-hour timeout for transfer operations to prevent hangs.

**How to Use:**
- Start Redis server and Celery worker.
- Trigger deployment from admin; status updates on refresh.

---
## 5. System Setup & Installation
- Python packages: `celery`, `redis`, `django-encrypted-model-fields`, `fabric`.
- System packages: `sshpass`, `redis-server`.
- All packages can be downloaded for offline use in `/home/isha/deepak/MFM_offline_setup/packages_folder`.

**Setup Steps:**
1. Install Python and system packages.
2. Configure `settings.py` (see CELERY_BROKER_URL, database, etc.).
3. Create and configure `celery.py` and `__init__.py` in main project folder.
4. Start Redis and Celery worker.
5. Use Django admin for all management and deployment actions.

---
## 6. Troubleshooting & Best Practices
- Check Celery and Redis status before deploying.
- Use systemd or supervisor to keep Celery running in production.
- Use admin messages and status fields to monitor deployments.
- For perfect sync, ensure correct source/destination paths and use `--delete` in rsync.

---
## 7. Security & Maintenance
- Use SSH keys for secure Pi access.
- Store sensitive keys in environment variables.
- Regularly update packages and monitor logs.

---
## 8. Additional Features
- Meter model selection with datalist in admin forms.
- Customizable system configuration per Pi.
- Deployment history tracking.

---
## For More Details
- See individual README files in `/docs` folder for Celery, deployment, and setup instructions.
- All admin actions and features are accessible via Django admin interface.
