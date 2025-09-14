#!/usr/bin/env python3
"""
Generate PostgreSQL schema from Django models

This script shows what the PostgreSQL schema should look like
based on your current Django models.
"""


def print_dcms_pi_setup_schema():
    """Print the expected PostgreSQL schema for DCMS_PI_SETUP table"""

    print("-- PostgreSQL Schema for DCMS_PI_SETUP table")
    print("-- Table name: dcms_pi_setup")
    print()

    schema = """
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

-- Indexes for DCMS_PI_SETUP
CREATE INDEX idx_dcms_pi_setup_pi_name ON dcms_pi_setup(pi_name);
CREATE INDEX idx_dcms_pi_setup_pi_ip ON dcms_pi_setup(pi_ip);
CREATE INDEX idx_dcms_pi_setup_location ON dcms_pi_setup(location);
CREATE INDEX idx_dcms_pi_setup_active ON dcms_pi_setup(is_active);

-- Comments
COMMENT ON TABLE dcms_pi_setup IS 'Configuration and connection details for Raspberry Pi devices';
COMMENT ON COLUMN dcms_pi_setup.pi_name IS 'Unique name identifier for the Pi device';
COMMENT ON COLUMN dcms_pi_setup.pi_ip IS 'IP address of the Pi device';
COMMENT ON COLUMN dcms_pi_setup.ssh_username IS 'SSH username for connecting to Pi';
COMMENT ON COLUMN dcms_pi_setup.config_path IS 'Path to configuration file on the Pi';
"""

    print(schema)


def print_env_config_schema():
    """Print the expected PostgreSQL schema for ENV_CONFIG table"""

    print("\n-- PostgreSQL Schema for ENV_CONFIG table")
    print("-- Table name: env_config")
    print()

    schema = """
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

-- Indexes for ENV_CONFIG
CREATE INDEX idx_env_config_log_level ON env_config(log_level);
CREATE INDEX idx_env_config_simulation ON env_config(simulation_mode);

-- Constraints
ALTER TABLE env_config 
ADD CONSTRAINT check_reading_interval_positive 
CHECK (reading_interval > 0);

ALTER TABLE env_config 
ADD CONSTRAINT check_inter_device_delay_positive 
CHECK (inter_device_delay >= 0);

-- Comments
COMMENT ON TABLE env_config IS 'Environment configuration settings for each Pi device';
COMMENT ON COLUMN env_config.reading_interval IS 'Interval between meter readings in seconds';
COMMENT ON COLUMN env_config.inter_device_delay IS 'Delay between device communications in seconds';
"""

    print(schema)


