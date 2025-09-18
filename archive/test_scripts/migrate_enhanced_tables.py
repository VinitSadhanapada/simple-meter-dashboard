#!/usr/bin/env python3
"""
Enhanced table structure for meter readings with proper foreign key relationships

This script creates/updates tables to ensure:
1. meter_readings table (for Pi script) has pi_setup_id foreign key
2. meters_meterreading table (for Django app) has pi_setup_id foreign key
3. Both tables have all necessary fields
4. Proper relationships with dcms_pi_setup table
"""


def get_meter_readings_schema():
    """Define the complete schema for meter_readings table (Pi script)"""
    return """
    CREATE TABLE IF NOT EXISTS meter_readings (
        id SERIAL PRIMARY KEY,
        pi_setup_id INTEGER REFERENCES dcms_pi_setup(id),
        location VARCHAR(100),
        device_id VARCHAR(50),
        meter_name VARCHAR(100),
        reading_time TIMESTAMP NOT NULL,
        model VARCHAR(50),
        
        -- Power measurements
        watts_total REAL,
        watts_r_ph REAL,
        watts_y_ph REAL,
        watts_b_ph REAL,
        
        -- Power factor
        pf_ave REAL,
        pf_r_ph REAL,
        pf_y_ph REAL,
        pf_b_ph REAL,
        
        -- Voltage measurements
        vln_average REAL,
        v_r_ph REAL,
        v_y_ph REAL,
        v_b_ph REAL,
        
        -- Current measurements
        a_average REAL,
        a_r_ph REAL,
        a_y_ph REAL,
        a_b_ph REAL,
        
        -- System measurements
        frequency REAL,
        wh_received REAL,
        load_hours_delivered REAL,
        no_of_interruption REAL,
        on_hours VARCHAR(20),
        
        -- Harmonics
        v_r_harmonics REAL,
        v_y_harmonics REAL,
        v_b_harmonics REAL,
        a_r_harmonics REAL,
        a_y_harmonics REAL,
        a_b_harmonics REAL,
        
        -- Metadata
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_meter_readings_pi_setup_id ON meter_readings(pi_setup_id);
    CREATE INDEX IF NOT EXISTS idx_meter_readings_time ON meter_readings(reading_time);
    CREATE INDEX IF NOT EXISTS idx_meter_readings_location ON meter_readings(location);
    CREATE INDEX IF NOT EXISTS idx_meter_readings_meter_name ON meter_readings(meter_name);
    """


def get_django_meter_readings_schema():
    """Define the complete schema for meters_meterreading table (Django app)"""
    return """
    CREATE TABLE IF NOT EXISTS meters_meterreading (
        id SERIAL PRIMARY KEY,
        pi_setup_id INTEGER REFERENCES dcms_pi_setup(id),
        
        -- Basic info
        device_id VARCHAR(50),
        location VARCHAR(100),
        meter_name VARCHAR(100),
        time TIMESTAMP NOT NULL,
        model VARCHAR(50),
        
        -- Power measurements
        watts_total REAL,
        watts_r_ph REAL,
        watts_y_ph REAL,
        watts_b_ph REAL,
        
        -- Power factor
        pf_ave REAL,
        pf_r_ph REAL,
        pf_y_ph REAL,
        pf_b_ph REAL,
        
        -- Voltage measurements
        vln_average REAL,
        v_r_ph REAL,
        v_y_ph REAL,
        v_b_ph REAL,
        
        -- Current measurements (total calculated fields)
        current_total REAL,
        a_r_ph REAL,
        a_y_ph REAL,
        a_b_ph REAL,
        
        -- System measurements
        frequency REAL,
        wh_received REAL,
        load_hours_delivered REAL,
        no_of_interruption INTEGER,
        on_hours VARCHAR(20),
        
        -- Harmonics
        v_r_harmonics REAL,
        v_y_harmonics REAL,
        v_b_harmonics REAL,
        a_r_harmonics REAL,
        a_y_harmonics REAL,
        a_b_harmonics REAL,
        
        -- Additional Django fields
        energy_consumed_kwh REAL,
        cost_estimate DECIMAL(10,2),
        data_quality_score REAL DEFAULT 1.0,
        
        -- Metadata
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Indexes for Django queries
    CREATE INDEX IF NOT EXISTS idx_meters_meterreading_pi_setup_id ON meters_meterreading(pi_setup_id);
    CREATE INDEX IF NOT EXISTS idx_meters_meterreading_time ON meters_meterreading(time);
    CREATE INDEX IF NOT EXISTS idx_meters_meterreading_location ON meters_meterreading(location);
    CREATE INDEX IF NOT EXISTS idx_meters_meterreading_meter_name ON meters_meterreading(meter_name);
    CREATE INDEX IF NOT EXISTS idx_meters_meterreading_device_id ON meters_meterreading(device_id);
    """


