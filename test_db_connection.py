#!/usr/bin/env python3
"""
Test database connection and show exact connection details for pgAdmin
"""
import psycopg2
import sys

# Your database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'mfmdb',
    'user': 'mfmuser',
    'password': 'devi'
}


def test_connection():
    """Test database connection and show details"""
    print("=== Database Connection Test ===")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"Port: {DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Password: {'*' * len(DB_CONFIG['password'])}")
    print()

    try:
        print("Testing connection...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connection successful!")
        print(f"PostgreSQL Version: {version}")

        # Check if our tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('meter_readings', 'dcms_pi_setup', 'env_config')
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\n📊 Found {len(tables)} key tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count:,} rows")

        conn.close()

        print("\n🎯 Use these settings in pgAdmin:")
        print("=" * 40)
        print(f"Host name/address: {DB_CONFIG['host']}")
        print(f"Port: {DB_CONFIG['port']}")
        print(f"Maintenance database: {DB_CONFIG['database']}")
        print(f"Username: {DB_CONFIG['user']}")
        print(f"Password: {DB_CONFIG['password']}")
        print("=" * 40)

        return True

    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if PostgreSQL is running: sudo systemctl status postgresql")
        print("2. Start PostgreSQL: sudo systemctl start postgresql")
        print("3. Check if database exists: sudo -u postgres psql -l")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_postgresql_status():
    """Check PostgreSQL service status"""
    import subprocess

    print("\n=== PostgreSQL Service Status ===")
    try:
        result = subprocess.run(['systemctl', 'is-active', 'postgresql'],
                                capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ PostgreSQL service is active")
        else:
            print("❌ PostgreSQL service is not active")
            print("Run: sudo systemctl start postgresql")

    except Exception as e:
        print(f"Error checking service: {e}")


def check_port_listening():
    """Check if PostgreSQL is listening on port 5432"""
    import subprocess

    print("\n=== Port Check ===")
    try:
        result = subprocess.run(['netstat', '-tulpn'],
                                capture_output=True, text=True)
        if ':5432' in result.stdout:
            print("✅ PostgreSQL is listening on port 5432")
            for line in result.stdout.split('\n'):
                if ':5432' in line:
                    print(f"  {line.strip()}")
        else:
            print("❌ PostgreSQL is not listening on port 5432")

    except Exception as e:
        print(f"Error checking ports: {e}")


if __name__ == "__main__":
    check_postgresql_status()
    check_port_listening()
    test_connection()
