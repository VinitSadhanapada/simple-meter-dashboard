# File Cleanup Guide - Legacy and Unnecessary Files

**Project:** Simple Meter Dashboard  
**Purpose:** Identify files safe to remove for cleaner handover  
**Date:** January 6, 2026

---

## 📂 DIRECTORIES TO REVIEW/REMOVE

### 1. **`/archive/`** - Old debug and migration scripts
**Status:** ⚠️ CAN BE REMOVED (after verification)

**Contents:**
- `add_missing_functions.py` - Old migration script
- `admin_30_08.py` - Legacy admin backup
- `api_improvements.py` - Superseded by current API
- `check_*.py` - Multiple debug scripts
- `csv_*.py` - CSV utilities (may want to keep)
- `database_*.sql` - Old SQL scripts
- `fix_*.py` - Migration scripts (completed)
- `models_30_08.py`, `signals_30_08.py` - Old model backups
- `test_*.py` - Test scripts (can move to test_scripts/)
- `vinit_sep29/` - Old backup directory
- **`logs/`** subdirectory - Old log files

**Action:**
```bash
# Review first, then:
mv archive/ archive_BACKUP_2026-01-06/
# Or delete if confirmed not needed:
# rm -rf archive/
```

**Keep these if needed:**
- `csv_analysis_tool.py` - If CSV analysis is still used
- `csv_formatter.py` - If CSV formatting is still used  
- `current_environment.txt` - Environment documentation

---

### 2. **`/legacy/`** - Old implementation files
**Status:** ⚠️ CAN BE REMOVED

**Contents:**
- `99runinstallscript` - Old install script
- `DB_readings.py` - Superseded by Django ORM
- `check_and_install_ensure_pip_and_python.env.py` - Old setup
- `live_console_monitor.py` - Superseded by web dashboard
- `rtc_new.py` - Old RTC implementation
- `startup_cron_setup.sh` - Old startup script
- `usb_csv_auto_copy.py` - Old USB copy utility
- `scp/` - Old SCP scripts

**Action:**
```bash
mv legacy/ legacy_BACKUP_2026-01-06/
# Or delete:
# rm -rf legacy/
```

---

### 3. **`/meter_dashboard/archive/`** - Django app old files
**Status:** ⚠️ CAN BE REMOVED

Located in: `/meter_dashboard/archive/`

**Action:**
```bash
cd meter_dashboard
mv archive/ archive_BACKUP_2026-01-06/
```

---

### 4. **`/meter_dashboard/quick_improvements/`**
**Status:** ⚠️ REVIEW - May contain useful scripts

**Action:**
- Review contents first
- Move to `/docs/` if documentation
- Move to `/scripts/` if utility scripts
- Delete if obsolete

---

### 5. **Old Backup Files**
**Status:** ❌ DELETE (after creating fresh backup)

**Files:**
- `meter_readings_backup_20251222T104300Z.dump`
- `meter_readings_backup_20251222T104307Z.dump`
- `meter_readings_backup_20251222T104338Z.dump`
- `meter_readings_backup_20251222T104340Z.dump`
- `archive/mfmdb_backup.sql`
- `session-updates-20251120-alerts-config.tar.gz`
- `updated-session-files-20251120.tar.gz`

**Action:**
```bash
# Create fresh backup first:
pg_dump -h 192.168.112.106 -U mfmuser -d mfmdb > backup_FINAL_2026-01-06.sql

# Then remove old backups:
rm -f meter_readings_backup_*.dump
rm -f *.tar.gz
```

---

### 6. **Temporary/Debug Files**
**Status:** ❌ DELETE

**Files:**
- `tmp_explain.py`
- `tmp_time.py`
- `dashboard_debug.log`
- `usb_copy.log`
- `meter_dashboard/db.sqlite3` (if using PostgreSQL)
- `meter_dashboard/ql -h 192.168.112.106 -U mfmuser -d mfmdb -c SELECT * FROM device_config_raspberrypi ORDER BY id;` (strange filename)

**Action:**
```bash
rm -f tmp_*.py
rm -f *.log
rm -f meter_dashboard/db.sqlite3
rm -f meter_dashboard/"ql -h"*
```

---