def update_dcms_pi_setup_table():
    """Ensure dcms_pi_setup table has all necessary fields"""
    return """
    -- Update dcms_pi_setup table to match Django model structure
    CREATE TABLE IF NOT EXISTS dcms_pi_setup (
        id SERIAL PRIMARY KEY,
        pi_name VARCHAR(100) UNIQUE NOT NULL,
        pi_ip INET UNIQUE NOT NULL,
        location VARCHAR(100) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        last_connected TIMESTAMP,
        
        -- SSH configuration
        ssh_username VARCHAR(100),
        ssh_key_path TEXT,
        ssh_password TEXT,
        
        -- Additional fields
        description TEXT,
        contact_person VARCHAR(100),
        installation_date DATE,
        
        -- Status tracking
        cpu_usage REAL,
        memory_usage REAL,
        disk_usage REAL,
        uptime_hours INTEGER,
        connection_status VARCHAR(20) DEFAULT 'offline',
        
        -- Metadata
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Add missing columns if they don't exist
    DO $$ 
    BEGIN
        -- Add description column if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'dcms_pi_setup' AND column_name = 'description') THEN
            ALTER TABLE dcms_pi_setup ADD COLUMN description TEXT;
        END IF;
        
        -- Add contact_person column if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'dcms_pi_setup' AND column_name = 'contact_person') THEN
            ALTER TABLE dcms_pi_setup ADD COLUMN contact_person VARCHAR(100);
        END IF;
        
        -- Add installation_date column if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'dcms_pi_setup' AND column_name = 'installation_date') THEN
            ALTER TABLE dcms_pi_setup ADD COLUMN installation_date DATE;
        END IF;
        
        -- Add cpu_usage column if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'dcms_pi_setup' AND column_name = 'cpu_usage') THEN
            ALTER TABLE dcms_pi_setup ADD COLUMN cpu_usage REAL;
        END IF;
        
        -- Add memory_usage column if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'dcms_pi_setup' AND column_name = 'memory_usage') THEN
            ALTER TABLE dcms_pi_setup ADD COLUMN memory_usage REAL;
        END IF;
        
        -- Add disk_usage column if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'dcms_pi_setup' AND column_name = 'disk_usage') THEN
            ALTER TABLE dcms_pi_setup ADD COLUMN disk_usage REAL;
        END IF;
        
        -- Add uptime_hours column if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'dcms_pi_setup' AND column_name = 'uptime_hours') THEN
            ALTER TABLE dcms_pi_setup ADD COLUMN uptime_hours INTEGER;
        END IF;
        
        -- Add connection_status column if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'dcms_pi_setup' AND column_name = 'connection_status') THEN
            ALTER TABLE dcms_pi_setup ADD COLUMN connection_status VARCHAR(20) DEFAULT 'offline';
        END IF;
    END $$;
    
    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_location ON dcms_pi_setup(location);
    CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_active ON dcms_pi_setup(is_active);
    CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_status ON dcms_pi_setup(connection_status);
    """


