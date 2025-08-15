#!/usr/bin/env python3
"""
Update database schema to accommodate encrypted data
"""
from django.db import connection
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/isha/deepak/MFM_offline_setup/meter_dashboard')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')
django.setup()


def update_field_sizes():
    """Update field sizes to accommodate encrypted data"""
    print("🔧 Updating database schema for encrypted fields...")

    with connection.cursor() as cursor:
        # Check current field sizes
        cursor.execute("""
            SELECT column_name, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'dcms_pi_setup' 
            AND column_name IN ('ssh_password', 'ssh_key_path')
        """)

        current_sizes = dict(cursor.fetchall())
        print(f"📏 Current field sizes: {current_sizes}")

        # Update ssh_password field to accommodate encrypted data
        print("🔐 Updating ssh_password field size...")
        cursor.execute(
            "ALTER TABLE dcms_pi_setup ALTER COLUMN ssh_password TYPE VARCHAR(500);")

        # Update ssh_key_path field to accommodate encrypted data
        print("🔑 Updating ssh_key_path field size...")
        cursor.execute(
            "ALTER TABLE dcms_pi_setup ALTER COLUMN ssh_key_path TYPE VARCHAR(500);")

        # Verify changes
        cursor.execute("""
            SELECT column_name, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'dcms_pi_setup' 
            AND column_name IN ('ssh_password', 'ssh_key_path')
        """)

        new_sizes = dict(cursor.fetchall())
        print(f"✅ Updated field sizes: {new_sizes}")

        print("✅ Database schema updated successfully!")


if __name__ == "__main__":
    try:
        update_field_sizes()
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        sys.exit(1)