### 7. **Git Artifacts**
**Status:** ✅ KEEP (but verify .gitignore)

**Files:**
- `.git/` - Version control (KEEP)
- `.gitignore` - Ignore rules (KEEP)

**Action:**
Verify `.gitignore` is comprehensive (see DEPLOYMENT_SECURITY_CHECKLIST.md)

---

### 8. **Python Cache**
**Status:** ❌ DELETE (regenerates automatically)

**Directories:**
- `__pycache__/` - All instances
- `*.pyc` - Compiled Python files

**Action:**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

---

### 9. **Virtual Environment**
**Status:** ⚠️ EXCLUDE FROM VERSION CONTROL

**Directory:**
- `.venv/` or `venv/`

**Action:**
- Keep locally for development
- Ensure in `.gitignore`
- Don't include in production deployment (use Docker)

---

### 10. **Device Config Exports**
**Status:** ⚠️ REVIEW - May contain sensitive data

**Directory:**
- `device_config_exports/`

**Action:**
- Review for sensitive information
- Consider encrypting or restricting access
- Ensure in `.gitignore` if contains secrets
- Keep directory structure but exclude from version control

---

## 📋 ORGANIZED CLEANUP SCRIPT

Create this as `/scripts/cleanup.sh`:

```bash
#!/bin/bash
# Cleanup script for Simple Meter Dashboard
# Run with: bash scripts/cleanup.sh

set -e  # Exit on error

echo "========================================="
echo "Simple Meter Dashboard Cleanup Script"
echo "========================================="
echo ""

# Confirm
read -p "This will archive/delete legacy files. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

BACKUP_DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="CLEANUP_BACKUP_${BACKUP_DATE}"

echo "Creating backup directory: ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# 1. Archive old directories
echo "Archiving legacy directories..."
[ -d "archive" ] && mv archive "${BACKUP_DIR}/archive"
[ -d "legacy" ] && mv legacy "${BACKUP_DIR}/legacy"
[ -d "meter_dashboard/archive" ] && mv meter_dashboard/archive "${BACKUP_DIR}/meter_dashboard_archive"

# 2. Remove temp files
echo "Removing temporary files..."
rm -f tmp_*.py
rm -f dashboard_debug.log
rm -f usb_copy.log

# 3. Remove old database backups (AFTER creating new backup)
echo "WARNING: About to delete old database dumps"
read -p "Have you created a fresh backup? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Moving old dumps to backup..."
    mkdir -p "${BACKUP_DIR}/old_dumps"
    mv -f meter_readings_backup_*.dump "${BACKUP_DIR}/old_dumps/" 2>/dev/null || true
    mv -f *.tar.gz "${BACKUP_DIR}/old_dumps/" 2>/dev/null || true
fi

# 4. Clean Python cache
echo "Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# 5. Remove strange filename
echo "Removing strange filenames..."
cd meter_dashboard 2>/dev/null || true
rm -f "ql -h"* 2>/dev/null || true
cd ..

echo ""
echo "========================================="
echo "Cleanup Complete!"
echo "========================================="
echo "Backup created at: ${BACKUP_DIR}"
echo ""
echo "Next steps:"
echo "1. Review ${BACKUP_DIR} to ensure nothing important was removed"
echo "2. Test application: docker-compose up"
echo "3. If all works, delete ${BACKUP_DIR} in 30 days"
echo "4. Commit changes: git add . && git commit -m 'Clean up legacy files'"
echo ""
```

---

## 🗂️ RECOMMENDED FINAL STRUCTURE

After cleanup, your structure should look like:

