#!/bin/bash
# Deep Cleanup Script for Simple Meter Dashboard
# Purpose: Remove IoT device files, organize documentation, clean backups
# This server is for API/Web App only - device scripts not needed
# Date: January 6, 2026
# Usage: bash scripts/deep_cleanup.sh

set -e  # Exit on error

echo "==========================================="
echo "Simple Meter Dashboard - DEEP CLEANUP"
echo "==========================================="
echo ""
echo "This script will:"
echo "  1. Move all .md documentation to docs/ folder"
echo "  2. Remove IoT device-specific scripts (keep server essentials)"
echo "  3. Remove packages_folder (offline installation packages)"
echo "  4. Remove mosquitto/ folder (publisher configs not needed)"
echo "  5. Remove all backup files (*.dump, *.tar.gz, *.sql)"
echo "  6. Remove archive/ and legacy/ directories"
echo "  7. Clean Python cache and temp files"
echo ""
echo "⚠️  WARNING: This is an AGGRESSIVE cleanup!"
echo "   Only keep files needed for the Django web application."
echo ""

# Confirm
read -p "Continue with DEEP cleanup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup aborted."
    exit 1
fi

BACKUP_DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="DEEP_CLEANUP_BACKUP_${BACKUP_DATE}"

echo ""
echo "==> Step 1: Creating backup directory..."
mkdir -p "${BACKUP_DIR}"
echo "✓ Created: ${BACKUP_DIR}"

# ============================================================================
# DOCUMENTATION ORGANIZATION
# ============================================================================

echo ""
echo "==> Step 2: Organizing documentation..."

# Create docs folder if it doesn't exist
mkdir -p docs

# Move all .md files from root to docs/
echo "  Moving .md files to docs/..."
MD_COUNT=0
for file in *.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/
        echo "    ✓ Moved: $file → docs/"
        ((MD_COUNT++))
    fi
done

if [ $MD_COUNT -gt 0 ]; then
    echo "✓ Moved $MD_COUNT documentation files to docs/"
else
    echo "  (No .md files found in root)"
fi

# Move specific documentation files if they exist
if [ -f "DASHBOARD_FEATURES.md" ]; then
    mv DASHBOARD_FEATURES.md docs/ 2>/dev/null || true
fi

# ============================================================================
# IOT_SCRIPTS CLEANUP (Keep only server essentials)
# ============================================================================

echo ""
echo "==> Step 3: Cleaning iot_scripts (keeping server essentials)..."

