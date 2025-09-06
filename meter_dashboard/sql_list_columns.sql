-- SQL Queries to List Table Columns
-- =================================

-- 1. PostgreSQL - List all columns of a specific table
-- Basic column information
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'device_config_raspberrypi'
ORDER BY ordinal_position;

-- Detailed column information with constraints
SELECT 
    c.column_name,
    c.data_type,
    c.character_maximum_length,
    c.is_nullable,
    c.column_default,
    tc.constraint_type
FROM information_schema.columns c
LEFT JOIN information_schema.key_column_usage kcu 
    ON c.table_name = kcu.table_name 
    AND c.column_name = kcu.column_name
LEFT JOIN information_schema.table_constraints tc 
    ON kcu.constraint_name = tc.constraint_name
WHERE c.table_name = 'device_config_raspberrypi'
ORDER BY c.ordinal_position;

-- 2. List all device_config tables and their columns
SELECT 
    t.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public' 
    AND t.table_name LIKE 'device_config_%'
ORDER BY t.table_name, c.ordinal_position;

-- 3. Get column details with size and constraints
SELECT 
    column_name,
    data_type,
    CASE 
        WHEN character_maximum_length IS NOT NULL 
        THEN character_maximum_length::text
        WHEN numeric_precision IS NOT NULL 
        THEN numeric_precision::text || ',' || numeric_scale::text
        ELSE ''
    END AS column_size,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'device_config_meterdevice'
ORDER BY ordinal_position;

-- 4. MySQL - List columns (if you were using MySQL)
-- DESCRIBE table_name;
-- OR
-- SHOW COLUMNS FROM table_name;
-- OR
-- SELECT 
--     COLUMN_NAME,
--     DATA_TYPE,
--     IS_NULLABLE,
--     COLUMN_DEFAULT,
--     COLUMN_KEY
-- FROM INFORMATION_SCHEMA.COLUMNS 
-- WHERE TABLE_NAME = 'your_table_name';

-- 5. SQLite - List columns (if you were using SQLite)
-- PRAGMA table_info(table_name);

-- 6. SQL Server - List columns (if you were using SQL Server)
-- SELECT 
--     COLUMN_NAME,
--     DATA_TYPE,
--     IS_NULLABLE,
--     COLUMN_DEFAULT
-- FROM INFORMATION_SCHEMA.COLUMNS 
-- WHERE TABLE_NAME = 'your_table_name';

-- 7. Oracle - List columns (if you were using Oracle)
-- SELECT 
--     column_name,
--     data_type,
--     nullable,
--     data_default
-- FROM user_tab_columns 
-- WHERE table_name = 'YOUR_TABLE_NAME';

-- 8. PostgreSQL - List all tables in current schema
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 9. PostgreSQL - Get table and column count
SELECT 
    table_name,
    COUNT(*) as column_count
FROM information_schema.columns 
WHERE table_schema = 'public' 
    AND table_name LIKE 'device_config_%'
GROUP BY table_name
ORDER BY table_name;
