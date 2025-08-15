#!/usr/bin/env python3
"""
PostgreSQL Schema Migration Script for Existing Database

This script migrates your existing MFM database to include the new tables:
- DCMS_PI_SETUP
- ENV_CONFIG
- Updates existing meter_readings table with foreign keys

Uses your existing PostgreSQL credentials from offline_rpi_dashboard_db.py
"""

import psycopg2
import psycopg2.extras
from datetime import datetime
import sys

# Your existing database configuration from offline_rpi_dashboard_db.py
DB_CONFIG = {
    'dbname': 'mfmdb',
    'user': 'mfmuser',
    'password': 'devi',
    'host': '192.168.43.127',
    'port': 5432
}


def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None


def check_existing_tables(cursor):
    """Check what tables already exist"""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    tables = [row[0] for row in cursor.fetchall()]
    print("📋 Existing tables:")
    for table in tables:
        print(f"   - {table}")

    return tables


def create_dcms_pi_setup_table(cursor):
    """Create DCMS_PI_SETUP table"""
    print("🔧 Creating DCMS_PI_SETUP table...")

    sql = """
    CREATE TABLE IF NOT EXISTS dcms_pi_setup (
        id BIGSERIAL PRIMARY KEY,
        pi_name VARCHAR(100) UNIQUE NOT NULL,
        pi_ip INET UNIQUE NOT NULL,
        location VARCHAR(100) NOT NULL,
        ssh_username VARCHAR(50) NOT NULL,
        ssh_password VARCHAR(100),
        ssh_key_path VARCHAR(255),
        config_path VARCHAR(255) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_connected TIMESTAMP WITH TIME ZONE,
        is_active BOOLEAN DEFAULT true
    );
    
    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_pi_name ON dcms_pi_setup(pi_name);
    CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_pi_ip ON dcms_pi_setup(pi_ip);
    CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_location ON dcms_pi_setup(location);
    CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_active ON dcms_pi_setup(is_active);
    
    -- Add comments
    COMMENT ON TABLE dcms_pi_setup IS 'Configuration and connection details for Raspberry Pi devices';
    COMMENT ON COLUMN dcms_pi_setup.pi_name IS 'Unique name identifier for the Pi device';
    COMMENT ON COLUMN dcms_pi_setup.pi_ip IS 'IP address of the Pi device';
    COMMENT ON COLUMN dcms_pi_setup.ssh_username IS 'SSH username for connecting to Pi';
    COMMENT ON COLUMN dcms_pi_setup.config_path IS 'Path to configuration file on the Pi';
    """

    cursor.execute(sql)
    print("✅ DCMS_PI_SETUP table created successfully")


