#!/usr/bin/env python3
"""
Fix dcms_pi_setup table constraints
"""
import sys
sys.path.append('/home/isha/deepak/MFM_offline_setup')


def fix_dcms_pi_setup_table():
    """Fix the dcms_pi_setup table to allow NULL values in optional fields"""

    try:
        from postgres_helper import PostgresHelper

        DB_CONFIG = {
            'dbname': 'mfmdb',
            'user': 'mfmuser',
            'password': 'devi',
            'host': 'localhost',
            'port': 5432
        }

        print("🔧 Fixing dcms_pi_setup table constraints...")

        db = PostgresHelper(**DB_CONFIG)
        db.connect()
        cursor = db.conn.cursor()

        # Check current table structure
        cursor.execute("""
            SELECT column_name, is_nullable, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'dcms_pi_setup' 
            ORDER BY ordinal_position;
        """)

        columns = cursor.fetchall()
        print("📊 Current table structure:")
        for col_name, nullable, data_type in columns:
            print(
                f"  {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")

        # Drop NOT NULL constraints on optional fields
        print("\n🔧 Removing NOT NULL constraints from optional fields...")

        optional_fields = ['ssh_username', 'ssh_key_path', 'ssh_password', 'description',
                           'contact_person', 'installation_date', 'cpu_usage', 'memory_usage',
                           'disk_usage', 'uptime_hours', 'connection_status']

        for field in optional_fields:
            try:
                cursor.execute(f"""
                    ALTER TABLE dcms_pi_setup 
                    ALTER COLUMN {field} DROP NOT NULL;
                """)
                print(f"✅ Removed NOT NULL constraint from {field}")
            except Exception as e:
                if "does not exist" in str(e):
                    print(f"⚠️  Column {field} does not exist")
                else:
                    print(f"⚠️  Could not modify {field}: {e}")

        db.conn.commit()
        print("\n✅ Table constraints fixed!")

        # Test inserting Pi data
        print("\n🧪 Testing Pi registration...")
        test_query = """
        INSERT INTO dcms_pi_setup (pi_name, pi_ip, location, is_active, last_connected)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (pi_name) 
        DO UPDATE SET 
            pi_ip = EXCLUDED.pi_ip,
            location = EXCLUDED.location,
            is_active = EXCLUDED.is_active,
            last_connected = CURRENT_TIMESTAMP
        RETURNING id;
        """

        cursor.execute(test_query, ('Test pi 11',
                       '172.20.10.2', 'KONDRAI', True))
        pi_id = cursor.fetchone()[0]
        db.conn.commit()

        print(f"✅ Successfully registered Pi with ID: {pi_id}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Error fixing table: {e}")
        return False


if __name__ == "__main__":
    fix_dcms_pi_setup_table()
