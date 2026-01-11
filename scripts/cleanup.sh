#!/bin/bash
# Cleanup script for Simple Meter Dashboard
# Purpose: Remove legacy files and organize codebase for handover
# Date: January 6, 2026
# Usage: bash scripts/cleanup.sh

set -e  # Exit on error

echo "========================================="
echo "Simple Meter Dashboard Cleanup Script"
echo "========================================="
echo ""
echo "This script will:"
echo "  1. Archive legacy directories (archive/, legacy/)"
echo "  2. Remove temporary files (*.log, tmp_*.py)"
echo "  3. Clean Python cache (__pycache__, *.pyc)"
echo "  4. Archive old database dumps"
echo "  5. Remove unnecessary files"
echo ""

# Confirm
read -p "Continue with cleanup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup aborted."
    exit 1
fi

BACKUP_DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="CLEANUP_BACKUP_${BACKUP_DATE}"

echo ""
echo "Step 1: Creating backup directory..."
mkdir -p "${BACKUP_DIR}"
echo "✓ Created: ${BACKUP_DIR}"

# Archive legacy directories
echo ""
echo "Step 2: Archiving legacy directories..."

if [ -d "archive" ]; then
    mv archive "${BACKUP_DIR}/archive"
    echo "✓ Moved: archive/ → ${BACKUP_DIR}/archive/"
else
    echo "  (archive/ not found, skipping)"
fi

if [ -d "legacy" ]; then
    mv legacy "${BACKUP_DIR}/legacy"
    echo "✓ Moved: legacy/ → ${BACKUP_DIR}/legacy/"
else
    echo "  (legacy/ not found, skipping)"
fi

if [ -d "meter_dashboard/archive" ]; then
    mv meter_dashboard/archive "${BACKUP_DIR}/meter_dashboard_archive"
    echo "✓ Moved: meter_dashboard/archive/ → ${BACKUP_DIR}/meter_dashboard_archive/"
else
    echo "  (meter_dashboard/archive/ not found, skipping)"
fi

if [ -d "meter_dashboard/quick_improvements" ]; then
    mv meter_dashboard/quick_improvements "${BACKUP_DIR}/quick_improvements"
    echo "✓ Moved: meter_dashboard/quick_improvements/ → ${BACKUP_DIR}/quick_improvements/"
else
    echo "  (meter_dashboard/quick_improvements/ not found, skipping)"
fi

# Remove temporary files
echo ""
echo "Step 3: Removing temporary files..."

TEMP_FILES=(
    "tmp_explain.py"
    "tmp_time.py"
    "dashboard_debug.log"
    "usb_copy.log"
)

for file in "${TEMP_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "✓ Removed: $file"
    fi
done

# Remove strange filename in meter_dashboard
if [ -f "meter_dashboard/ql -h 192.168.112.106 -U mfmuser -d mfmdb -c SELECT * FROM device_config_raspberrypi ORDER BY id;" ]; then
    rm -f meter_dashboard/"ql -h"*
    echo "✓ Removed: strange ql command file"
fi

# Archive old database backups
echo ""
echo "Step 4: Archiving old database dumps..."
echo "⚠️  WARNING: You should create a fresh backup first!"
read -p "Have you created a fresh database backup? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "${BACKUP_DIR}/old_dumps"
    
    # Move old dumps
    if ls meter_readings_backup_*.dump 1> /dev/null 2>&1; then
        mv meter_readings_backup_*.dump "${BACKUP_DIR}/old_dumps/" 2>/dev/null || true
        echo "✓ Moved: meter_readings_backup_*.dump"
    fi
    
    # Move old tar archives
    if ls *.tar.gz 1> /dev/null 2>&1; then
        mv *.tar.gz "${BACKUP_DIR}/old_dumps/" 2>/dev/null || true
        echo "✓ Moved: *.tar.gz archives"
    fi
else
    echo "⚠️  Skipping database dump cleanup (create backup first!)"
fi

# Clean Python cache
echo ""
echo "Step 5: Cleaning Python cache..."

# Count before cleanup
PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
PYC_COUNT=$(find . -type f -name "*.pyc" 2>/dev/null | wc -l)

if [ $PYCACHE_COUNT -gt 0 ] || [ $PYC_COUNT -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    echo "✓ Removed: $PYCACHE_COUNT __pycache__ directories"
    echo "✓ Removed: $PYC_COUNT *.pyc files"
else
    echo "  (No Python cache found)"
fi

# Summary
echo ""
echo "========================================="
echo "✅ Cleanup Complete!"
echo "========================================="
echo ""
echo "📦 Backup created at: ${BACKUP_DIR}"
echo ""
echo "📋 Next steps:"
echo "  1. Review ${BACKUP_DIR} to ensure nothing important was removed"
echo "  2. Test application:"
echo "     docker-compose down"
echo "     docker-compose build"
echo "     docker-compose up"
echo "  3. Verify all features work at http://localhost:8000"
echo "  4. If all works, you can delete ${BACKUP_DIR} in 30 days"
echo "  5. Commit changes:"
echo "     git add ."
echo "     git commit -m 'Clean up legacy files and organize codebase'"
echo ""
echo "📊 Estimated space saved: Check with 'du -sh ${BACKUP_DIR}'"
echo ""
