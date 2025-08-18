#!/usr/bin/env python3
"""
Fix method calls in main script to use correct MeterDevice methods
"""


def fix_method_calls():
    """Fix read_parameters() calls to read_data() in main script"""

    script_path = '/home/isha/deepak/MFM_offline_setup/offline_rpi_dashboard_db.py'

    try:
        with open(script_path, 'r') as f:
            content = f.read()

        # Replace read_parameters with read_data
        updated_content = content.replace('read_parameters', 'read_data')

        # Also fix any meter_data field mapping issues
        # The simulation mode generates data in list format, we need to map it to dictionary

        with open(script_path, 'w') as f:
            f.write(updated_content)

        print("✅ Fixed method calls")
        print("🔧 Changed read_parameters() to read_data()")

        return True

    except Exception as e:
        print(f"❌ Error fixing method calls: {e}")
        return False


if __name__ == "__main__":
    fix_method_calls()