def print_meterreading_schema():
    """Print the expected PostgreSQL schema for MeterReading model with foreign keys"""

    print("\n-- PostgreSQL Schema for MeterReading model (Updated)")
    print("-- Table name: meters_meterreading")
    print()

    schema = """
CREATE TABLE meters_meterreading (
    id BIGSERIAL PRIMARY KEY,
    pi_setup_id BIGINT NOT NULL REFERENCES dcms_pi_setup(id) ON DELETE CASCADE,
    device_id VARCHAR(100) NOT NULL,
    meter_name VARCHAR(100) NOT NULL,
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    model VARCHAR(100) NOT NULL,
    watts_total DOUBLE PRECISION NOT NULL,
    watts_r_ph DOUBLE PRECISION,
    watts_y_ph DOUBLE PRECISION,
    watts_b_ph DOUBLE PRECISION,
    pf_ave DOUBLE PRECISION,
    pf_r_ph DOUBLE PRECISION,
    pf_y_ph DOUBLE PRECISION,
    pf_b_ph DOUBLE PRECISION,
    vln_average DOUBLE PRECISION,
    v_r_ph DOUBLE PRECISION,
    v_y_ph DOUBLE PRECISION,
    v_b_ph DOUBLE PRECISION,
    a_average DOUBLE PRECISION,
    a_r_ph DOUBLE PRECISION,
    a_y_ph DOUBLE PRECISION,
    a_b_ph DOUBLE PRECISION,
    frequency DOUBLE PRECISION,
    wh_received DOUBLE PRECISION,
    load_hours_delivered DOUBLE PRECISION,
    no_of_interruption INTEGER,
    on_hours VARCHAR(20),
    v_r_harmonics DOUBLE PRECISION,
    v_y_harmonics DOUBLE PRECISION,
    v_b_harmonics DOUBLE PRECISION,
    a_r_harmonics DOUBLE PRECISION,
    a_y_harmonics DOUBLE PRECISION,
    a_b_harmonics DOUBLE PRECISION
);

-- Recommended indexes for performance (Updated)
CREATE INDEX idx_meterreading_pi_setup_time ON meters_meterreading(pi_setup_id, time);
CREATE INDEX idx_meterreading_device_time ON meters_meterreading(device_id, time);
CREATE INDEX idx_meterreading_time ON meters_meterreading(time DESC);
CREATE INDEX idx_meterreading_meter_name ON meters_meterreading(meter_name);
CREATE INDEX idx_meterreading_pi_setup ON meters_meterreading(pi_setup_id);

-- Data validation constraints
ALTER TABLE meters_meterreading 
ADD CONSTRAINT check_watts_total_positive 
CHECK (watts_total >= 0);

ALTER TABLE meters_meterreading 
ADD CONSTRAINT check_frequency_range 
CHECK (frequency IS NULL OR (frequency BETWEEN 45 AND 65));

-- Comments for documentation
COMMENT ON TABLE meters_meterreading IS 'Stores meter reading data from various electrical meters linked to Pi devices';
COMMENT ON COLUMN meters_meterreading.pi_setup_id IS 'Foreign key reference to dcms_pi_setup table';
COMMENT ON COLUMN meters_meterreading.device_id IS 'Unique identifier for the measuring device';
COMMENT ON COLUMN meters_meterreading.time IS 'Timestamp when the reading was taken';
COMMENT ON COLUMN meters_meterreading.watts_total IS 'Total power consumption in watts';
COMMENT ON COLUMN meters_meterreading.vln_average IS 'Average voltage line to neutral';
COMMENT ON COLUMN meters_meterreading.frequency IS 'Electrical frequency in Hz (typically 50-60Hz)';
"""

    print(schema)


def print_deviceconfig_schema():
    """Print the expected PostgreSQL schema for DeviceConfig model"""

    print("\n-- PostgreSQL Schema for DeviceConfig model")
    print("-- Table name: meters_deviceconfig")
    print()

    schema = """
CREATE TABLE meters_deviceconfig (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    location VARCHAR(100) NOT NULL,
    meter_name VARCHAR(100) NOT NULL,
    ip_address INET NOT NULL,
    port INTEGER DEFAULT 502,
    reading_interval INTEGER DEFAULT 60,
    server_url VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_deviceconfig_device_id ON meters_deviceconfig(device_id);
CREATE INDEX idx_deviceconfig_active ON meters_deviceconfig(is_active);
CREATE INDEX idx_deviceconfig_location ON meters_deviceconfig(location);

-- Constraints
ALTER TABLE meters_deviceconfig 
ADD CONSTRAINT check_port_range 
CHECK (port BETWEEN 1 AND 65535);

ALTER TABLE meters_deviceconfig 
ADD CONSTRAINT check_reading_interval_positive 
CHECK (reading_interval > 0);
"""

    print(schema)


