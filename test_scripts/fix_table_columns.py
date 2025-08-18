#!/usr/bin/env python3
"""
Check meter_readings table structure and fix column mapping
"""
import sys
sys.path.append('/home/isha/deepak/MFM_offline_setup')


def check_meter_readings_table():
    """Check the actual structure of meter_readings table"""

    try:
        from postgres_helper import PostgresHelper

        DB_CONFIG = {
            'dbname': 'mfmdb',
            'user': 'mfmuser',
            'password': 'devi',
            'host': 'localhost',
            'port': 5432
        }

        print("🔍 Checking meter_readings table structure...")
        db = PostgresHelper(**DB_CONFIG)
        db.connect()

        cursor = db.conn.cursor()

        # Get table structure
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'meter_readings' 
            ORDER BY ordinal_position;
        """)

        columns = cursor.fetchall()

        if not columns:
            print("❌ meter_readings table not found")
            return []

        print("\n📊 meter_readings table structure:")
        print(f"{'Column':<25} {'Type':<15} {'Nullable':<10} {'Default':<20}")
        print("-" * 75)

        column_names = []
        for col_name, data_type, nullable, default in columns:
            nullable_str = "YES" if nullable == "YES" else "NO"
            default_str = str(default) if default else "None"
            print(
                f"{col_name:<25} {data_type:<15} {nullable_str:<10} {default_str:<20}")
            column_names.append(col_name)

        print(f"\n📋 Available columns: {column_names}")

        # Check what column is used for timestamp
        timestamp_columns = [
            col for col in column_names if 'time' in col.lower() or 'date' in col.lower()]
        print(f"🕒 Timestamp-related columns: {timestamp_columns}")

        db.close()
        return column_names

    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
        return []


def fix_insert_query():
    """Fix the insert query to match actual table structure"""

    script_path = '/home/isha/deepak/MFM_offline_setup/offline_rpi_dashboard_db.py'

    # Common column name mappings
    column_mappings = {
        'reading_time': ['time', 'timestamp', 'created_at', 'datetime'],
        'device_id': ['device_id', 'address', 'meter_address'],
        'meter_name': ['meter_name', 'name', 'device_name']
    }

    try:
        with open(script_path, 'r') as f:
            content = f.read()

        # Replace the problematic column names
        # Most likely 'reading_time' should be 'time'
        updated_content = content.replace('reading_time', 'time')

        # Also might need to fix device_id if it's actually 'address'
        if 'device_id' not in content and 'address' in content:
            updated_content = updated_content.replace('device_id', 'address')

        with open(script_path, 'w') as f:
            f.write(updated_content)

        print("✅ Fixed column name mapping")
        print("🔧 Changed 'reading_time' to 'time'")

        return True

    except Exception as e:
        print(f"❌ Error fixing insert query: {e}")
        return False


if __name__ == "__main__":
    columns = check_meter_readings_table()
    if columns:
        print("\n🔧 Fixing insert query...")
        fix_insert_query()