if [ -d "iot_scripts" ]; then
    mkdir -p "${BACKUP_DIR}/iot_scripts"
    
    # List of files to KEEP (used by Django app)
    KEEP_FILES=(
        "config.json"
        "failure_modes.json"
        "mqtt_to_db_ingest.py"
        "offline_rpi_dashboard_db.py"
    )
    
    # Keep alerting/ directory (used by Celery)
    if [ -d "iot_scripts/alerting" ]; then
        echo "  ✓ Keeping: iot_scripts/alerting/ (Celery tasks)"
    fi
    
    # Archive device-specific scripts
    echo "  Archiving device-specific scripts..."
    
    # Move device meter scripts
    for file in iot_scripts/elmeasure_*.py; do
        if [ -f "$file" ]; then
            cp "$file" "${BACKUP_DIR}/iot_scripts/"
            rm "$file"
            echo "    ✓ Removed: $(basename $file) (device script)"
        fi
    done
    
    # Move other device-related files
    DEVICE_FILES=(
        "meter_device.py"
        "meter_manager.py"
        "mosquitto_setup.py"
        "mqtt_client.py"
        "postgre_setup.py"
        "macros.py"
        "venv_utils.py"
        "DB_Setup_README"
        "TEMP_README_ALERT_ARCHITECTURE.md"
    )
    
    for file in "${DEVICE_FILES[@]}"; do
        if [ -f "iot_scripts/$file" ]; then
            cp "iot_scripts/$file" "${BACKUP_DIR}/iot_scripts/"
            rm "iot_scripts/$file"
            echo "    ✓ Removed: $file (device file)"
        fi
    done
    
    # Archive device-specific directories
    if [ -d "iot_scripts/el_meters" ]; then
        cp -r "iot_scripts/el_meters" "${BACKUP_DIR}/iot_scripts/"
        rm -rf "iot_scripts/el_meters"
        echo "    ✓ Removed: el_meters/ (device definitions)"
    fi
    
    if [ -d "iot_scripts/systemd" ]; then
        cp -r "iot_scripts/systemd" "${BACKUP_DIR}/iot_scripts/"
        rm -rf "iot_scripts/systemd"
        echo "    ✓ Removed: systemd/ (device services)"
    fi
    
    if [ -d "iot_scripts/tests" ]; then
        cp -r "iot_scripts/tests" "${BACKUP_DIR}/iot_scripts/"
        rm -rf "iot_scripts/tests"
        echo "    ✓ Removed: tests/ (device tests)"
    fi
    
    if [ -d "iot_scripts/csv_data" ]; then
        cp -r "iot_scripts/csv_data" "${BACKUP_DIR}/iot_scripts/"
        rm -rf "iot_scripts/csv_data"
        echo "    ✓ Removed: csv_data/ (old data)"
    fi
    
    if [ -d "iot_scripts/logs" ]; then
        cp -r "iot_scripts/logs" "${BACKUP_DIR}/iot_scripts/"
        rm -rf "iot_scripts/logs"
        echo "    ✓ Removed: logs/ (old logs)"
    fi
    
    # Remove log files
    if [ -f "iot_scripts/alerts.log" ]; then
        rm "iot_scripts/alerts.log"
        echo "    ✓ Removed: alerts.log"
    fi
    
    echo "✓ iot_scripts cleaned (kept config.json, failure_modes.json, alerting/, ingest scripts)"
else
    echo "  (iot_scripts/ not found)"
fi

# ============================================================================
# PACKAGES_FOLDER REMOVAL
# ============================================================================

echo ""
echo "==> Step 4: Removing packages_folder (offline packages)..."

if [ -d "packages_folder" ]; then
    # Calculate size
    SIZE=$(du -sh packages_folder | cut -f1)
    
    # Move to backup
    mv packages_folder "${BACKUP_DIR}/"
    echo "✓ Removed: packages_folder/ ($SIZE) - offline packages not needed"
else
    echo "  (packages_folder/ not found)"
fi

# ============================================================================
# MOSQUITTO REMOVAL
# ============================================================================

echo ""
echo "==> Step 5: Removing mosquitto/ (publisher configs)..."

if [ -d "mosquitto" ]; then
    mv mosquitto "${BACKUP_DIR}/"
    echo "✓ Removed: mosquitto/ - publisher configs (server uses external broker)"
else
    echo "  (mosquitto/ not found)"
fi

# ============================================================================
# BACKUP FILES CLEANUP
# ============================================================================

echo ""
echo "==> Step 6: Removing old backup files..."

# Database dumps
if ls *.dump 1> /dev/null 2>&1; then
    mkdir -p "${BACKUP_DIR}/old_backups"
    mv *.dump "${BACKUP_DIR}/old_backups/"
    echo "✓ Removed: *.dump files"
fi

# SQL backups
if ls *.sql 1> /dev/null 2>&1; then
    mkdir -p "${BACKUP_DIR}/old_backups"
    mv *.sql "${BACKUP_DIR}/old_backups/" 2>/dev/null || true
    echo "✓ Removed: *.sql files"
fi

# Tar archives
if ls *.tar.gz 1> /dev/null 2>&1; then
    mkdir -p "${BACKUP_DIR}/old_backups"
    mv *.tar.gz "${BACKUP_DIR}/old_backups/"
    echo "✓ Removed: *.tar.gz archives"
fi

# ============================================================================
# LEGACY DIRECTORIES
# ============================================================================

echo ""
echo "==> Step 7: Removing legacy directories..."

if [ -d "archive" ]; then
    mv archive "${BACKUP_DIR}/"
    echo "✓ Removed: archive/"