def print_verification_queries():
    """Print queries to verify the schema"""

    print("\n-- Verification Queries")
    print("-- Run these to check your current schema")
    print()

    queries = """
-- 1. Check if all tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('dcms_pi_setup', 'env_config', 'meters_meterreading');

-- 2. Check DCMS_PI_SETUP table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'dcms_pi_setup' 
ORDER BY ordinal_position;

-- 3. Check ENV_CONFIG table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'env_config' 
ORDER BY ordinal_position;

-- 4. Check meters_meterreading columns (updated)
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'meters_meterreading' 
ORDER BY ordinal_position;

-- 5. Check foreign key relationships
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
AND tc.table_name IN ('env_config', 'meters_meterreading');

-- 6. Check indexes for all tables
SELECT tablename, indexname, indexdef
FROM pg_indexes 
WHERE tablename IN ('dcms_pi_setup', 'env_config', 'meters_meterreading')
ORDER BY tablename, indexname;

-- 7. Sample data queries
-- Get Pi devices with their configurations
SELECT 
    d.pi_name,
    d.pi_ip,
    d.location,
    e.simulation_mode,
    e.reading_interval,
    e.log_level
FROM dcms_pi_setup d
LEFT JOIN env_config e ON d.id = e.pi_setup_id
WHERE d.is_active = true;

-- Get latest meter readings with Pi info
SELECT 
    d.pi_name,
    d.pi_ip,
    d.location,
    m.meter_name,
    m.time,
    m.watts_total,
    m.vln_average
FROM dcms_pi_setup d
JOIN meters_meterreading m ON d.id = m.pi_setup_id
ORDER BY m.time DESC 
LIMIT 10;

-- Count readings per Pi device
SELECT 
    d.pi_name,
    d.location,
    COUNT(m.id) as reading_count,
    MAX(m.time) as latest_reading
FROM dcms_pi_setup d
LEFT JOIN meters_meterreading m ON d.id = m.pi_setup_id
GROUP BY d.id, d.pi_name, d.location
ORDER BY reading_count DESC;
"""

    print(queries)


def print_sample_data():
    """Print sample data insertion queries"""

    print("\n-- Sample Data Insertion")
    print("-- Use these to test your tables")
    print()

    sample_data = """
-- Insert sample Pi devices
INSERT INTO dcms_pi_setup (pi_name, pi_ip, location, ssh_username, config_path, is_active) VALUES
('PI-001', '192.168.1.101', 'Building A - Floor 1', 'pi', '/home/pi/meter_config.json', true),
('PI-002', '192.168.1.102', 'Building A - Floor 2', 'pi', '/home/pi/meter_config.json', true),
('PI-003', '192.168.1.103', 'Building B - Floor 1', 'pi', '/home/pi/meter_config.json', true);

-- Insert environment configurations
INSERT INTO env_config (pi_setup_id, simulation_mode, reading_interval, inter_device_delay, enable_mqtt, log_level)
SELECT 
    id,
    false,
    30,
    0.1,
    true,
    'INFO'
FROM dcms_pi_setup;

-- Insert sample meter readings
INSERT INTO meters_meterreading (
    pi_setup_id, device_id, meter_name, time, model, watts_total, 
    vln_average, frequency, a_average
) 
SELECT 
    d.id,
    'METER_' || d.pi_name,
    'Main Meter - ' || d.location,
    NOW() - INTERVAL '1 hour',
    'LG5220',
    1500.0 + (RANDOM() * 500),
    230.0 + (RANDOM() * 10),
    50.0 + (RANDOM() * 0.5),
    6.5 + (RANDOM() * 1.0)
FROM dcms_pi_setup d
WHERE d.is_active = true;
"""

    print(sample_data)


if __name__ == "__main__":
    print("🗄️  PostgreSQL Schema Generator for Meter Dashboard (Updated)")
    print("=" * 70)

    print_dcms_pi_setup_schema()
    print_env_config_schema()
    print_meterreading_schema()
    print_deviceconfig_schema()
    print_verification_queries()
    print_sample_data()

    print("\n💡 Quick Commands:")
    print("   python3 manage.py describe_table dcms_pi_setup")
    print("   python3 manage.py describe_table env_config")
    print("   python3 manage.py describe_table meterreading")
    print("   python3 manage.py dbshell")
    print("   \\d dcms_pi_setup")
    print("   \\d env_config")
    print("   \\d meters_meterreading")