```
simple-meter-dashboard/
├── .env                          # Environment config (NOT in git)
├── .env.example                  # Template (IN git)
├── .gitignore                    # Git ignore rules
├── docker-compose.yml            # Development
├── docker-compose.prod.yml       # Production (to create)
├── Dockerfile                    # Container definition
├── requirements.txt              # Python dependencies
├── manage.py                     # Django management
│
├── PROJECT_OVERVIEW.md           # ✨ NEW - Complete documentation
├── DEPLOYMENT_SECURITY_CHECKLIST.md  # ✨ NEW - Security guide
├── FILE_CLEANUP_GUIDE.md         # ✨ NEW - This file
├── README.md                     # User-facing docs
│
├── meter_dashboard/              # Django project
│   ├── meter_dashboard/          # Settings & core
│   ├── meter_readings/           # Meter data app
│   ├── device_config/            # Device mgmt app
│   ├── meters/                   # Meter models app
│   ├── alerts/                   # Alert system app
│   ├── templates/                # Shared templates
│   ├── static/                   # Static files
│   └── requirements.txt          # App-specific deps
│
├── iot_scripts/                  # IoT configurations
│   ├── config.json               # DB & MQTT config
│   └── failure_modes.json        # Alert thresholds
│
├── device_config_exports/        # Auto-generated configs
├── staticfiles/                  # Collected static (generated)
│
├── docs/                         # Documentation
│   ├── MANUAL_SETUP.md
│   ├── DEVICE_CONFIG.md
│   └── OFFLINE_INSTALLATION.md
│
├── scripts/                      # Utility scripts
│   ├── cleanup.sh                # Cleanup script
│   └── backup.sh                 # Backup script (to create)
│
└── test_scripts/                 # Testing utilities
```

---

## ⚠️ FILES TO DEFINITELY KEEP

### Configuration
- ✅ `.env` (but NOT in git)
- ✅ `.env.example` (template)
- ✅ `.gitignore`
- ✅ `docker-compose.yml`
- ✅ `Dockerfile`
- ✅ `requirements.txt`
- ✅ `iot_scripts/config.json` (but NOT in git)
- ✅ `iot_scripts/failure_modes.json`

### Application Code
- ✅ All files in `meter_dashboard/` (except archives)
- ✅ All Django app directories
- ✅ All templates and static files

### Documentation
- ✅ `README.md`
- ✅ `PROJECT_OVERVIEW.md`
- ✅ `DEPLOYMENT_SECURITY_CHECKLIST.md`
- ✅ All files in `docs/`

### Deployment
- ✅ `README_DEPLOY_USB.md`
- ✅ `README_UBUNTU_HOST_SETUP.md`

---

## 🎯 EXECUTION PLAN

### Phase 1: Backup (CRITICAL)
```bash
# 1. Create full backup
pg_dump -h 192.168.112.106 -U mfmuser -d mfmdb > FINAL_BACKUP_$(date +%Y%m%d).sql

# 2. Create git snapshot
git add .
git commit -m "Pre-cleanup snapshot - $(date +%Y-%m-%d)"
git tag pre-cleanup-snapshot

# 3. Create filesystem backup
tar -czf ../simple-meter-dashboard-BACKUP-$(date +%Y%m%d).tar.gz .
```

### Phase 2: Cleanup
```bash
# Create and run cleanup script
chmod +x scripts/cleanup.sh
bash scripts/cleanup.sh
```

### Phase 3: Test
```bash
# Test application still works
docker-compose down
docker-compose build
docker-compose up

# Access http://localhost:8000
# Verify all features work
```

### Phase 4: Commit
```bash
# If all tests pass
git add .
git commit -m "Clean up legacy and temporary files"
git tag cleanup-complete
```

---

## 📊 SIZE ESTIMATES

**Before cleanup:** ~2-3 GB (including .venv, logs, backups)  
**After cleanup:** ~500 MB (excluding .venv)  
**Production deployment:** ~200 MB (Docker image)

---

## ✅ POST-CLEANUP VERIFICATION

After running cleanup, verify:

- [ ] Application starts: `docker-compose up`
- [ ] Web interface loads: http://localhost:8000
- [ ] Meter readings display correctly
- [ ] Device config page works
- [ ] Grafana loads: http://localhost:3000
- [ ] API endpoints respond: http://localhost:8000/api/
- [ ] No import errors in logs
- [ ] All tests pass: `python manage.py test`

---

## 🔄 MAINTENANCE

### Monthly:
- Remove old log files
- Clear temporary files
- Update dependencies

### Quarterly:
- Review and archive old device_config_exports
- Clean Docker images: `docker system prune`
- Review and update documentation

---

**Last Updated:** January 6, 2026  
**Created By:** Cleanup preparation for IT handover  
**Next Review:** After cleanup execution
