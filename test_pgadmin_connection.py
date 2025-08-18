#!/usr/bin/env python3
"""
Test the exact connection that pgAdmin would use
"""
import psycopg2
import sys


def test_pgadmin_connection():
    """Test connection using pgAdmin-style parameters"""

    # These are the exact parameters pgAdmin will use
    connection_params = {
        'host': 'localhost',
        'port': 5432,
        'dbname': 'mfmdb',  # Note: psycopg2 uses 'dbname', not 'database'
        'user': 'mfmuser',
        'password': 'devi'
    }

    print("Testing pgAdmin-style connection...")
    print(
        f"Connection: postgresql://{connection_params['user']}:***@{connection_params['host']}:{connection_params['port']}/{connection_params['dbname']}")

    try:
        # This is exactly how pgAdmin connects
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        # Test basic queries
        cursor.execute("SELECT current_database(), current_user, version();")
        db, user, version = cursor.fetchone()

        print(f"✅ Connection successful!")
        print(f"Database: {db}")
        print(f"User: {user}")
        print(f"PostgreSQL: {version.split()[0]} {version.split()[1]}")

        # Check your tables
        cursor.execute("""
            SELECT schemaname, tablename, 
                   pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('meter_readings', 'dcms_pi_setup')
            ORDER BY tablename;
        """)

        tables = cursor.fetchall()
        print(f"\n📊 Key tables found:")
        for schema, table, size in tables:
            print(f"  - {table}: {size}")

        conn.close()

        print(f"\n🎯 pgAdmin Connection Settings:")
        print("=" * 40)
        print(f"Host: {connection_params['host']}")
        print(f"Port: {connection_params['port']}")
        print(f"Database: {connection_params['dbname']}")
        print(f"Username: {connection_params['user']}")
        print(f"Password: {connection_params['password']}")
        print("Save password: YES")
        print("=" * 40)

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_pgadmin_connection()
