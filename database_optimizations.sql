"""
Database Performance Optimization Suggestions for Meter Dashboard

1. Add Database Indexes for Better Query Performance
2. Implement Database Partitioning for Large Data
3. Add Data Archiving Strategy
4. Optimize Queries with Database Views
"""

# Add these indexes to improve query performance
CREATE_INDEXES = """
-- Indexes for meter_readings table (7,500+ records and growing)
CREATE INDEX IF NOT EXISTS idx_meter_readings_time ON meter_readings(reading_time);
CREATE INDEX IF NOT EXISTS idx_meter_readings_location ON meter_readings(location);
CREATE INDEX IF NOT EXISTS idx_meter_readings_meter_name ON meter_readings(meter_name);
CREATE INDEX IF NOT EXISTS idx_meter_readings_time_location ON meter_readings(reading_time, location);
CREATE INDEX IF NOT EXISTS idx_meter_readings_pi_setup_time ON meter_readings(pi_setup_id, reading_time);

-- Indexes for device management
CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_active ON dcms_pi_setup(is_active);
CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_location ON dcms_pi_setup(location);
CREATE INDEX IF NOT EXISTS idx_device_config_pi_active ON device_config_raspberrypi(is_active);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_meter_readings_recent ON meter_readings(reading_time DESC, location);
"""

# Database Views for Common Queries
CREATE_VIEWS = """
-- View for latest readings per meter
CREATE OR REPLACE VIEW latest_meter_readings AS
SELECT DISTINCT ON (meter_name, location) 
    meter_name, 
    location, 
    reading_time, 
    watts_total, 
    vln_average,
    frequency,
    device_id
FROM meter_readings 
ORDER BY meter_name, location, reading_time DESC;

-- View for daily energy consumption summary
CREATE OR REPLACE VIEW daily_energy_summary AS
SELECT 
    DATE(reading_time) as reading_date,
    location,
    meter_name,
    COUNT(*) as reading_count,
    AVG(watts_total) as avg_power,
    MAX(watts_total) as peak_power,
    MIN(watts_total) as min_power,
    AVG(vln_average) as avg_voltage,
    AVG(frequency) as avg_frequency
FROM meter_readings 
GROUP BY DATE(reading_time), location, meter_name
ORDER BY reading_date DESC;

-- View for Pi device status with latest data
CREATE OR REPLACE VIEW pi_device_status AS
SELECT 
    p.pi_name,
    p.pi_ip,
    p.location,
    p.is_active,
    p.last_connected,
    COUNT(m.id) as meter_count,
    MAX(mr.reading_time) as last_reading_time
FROM dcms_pi_setup p
LEFT JOIN device_config_meterdevice m ON p.id = m.raspberry_pi_id
LEFT JOIN meter_readings mr ON p.location = mr.location
GROUP BY p.id, p.pi_name, p.pi_ip, p.location, p.is_active, p.last_connected;
"""