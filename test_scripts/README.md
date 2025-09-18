# Test Scripts Directory

This directory contains test, debug, and development scripts that are not part of the main application.

## Scripts:
- debug_postgres_helper.py - Debug PostgreSQL connection
- register_pi_*.py - Test Pi registration functions  
- check_dcms_table.py - Check database table structure
- test_postgresql_data.py - Test database connectivity
- migrate_enhanced_tables.py - Database migration scripts
- dcms_integration_guide.py - DCMS integration examples

## Usage:
These scripts are for testing and debugging only. The main application uses:
- offline_rpi_dashboard_db.py (main script)
- config.jsonc (configuration)
- device_config.jsonc (device setup)

## Cleanup:
You can safely delete this entire directory once development is complete.
