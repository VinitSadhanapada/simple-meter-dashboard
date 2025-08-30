#!/usr/bin/env python3
"""
Quick Database Connection Test

Test connection to your existing PostgreSQL database.
"""

import psycopg2
import psycopg2.extras

# Your existing database configuration
DB_CONFIG = {
    'dbname': 'mfmdb',
    'user': 'mfmuser',
    'password': 'devi',
    'host': '10.53.66.59',
    'port': 5432
}


def test_connection():
    """Test database connection and show basic info"""
    print("🔍 Testing PostgreSQL connection...")
    print(f"Database: {DB_CONFIG['dbname']} at {DB_CONFIG['host']}")

    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        print("✅ Connection successful!")

        # Get database version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"PostgreSQL version: {version.split()[1]}")

        # List all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        tables = cursor.fetchall()
        print(f"\n📋 Found {len(tables)} tables:")
        for table in tables:
            # Get row count for each table
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"   - {table[0]}: {count} rows")
            except:
                print(f"   - {table[0]}: (unable to count)")

        # Check if meter table exists and show sample data
        meter_tables = [t[0] for t in tables if 'meter' in t[0].lower()]
        if meter_tables:
            meter_table = meter_tables[0]
            print(f"\n📊 Sample data from {meter_table}:")
            cursor.execute(f"SELECT * FROM {meter_table} LIMIT 3")

            rows = cursor.fetchall()
            if rows:
                # Show column names
                col_names = [desc[0] for desc in cursor.description]
                print(f"   Columns: {', '.join(col_names[:5])}...")

                # Show sample rows
                for i, row in enumerate(rows):
                    print(f"   Row {i+1}: {dict(row)}")
            else:
                print("   No data found")

        cursor.close()
        conn.close()

        print("\n✅ Database test completed successfully!")
        return True

    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 PostgreSQL Database Connection Test")
    print("=" * 50)
    test_connection()
    print("\n💡 If connection successful, you can run the migration:")
    print("   python3 migrate_existing_db.py")