def create_env_config_table(cursor):
    """Create ENV_CONFIG table"""
    print("🔧 Creating ENV_CONFIG table...")

    # First create the table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS env_config (
            pi_setup_id BIGINT PRIMARY KEY REFERENCES dcms_pi_setup(id) ON DELETE CASCADE,
            simulation_mode BOOLEAN DEFAULT false,
            reading_interval INTEGER DEFAULT 30,
            inter_device_delay DOUBLE PRECISION DEFAULT 0.1,
            port VARCHAR(100) DEFAULT '/dev/ttyUSB0',
            enable_mqtt BOOLEAN DEFAULT false,
            enable_rtc BOOLEAN DEFAULT true,
            log_level VARCHAR(10) DEFAULT 'INFO',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Add check constraint for log_level
    try:
        cursor.execute("""
            ALTER TABLE env_config 
            ADD CONSTRAINT check_log_level 
            CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
        """)
    except Exception:
        pass  # Constraint may already exist

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_env_config_log_level ON env_config(log_level)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_env_config_simulation ON env_config(simulation_mode)
    """)

    # Add other constraints
    try:
        cursor.execute("""
            ALTER TABLE env_config 
            ADD CONSTRAINT check_reading_interval_positive 
            CHECK (reading_interval > 0)
        """)
    except Exception:
        pass  # Constraint may already exist

    try:
        cursor.execute("""
            ALTER TABLE env_config 
            ADD CONSTRAINT check_inter_device_delay_positive 
            CHECK (inter_device_delay >= 0)
        """)
    except Exception:
        pass  # Constraint may already exist

    # Add comments
    cursor.execute("""
        COMMENT ON TABLE env_config IS 'Environment configuration settings for each Pi device'
    """)
    cursor.execute("""
        COMMENT ON COLUMN env_config.reading_interval IS 'Interval between meter readings in seconds'
    """)
    cursor.execute("""
        COMMENT ON COLUMN env_config.inter_device_delay IS 'Delay between device communications in seconds'
    """)

    print("✅ ENV_CONFIG table created successfully")


def get_existing_meter_table_info(cursor):
    """Get information about existing meter table"""
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name LIKE '%meter%' 
        AND table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)

    columns = cursor.fetchall()
    if columns:
        print("📊 Existing meter table columns:")
        for col_name, data_type, is_nullable in columns:
            print(
                f"   - {col_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")

    return columns


def update_meter_readings_table(cursor):
    """Update existing meter readings table to add foreign key"""
    print("🔧 Updating meter readings table...")

    # First, check if the table exists and what it's called
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%meter%'
    """)

    meter_tables = cursor.fetchall()
    if not meter_tables:
        print("❌ No meter table found!")
        return False

    # Assume first meter table is the main one
    table_name = meter_tables[0][0]
    print(f"📋 Found meter table: {table_name}")

    # Check if pi_setup_id column already exists
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s 
        AND column_name = 'pi_setup_id'
    """, (table_name,))

    if cursor.fetchone():
        print("⚠️ pi_setup_id column already exists")
        return True

    # Add pi_setup_id column
    cursor.execute(f"""
        ALTER TABLE {table_name} 
        ADD COLUMN pi_setup_id BIGINT;
    """)

    # Add foreign key constraint (after data is populated)
    print(f"✅ Added pi_setup_id column to {table_name}")
    return True


def insert_sample_pi_data(cursor):
    """Insert sample Pi device data"""
    print("📝 Inserting sample Pi device data...")

    sample_data = [
        ('PI-001', '192.168.43.127', 'Main Server Location',
         'pi', '/home/pi/meter_config.json'),
        ('PI-002', '192.168.1.101', 'Building A - Floor 1',
         'pi', '/home/pi/meter_config.json'),
        ('PI-003', '192.168.1.102', 'Building A - Floor 2',
         'pi', '/home/pi/meter_config.json'),
    ]

    for pi_name, pi_ip, location, ssh_user, config_path in sample_data:
        cursor.execute("""
            INSERT INTO dcms_pi_setup (pi_name, pi_ip, location, ssh_username, config_path)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (pi_name) DO NOTHING
        """, (pi_name, pi_ip, location, ssh_user, config_path))

    # Insert corresponding env_config entries
    cursor.execute("""
        INSERT INTO env_config (pi_setup_id, simulation_mode, reading_interval, enable_mqtt, log_level)
        SELECT id, false, 30, true, 'INFO'
        FROM dcms_pi_setup
        WHERE NOT EXISTS (
            SELECT 1 FROM env_config WHERE pi_setup_id = dcms_pi_setup.id
        )
    """)

    print("✅ Sample Pi device data inserted")


def update_existing_meter_data(cursor):
    """Update existing meter readings to reference Pi devices"""
    print("🔄 Updating existing meter readings with Pi references...")

    # Get the meter table name
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%meter%'
    """)

    meter_tables = cursor.fetchall()
    if not meter_tables:
        return

    table_name = meter_tables[0][0]

    # Update existing records to reference the default Pi (PI-001)
    cursor.execute(f"""
        UPDATE {table_name} 
        SET pi_setup_id = (
            SELECT id FROM dcms_pi_setup WHERE pi_name = 'PI-001'
        )
        WHERE pi_setup_id IS NULL
    """)

    updated_rows = cursor.rowcount
    print(f"✅ Updated {updated_rows} meter readings with Pi reference")


def add_foreign_key_constraint(cursor):
    """Add foreign key constraint to meter readings table"""
    print("🔗 Adding foreign key constraint...")

    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%meter%'
    """)

    meter_tables = cursor.fetchall()
    if not meter_tables:
        return

    table_name = meter_tables[0][0]

    try:
        cursor.execute(f"""
            ALTER TABLE {table_name} 
            ADD CONSTRAINT fk_meter_pi_setup 
            FOREIGN KEY (pi_setup_id) REFERENCES dcms_pi_setup(id) ON DELETE CASCADE
        """)
        print("✅ Foreign key constraint added")
    except Exception as e:
        print(f"⚠️ Foreign key constraint may already exist: {e}")


def verify_migration(cursor):
    """Verify the migration was successful"""
    print("🔍 Verifying migration...")

    # Check table counts
    tables_to_check = ['dcms_pi_setup', 'env_config']

    for table in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   - {table}: {count} records")

    # Check foreign key relationships
    cursor.execute("""
        SELECT 
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND (tc.table_name = 'env_config' OR kcu.column_name = 'pi_setup_id')
    """)

    foreign_keys = cursor.fetchall()
    if foreign_keys:
        print("   ✅ Foreign key relationships:")
        for fk in foreign_keys:
            print(f"      - {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")

    print("✅ Migration verification completed")


def main():
    """Main migration function"""
    print("🚀 PostgreSQL Schema Migration for MFM Database")
    print("=" * 60)
    print(f"Database: {DB_CONFIG['dbname']} at {DB_CONFIG['host']}")
    print()

    # Connect to database
    conn = connect_to_database()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Check existing tables
        existing_tables = check_existing_tables(cursor)
        print()

        # Get existing meter table info
        get_existing_meter_table_info(cursor)
        print()

        # Create new tables
        create_dcms_pi_setup_table(cursor)
        create_env_config_table(cursor)

        # Update meter readings table
        update_meter_readings_table(cursor)

        # Insert sample data
        insert_sample_pi_data(cursor)

        # Update existing meter data
        update_existing_meter_data(cursor)

        # Add foreign key constraint
        add_foreign_key_constraint(cursor)

        # Verify migration
        verify_migration(cursor)

        # Commit all changes
        conn.commit()
        print("\n🎉 Migration completed successfully!")

        print("\n💡 Next steps:")
        print("1. Verify data: psql -h 192.168.43.127 -U mfmuser -d mfmdb")
        print("2. Check tables: \\dt")
        print("3. View Pi devices: SELECT * FROM dcms_pi_setup;")
        print("4. View env config: SELECT * FROM env_config;")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