fi

if [ -d "legacy" ]; then
    mv legacy "${BACKUP_DIR}/"
    echo "✓ Removed: legacy/"
fi

if [ -d "meter_dashboard/archive" ]; then
    mv meter_dashboard/archive "${BACKUP_DIR}/meter_dashboard_archive"
    echo "✓ Removed: meter_dashboard/archive/"
fi

if [ -d "meter_dashboard/quick_improvements" ]; then
    mv meter_dashboard/quick_improvements "${BACKUP_DIR}/quick_improvements"
    echo "✓ Removed: meter_dashboard/quick_improvements/"
fi

# ============================================================================
# TEMPORARY FILES
# ============================================================================

echo ""
echo "==> Step 8: Removing temporary files..."

# Temp Python files
rm -f tmp_*.py 2>/dev/null || true
echo "  ✓ Removed: tmp_*.py"

# Log files
rm -f *.log 2>/dev/null || true
echo "  ✓ Removed: *.log"

# Strange filename
rm -f meter_dashboard/"ql -h"* 2>/dev/null || true

# ============================================================================
# PYTHON CACHE
# ============================================================================

echo ""
echo "==> Step 9: Cleaning Python cache..."

PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
PYC_COUNT=$(find . -type f -name "*.pyc" 2>/dev/null | wc -l)

if [ $PYCACHE_COUNT -gt 0 ] || [ $PYC_COUNT -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    echo "✓ Removed: $PYCACHE_COUNT __pycache__ directories, $PYC_COUNT .pyc files"
else
    echo "  (No Python cache found)"
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "==========================================="
echo "✅ DEEP CLEANUP COMPLETE!"
echo "==========================================="
echo ""
echo "📦 Backup created at: ${BACKUP_DIR}"
echo ""
echo "📊 What was cleaned:"
echo "  ✓ Documentation moved to docs/ folder"
echo "  ✓ IoT device scripts removed from iot_scripts/"
echo "  ✓ packages_folder/ removed (offline packages)"
echo "  ✓ mosquitto/ removed (publisher configs)"
echo "  ✓ Old backups archived (*.dump, *.sql, *.tar.gz)"
echo "  ✓ Legacy directories archived"
echo "  ✓ Temporary files removed"
echo "  ✓ Python cache cleaned"
echo ""
echo "📁 Current structure (server essentials only):"
echo "  meter_dashboard/          # Django web application"
echo "  iot_scripts/              # Server configs only"
echo "    ├── config.json         # Database config"
echo "    ├── failure_modes.json  # Alert thresholds"
echo "    ├── alerting/           # Celery alert tasks"
echo "    ├── mqtt_to_db_ingest.py # Data ingestion"
echo "    └── offline_rpi_dashboard_db.py"
echo "  docs/                     # All documentation"
echo "  scripts/                  # Utility scripts"
echo "  device_config_exports/    # Generated configs"
echo "  docker-compose.yml        # Services"
echo "  .env                      # Environment vars"
echo ""
echo "⚠️  IMPORTANT: Verify application still works!"
echo ""
echo "📋 Next steps:"
echo "  1. Test application:"
echo "     docker-compose down"
echo "     docker-compose build"
echo "     docker-compose up -d"
echo ""
echo "  2. Verify at http://localhost:8000"
echo "     - Meter readings load"
echo "     - Device config works"
echo "     - Alerts function"
echo "     - Grafana connects"
echo ""
echo "  3. If all works, delete backup in 30 days:"
echo "     rm -rf ${BACKUP_DIR}"
echo ""
echo "  4. Commit changes:"
echo "     git add ."
echo "     git commit -m 'Deep cleanup: Organize docs, remove device files'"
echo ""

# Calculate space saved
if [ -d "${BACKUP_DIR}" ]; then
    BACKUP_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
    echo "💾 Space that can be freed: ${BACKUP_SIZE}"
    echo "   (After verifying application works)"
fi

echo ""
echo "✅ Cleanup complete! Your server is now lean and focused."
echo ""