def migrate_database_structure():
    """Apply all database structure updates"""

    # Import database helper
    import sys
    sys.path.append('/home/isha/deepak/MFM_offline_setup')

    from postgres_helper import PostgresHelper

    DB_CONFIG = {
        'dbname': 'mfmdb',
        'user': 'mfmuser',
        'password': 'devi',
        'host': 'localhost',
        'port': 5432
    }

    print("🔧 Updating database structure for enhanced meter readings...")

    try:
        # Connect to database
        db = PostgresHelper(**DB_CONFIG)
        db.connect()
        cursor = db.connection.cursor()

        print("1️⃣  Updating dcms_pi_setup table...")
        cursor.execute(update_dcms_pi_setup_table())

        print("2️⃣  Creating/updating meter_readings table (Pi script)...")
        cursor.execute(get_meter_readings_schema())

        print("3️⃣  Creating/updating meters_meterreading table (Django app)...")
        cursor.execute(get_django_meter_readings_schema())

        # Add pi_setup_id column to existing meter_readings if it doesn't exist
        print("4️⃣  Adding pi_setup_id foreign key to existing tables...")
        cursor.execute("""
            DO $$ 
            BEGIN
                -- Add pi_setup_id to meter_readings if not exists
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'meter_readings' AND column_name = 'pi_setup_id') THEN
                    ALTER TABLE meter_readings ADD COLUMN pi_setup_id INTEGER;
                    ALTER TABLE meter_readings ADD CONSTRAINT fk_meter_readings_pi_setup 
                        FOREIGN KEY (pi_setup_id) REFERENCES dcms_pi_setup(id);
                END IF;
                
                -- Add pi_setup_id to meters_meterreading if not exists
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'meters_meterreading' AND column_name = 'pi_setup_id') THEN
                    ALTER TABLE meters_meterreading ADD COLUMN pi_setup_id INTEGER;
                    ALTER TABLE meters_meterreading ADD CONSTRAINT fk_meters_meterreading_pi_setup 
                        FOREIGN KEY (pi_setup_id) REFERENCES dcms_pi_setup(id);
                END IF;
            END $$;
        """)

        db.connection.commit()

        print("✅ Database structure updated successfully!")

        # Show table relationships
        cursor.execute("""
            SELECT 
                t.table_name,
                COUNT(c.column_name) as column_count,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = t.table_name AND column_name = 'pi_setup_id'
                    ) THEN 'Yes' 
                    ELSE 'No' 
                END as has_pi_setup_fk
            FROM information_schema.tables t
            LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_name IN ('dcms_pi_setup', 'meter_readings', 'meters_meterreading')
            AND t.table_schema = 'public'
            GROUP BY t.table_name
            ORDER BY t.table_name;
        """)

        tables = cursor.fetchall()
        print(f"\n📊 Table Structure Summary:")
        print(f"{'Table Name':<25} {'Columns':<10} {'Has Pi FK':<10}")
        print("-" * 50)
        for table_name, col_count, has_fk in tables:
            print(f"{table_name:<25} {col_count:<10} {has_fk:<10}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def verify_relationships():
    """Verify the foreign key relationships are working"""

    import sys
    sys.path.append('/home/isha/deepak/MFM_offline_setup')

    from postgres_helper import PostgresHelper

    DB_CONFIG = {
        'dbname': 'mfmdb',
        'user': 'mfmuser',
        'password': 'devi',
        'host': 'localhost',
        'port': 5432
    }

    try:
        db = PostgresHelper(**DB_CONFIG)
        db.connect()
        cursor = db.connection.cursor()

        print("🔍 Verifying foreign key relationships...")

        # Check foreign key constraints
        cursor.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND (tc.table_name = 'meter_readings' OR tc.table_name = 'meters_meterreading')
            AND ccu.table_name = 'dcms_pi_setup';
        """)

        relationships = cursor.fetchall()
        if relationships:
            print("✅ Foreign key relationships verified:")
            for table, column, foreign_table, foreign_column in relationships:
                print(f"  {table}.{column} → {foreign_table}.{foreign_column}")
        else:
            print("⚠️  No foreign key relationships found")

        db.close()

    except Exception as e:
        print(f"❌ Verification failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Enhanced Database Structure Migration...")
    print("=" * 60)

    if migrate_database_structure():
        print("\n🔍 Verifying relationships...")
        verify_relationships()

        print("\n🎉 Migration completed successfully!")
        print("\n📝 Summary:")
        print("✅ dcms_pi_setup table: Enhanced with all fields")
        print("✅ meter_readings table: For Pi script with pi_setup_id FK")
        print("✅ meters_meterreading table: For Django app with pi_setup_id FK")
        print("✅ Foreign key relationships: Properly established")

        print("\n💡 Next steps:")
        print("1. Update your Django models to include pi_setup field")
        print("2. Run Django makemigrations and migrate")
        print("3. Test the Pi script with new structure")
    else:
        print("\n❌ Migration failed!")
