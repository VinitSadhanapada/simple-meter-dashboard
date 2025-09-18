#!/usr/bin/env python3
"""
Test script to verify PostgreSQL connectivity and data insertion
"""
from datetime import datetime
from postgres_helper import PostgresHelper, create_meter_table, insert_meter_reading
import sys
sys.path.append('/home/isha/deepak/MFM_offline_setup')


def test_postgresql_connection():
    """Test PostgreSQL connection and data insertion"""

    DB_CONFIG = {
        'dbname': 'mfmdb',
        'user': 'mfmuser',
        'password': 'devi',
        'host': 'localhost',
        'port': 5432
    }

    print("🔍 Testing PostgreSQL Connection...")
    print(f"📊 Database: {DB_CONFIG['dbname']}")
    print(f"👤 User: {DB_CONFIG['user']}")
    print(f"🌐 Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")

    try:
        # Test connection
        db = PostgresHelper(**DB_CONFIG)
        db.connect()
        print("✅ PostgreSQL connection successful!")

        # Test table creation
        create_meter_table(db)
        print("✅ Table creation/verification successful!")

        # Test data insertion
        test_time = datetime.now().isoformat()
        insert_meter_reading(
            db,
            location="TEST_LOCATION",
            device_id="999",
            meter_name="TEST_METER",
            reading_time=test_time,
            model="TEST_MODEL",
            watts_total=1000.0,
            watts_r_ph=300.0,
            watts_y_ph=350.0,
            watts_b_ph=350.0,
            pf_ave=0.95,
            pf_r_ph=0.93,
            pf_y_ph=0.96,
            pf_b_ph=0.96,
            vln_average=230.0,
            v_r_ph=232.0,
            v_y_ph=231.0,
            v_b_ph=229.0,
            a_average=15.0,
            a_r_ph=14.5,
            a_y_ph=15.2,
            a_b_ph=15.3,
            frequency=50.0,
            wh_received=1000.0,
            load_hours_delivered=10.0,
            no_of_interruption=0.0,
            on_hours="10:30:45",
            v_r_harmonics=2.1,
            v_y_harmonics=2.0,
            v_b_harmonics=2.2,
            a_r_harmonics=3.1,
            a_y_harmonics=3.0,
            a_b_harmonics=3.2
        )
        print("✅ Test data insertion successful!")

        # Verify data was inserted
        cursor = db.connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM meter_readings WHERE meter_name = 'TEST_METER'")
        count = cursor.fetchone()[0]
        print(f"📊 Found {count} test record(s) in database")

        # Clean up test data
        cursor.execute(
            "DELETE FROM meter_readings WHERE meter_name = 'TEST_METER'")
        db.connection.commit()
        print("🧹 Test data cleaned up")

        # Show recent actual data
        cursor.execute("""
            SELECT location, meter_name, reading_time, watts_total 
            FROM meter_readings 
            WHERE reading_time > NOW() - INTERVAL '1 hour' 
            ORDER BY reading_time DESC 
            LIMIT 5
        """)
        recent_data = cursor.fetchall()

        if recent_data:
            print(f"\n📈 Recent data in PostgreSQL (last hour):")
            for location, meter_name, reading_time, watts_total in recent_data:
                print(
                    f"  🏢 {location} | 📟 {meter_name} | ⚡ {watts_total}W | 🕐 {reading_time}")
        else:
            print("\n📊 No recent data found in PostgreSQL")

        db.close()
        print("\n🎉 PostgreSQL is working correctly!")
        return True

    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        return False


if __name__ == "__main__":
    test_postgresql_connection()
