#!/usr/bin/env python3
"""
Test script to verify database relationships and data integrity
"""
import os
import sys
import django
from django.db import connection

# Add the project directory to Python path
sys.path.append('/home/isha/deepak/MFM_offline_setup/meter_dashboard')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')
django.setup()


def test_foreign_key_relationships():
    """Test foreign key relationships between tables"""
    print("🔍 Testing Database Relationships\n")

    with connection.cursor() as cursor:
        # 1. Check DCMS_PI_SETUP records
        print("1️⃣ DCMS_PI_SETUP Records:")
        cursor.execute(
            "SELECT id, pi_name, pi_ip, location FROM dcms_pi_setup ORDER BY id")
        pi_setups = cursor.fetchall()

        if pi_setups:
            for setup in pi_setups:
                print(
                    f"   ID: {setup[0]}, Name: {setup[1]}, IP: {setup[2]}, Location: {setup[3]}")
        else:
            print("   ⚠️ No DCMS_PI_SETUP records found")

        print()

        # 2. Check ENV_CONFIG records
        print("2️⃣ ENV_CONFIG Records:")
        cursor.execute("""
            SELECT ec.pi_setup_id, dps.pi_name, ec.simulation_mode, ec.reading_interval 
            FROM env_config ec 
            JOIN dcms_pi_setup dps ON ec.pi_setup_id = dps.id 
            ORDER BY ec.pi_setup_id
        """)
        env_configs = cursor.fetchall()

        if env_configs:
            for config in env_configs:
                print(
                    f"   Pi Setup ID: {config[0]}, Pi Name: {config[1]}, Simulation: {config[2]}, Interval: {config[3]}s")
        else:
            print("   ⚠️ No ENV_CONFIG records found")

        print()

        # 3. Check meter readings with pi_setup_id
        print("3️⃣ Meter Readings with Pi Setup (sample):")
        cursor.execute("""
            SELECT mr.id, mr.device_id, mr.meter_name, mr.pi_setup_id, dps.pi_name, mr.time
            FROM meter_readings mr 
            LEFT JOIN dcms_pi_setup dps ON mr.pi_setup_id = dps.id 
            ORDER BY mr.time DESC 
            LIMIT 5
        """)
        readings = cursor.fetchall()

        if readings:
            for reading in readings:
                pi_name = reading[4] if reading[4] else "No Pi Setup"
                print(
                    f"   Reading ID: {reading[0]}, Device: {reading[1]}, Meter: {reading[2]}, Pi Setup: {pi_name}, Time: {reading[5]}")
        else:
            print("   ⚠️ No meter readings found")

        print()

        # 4. Count statistics
        print("4️⃣ Database Statistics:")

        # Total records
        cursor.execute("SELECT COUNT(*) FROM dcms_pi_setup")
        pi_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM env_config")
        env_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM meter_readings")
        readings_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM meter_readings WHERE pi_setup_id IS NOT NULL")
        linked_readings = cursor.fetchone()[0]

        print(f"   📊 DCMS_PI_SETUP records: {pi_count}")
        print(f"   📊 ENV_CONFIG records: {env_count}")
        print(f"   📊 Total meter readings: {readings_count}")
        print(f"   📊 Readings with Pi Setup link: {linked_readings}")
        print(
            f"   📊 Readings without Pi Setup: {readings_count - linked_readings}")

        print()

        # 5. Foreign key constraint check
        print("5️⃣ Foreign Key Integrity:")

        # Check for orphaned env_config records
        cursor.execute("""
            SELECT COUNT(*) FROM env_config ec 
            LEFT JOIN dcms_pi_setup dps ON ec.pi_setup_id = dps.id 
            WHERE dps.id IS NULL
        """)
        orphaned_env = cursor.fetchone()[0]

        # Check for invalid pi_setup_id in meter_readings
        cursor.execute("""
            SELECT COUNT(*) FROM meter_readings mr 
            LEFT JOIN dcms_pi_setup dps ON mr.pi_setup_id = dps.id 
            WHERE mr.pi_setup_id IS NOT NULL AND dps.id IS NULL
        """)
        orphaned_readings = cursor.fetchone()[0]

        if orphaned_env == 0 and orphaned_readings == 0:
            print("   ✅ All foreign key relationships are valid!")
        else:
            print(f"   ⚠️ Found {orphaned_env} orphaned ENV_CONFIG records")
            print(f"   ⚠️ Found {orphaned_readings} orphaned meter readings")


if __name__ == "__main__":
    try:
        test_foreign_key_relationships()
        print("\n✅ Database relationship test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        sys.exit(1)
