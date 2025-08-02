#!/bin/bash
# This script sets up @reboot cron jobs for offline_rpi_dashboard.py and usb_csv_auto_copy.py
# Usage: sudo bash startup_cron_setup.sh

SCRIPT_DIR="/home/$USER/Desktop/offline_setup"
PYTHON="$(which python3)"
DASHBOARD="$SCRIPT_DIR/offline_rpi_dashboard_debug.py"
USB_COPY="$SCRIPT_DIR/usb_csv_auto_copy.py"

# Remove any previous @reboot lines for these scripts
crontab -l | grep -v "$DASHBOARD --run" | grep -v "$USB_COPY" > /tmp/cron_tmp_$$

# Add new @reboot lines
{
    cat /tmp/cron_tmp_$$
    echo "@reboot $PYTHON $DASHBOARD --run > $SCRIPT_DIR/dashboard_debug.log 2>&1 &"
    echo "@reboot $PYTHON $USB_COPY > $SCRIPT_DIR/usb_copy.log 2>&1 &"
} | crontab -

rm /tmp/cron_tmp_$$

echo "[INFO] Cron jobs set for dashboard and USB copy scripts. They will run on every reboot."
