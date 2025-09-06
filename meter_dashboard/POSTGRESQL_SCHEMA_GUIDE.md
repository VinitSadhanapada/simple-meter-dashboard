# PostgreSQL Schema Commands for meter_readings table

## Quick Commands to Check Schema

### 1. Connect to PostgreSQL
```bash
# Connect to your PostgreSQL database
psql -h localhost -U your_username -d your_database_name

# Or if using Django's dbshell
python3 manage.py dbshell
```

### 2. List All Tables
```sql
-- List all tables in current database
\dt

-- List tables with size information
\dt+

-- List tables matching pattern
\dt meters*
```

### 3. Describe meter_readings Table
```sql
-- Basic table description (Django creates table as meters_meterreading)
\d meters_meterreading

-- Detailed description with indexes and constraints
\d+ meters_meterreading

-- Alternative: Using information_schema
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'meters_meterreading' 
ORDER BY ordinal_position;
```

### 4. Get Table Schema with Column Details
```sql
-- Complete schema information
SELECT 
    column_name,
    data_type,
    CASE 
        WHEN character_maximum_length IS NOT NULL 
        THEN character_maximum_length::text
        WHEN numeric_precision IS NOT NULL 
        THEN numeric_precision::text || ',' || numeric_scale::text
        ELSE ''
    END as length_precision,
    is_nullable,
    column_default,
    ordinal_position
FROM information_schema.columns 
WHERE table_name = 'meters_meterreading' 
AND table_schema = 'public'
ORDER BY ordinal_position;
```

### 5. Get Indexes Information
```sql
-- Show all indexes for the table
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'meters_meterreading';
```

### 6. Get Table Constraints
```sql
-- Show constraints (primary key, foreign key, check, etc.)
SELECT 
    constraint_name,
    constraint_type,
    column_name
FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage ccu 
    ON tc.constraint_name = ccu.constraint_name
WHERE tc.table_name = 'meters_meterreading'
AND tc.table_schema = 'public';
```

### 7. Get Table Size
```sql
-- Get table size information
SELECT 
    pg_size_pretty(pg_total_relation_size('meters_meterreading')) as total_size,
    pg_size_pretty(pg_relation_size('meters_meterreading')) as table_size,
    pg_size_pretty(pg_total_relation_size('meters_meterreading') - pg_relation_size('meters_meterreading')) as index_size;
```

## Expected Schema Based on Your Django Model

Based on your `MeterReading` model, the PostgreSQL table should have these columns:

```sql
-- Expected schema for meters_meterreading table
TABLE meters_meterreading (
    id BIGINT PRIMARY KEY,
    location VARCHAR(100) NOT NULL,
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
```

## Using Django Management Commands

```bash
# Use our custom command to describe the table
python3 manage.py describe_table meterreading

# Show all tables
python3 manage.py describe_table --all

# Get SQL format
python3 manage.py describe_table meterreading --format sql

# Get Django model format
python3 manage.py describe_table meterreading --format django
```

## Sample Data Query
```sql
-- Get sample data to understand the structure
SELECT * FROM meters_meterreading LIMIT 5;

-- Get column statistics
SELECT 
    column_name,
    COUNT(*) as total_rows,
    COUNT(column_name) as non_null_count,
    COUNT(*) - COUNT(column_name) as null_count
FROM information_schema.columns 
CROSS JOIN meters_meterreading
WHERE table_name = 'meters_meterreading'
GROUP BY column_name
ORDER BY column_name;
```

## Quick Schema Update Commands

### Add Index for Performance
```sql
-- Add indexes for commonly queried fields
CREATE INDEX idx_meterreading_device_time ON meters_meterreading(device_id, time);
CREATE INDEX idx_meterreading_location ON meters_meterreading(location);
CREATE INDEX idx_meterreading_time ON meters_meterreading(time);
```

### Add Constraints
```sql
-- Add check constraints for data validation
ALTER TABLE meters_meterreading 
ADD CONSTRAINT check_watts_positive 
CHECK (watts_total >= 0);

ALTER TABLE meters_meterreading 
ADD CONSTRAINT check_frequency_range 
CHECK (frequency BETWEEN 45 AND 65);
```

## Backup Schema
```bash
# Backup only schema
pg_dump -h localhost -U username -d database_name --schema-only -t meters_meterreading > meterreading_schema.sql

# Backup schema and data
pg_dump -h localhost -U username -d database_name -t meters_meterreading > meterreading_full.sql
```
