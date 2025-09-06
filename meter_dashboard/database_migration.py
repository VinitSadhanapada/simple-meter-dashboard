#!/usr/bin/env python3
"""
Database Migration Script for New Tables

This script creates the SQL commands to migrate your existing database
to the new schema with DCMS_PI_SETUP and ENV_CONFIG tables.
"""


def print_migration_sql():
    """Print SQL commands for database migration"""

    print("-- DATABASE MIGRATION SCRIPT")
    print("-- Run these commands in your PostgreSQL database")
    print("=" * 60)
    print()

    migration_sql = """
-- Step 1: Create DCMS_PI_SETUP table
CREATE TABLE dcms_pi_setup (
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

-- Step 2: Create ENV_CONFIG table
CREATE TABLE env_config (
    pi_setup_id BIGINT PRIMARY KEY REFERENCES dcms_pi_setup(id) ON DELETE CASCADE,
    simulation_mode BOOLEAN DEFAULT false,
    reading_interval INTEGER DEFAULT 30,
    inter_device_delay DOUBLE PRECISION DEFAULT 0.1,
    port VARCHAR(100) DEFAULT '/dev/ttyUSB0',
    enable_mqtt BOOLEAN DEFAULT false,
    enable_rtc BOOLEAN DEFAULT true,
    log_level VARCHAR(10) DEFAULT 'INFO' CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 3: Insert sample Pi devices (modify as needed for your setup)
INSERT INTO dcms_pi_setup (pi_name, pi_ip, location, ssh_username, config_path) VALUES
('DEFAULT_PI', '192.168.1.100', 'Default Location', 'pi', '/home/pi/config.json');

-- Step 4: Create default environment config
INSERT INTO env_config (pi_setup_id, simulation_mode, reading_interval)
SELECT id, false, 30 FROM dcms_pi_setup WHERE pi_name = 'DEFAULT_PI';

-- Step 5: Add foreign key column to meters_meterreading
ALTER TABLE meters_meterreading 
ADD COLUMN pi_setup_id BIGINT;

-- Step 6: Update existing meter readings to reference default Pi
UPDATE meters_meterreading 
SET pi_setup_id = (SELECT id FROM dcms_pi_setup WHERE pi_name = 'DEFAULT_PI')
WHERE pi_setup_id IS NULL;

-- Step 7: Make pi_setup_id NOT NULL and add foreign key constraint
ALTER TABLE meters_meterreading 
ALTER COLUMN pi_setup_id SET NOT NULL;

ALTER TABLE meters_meterreading 
ADD CONSTRAINT fk_meterreading_pi_setup 
FOREIGN KEY (pi_setup_id) REFERENCES dcms_pi_setup(id) ON DELETE CASCADE;

-- Step 8: Remove old location column from meters_meterreading (optional)
-- Uncomment if you want to remove the direct location field
-- ALTER TABLE meters_meterreading DROP COLUMN location;

-- Step 9: Create indexes for performance
CREATE INDEX idx_dcms_pi_setup_pi_name ON dcms_pi_setup(pi_name);
CREATE INDEX idx_dcms_pi_setup_pi_ip ON dcms_pi_setup(pi_ip);
CREATE INDEX idx_dcms_pi_setup_location ON dcms_pi_setup(location);
CREATE INDEX idx_dcms_pi_setup_active ON dcms_pi_setup(is_active);

CREATE INDEX idx_env_config_log_level ON env_config(log_level);
CREATE INDEX idx_env_config_simulation ON env_config(simulation_mode);

CREATE INDEX idx_meterreading_pi_setup_time ON meters_meterreading(pi_setup_id, time);
CREATE INDEX idx_meterreading_pi_setup ON meters_meterreading(pi_setup_id);

-- Step 10: Add constraints
ALTER TABLE env_config 
ADD CONSTRAINT check_reading_interval_positive 
CHECK (reading_interval > 0);

ALTER TABLE env_config 
ADD CONSTRAINT check_inter_device_delay_positive 
CHECK (inter_device_delay >= 0);

-- Step 11: Add comments
COMMENT ON TABLE dcms_pi_setup IS 'Configuration and connection details for Raspberry Pi devices';
COMMENT ON TABLE env_config IS 'Environment configuration settings for each Pi device';
COMMENT ON COLUMN dcms_pi_setup.pi_name IS 'Unique name identifier for the Pi device';
COMMENT ON COLUMN dcms_pi_setup.pi_ip IS 'IP address of the Pi device';
COMMENT ON COLUMN env_config.reading_interval IS 'Interval between meter readings in seconds';
"""

    print(migration_sql)


def print_rollback_sql():
    """Print SQL commands to rollback the migration if needed"""

    print("\n-- ROLLBACK SCRIPT (if needed)")
    print("-- Use these commands to revert changes")
    print("=" * 60)
    print()

    rollback_sql = """
-- WARNING: This will delete all new tables and data!
-- Only run if you need to completely rollback the migration

-- Remove foreign key constraint
ALTER TABLE meters_meterreading DROP CONSTRAINT IF EXISTS fk_meterreading_pi_setup;

-- Remove the new column
ALTER TABLE meters_meterreading DROP COLUMN IF EXISTS pi_setup_id;

-- Drop tables (this will delete all data!)
DROP TABLE IF EXISTS env_config;
DROP TABLE IF EXISTS dcms_pi_setup;

-- Note: You may want to restore the location column if you removed it
-- ALTER TABLE meters_meterreading ADD COLUMN location VARCHAR(100);
"""

    print(rollback_sql)


def print_verification_after_migration():
    """Print verification queries to run after migration"""

    print("\n-- POST-MIGRATION VERIFICATION")
    print("-- Run these to verify the migration was successful")
    print("=" * 60)
    print()

    verification_sql = """
-- Check that all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('dcms_pi_setup', 'env_config', 'meters_meterreading');

-- Check foreign key relationships
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
AND tc.table_name IN ('env_config', 'meters_meterreading');

-- Check that all meter readings have valid pi_setup_id
SELECT 
    COUNT(*) as total_readings,
    COUNT(pi_setup_id) as readings_with_pi_setup,
    COUNT(*) - COUNT(pi_setup_id) as readings_without_pi_setup
FROM meters_meterreading;

-- Show sample data with joins
SELECT 
    d.pi_name,
    d.pi_ip,
    d.location,
    e.reading_interval,
    e.log_level,
    COUNT(m.id) as meter_reading_count
FROM dcms_pi_setup d
LEFT JOIN env_config e ON d.id = e.pi_setup_id
LEFT JOIN meters_meterreading m ON d.id = m.pi_setup_id
GROUP BY d.id, d.pi_name, d.pi_ip, d.location, e.reading_interval, e.log_level;
"""

    print(verification_sql)


if __name__ == "__main__":
    print("🔄 Database Migration Script for DCMS Pi Setup Tables")
    print("📅 Created for: Meter Dashboard Schema Update")
    print()

    print_migration_sql()
    print_rollback_sql()
    print_verification_after_migration()

    print("\n💡 Migration Steps:")
    print("1. Backup your current database")
    print("2. Run the migration SQL commands above")
    print("3. Run the verification queries")
    print("4. Update your Django models and run migrations")
    print("5. Test your application")
    print()
    print("🚨 IMPORTANT: Always backup your database before running migrations!")
