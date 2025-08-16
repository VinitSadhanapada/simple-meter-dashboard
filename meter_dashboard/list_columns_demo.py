#!/usr/bin/env python3
"""
Demo script showing different ways to list table columns
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/isha/deepak/MFM_offline_setup/meter_dashboard')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')
django.setup()

from device_config.models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment

def list_model_fields(model_class):
    """List all fields of a Django model"""
    print(f"\n=== {model_class.__name__} Model Fields ===")
    
    # Method 1: Using _meta.fields
    print("\n1. Using _meta.fields:")
    for field in model_class._meta.fields:
        print(f"  - {field.name} ({field.__class__.__name__})")
    
    # Method 2: Using _meta.get_fields()
    print("\n2. Using _meta.get_fields():")
    for field in model_class._meta.get_fields():
        print(f"  - {field.name} ({field.__class__.__name__})")
    
    # Method 3: Get field names only
    print("\n3. Field names only:")
    field_names = [field.name for field in model_class._meta.fields]
    print(f"  {field_names}")

def list_database_columns():
    """List columns directly from database"""
    from django.db import connection
    
    print("\n=== Database Table Columns ===")
    
    with connection.cursor() as cursor:
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'device_config_%'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            print(f"\n--- Table: {table_name} ---")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position;
            """, [table_name])
            
            columns = cursor.fetchall()
            for col_name, data_type, is_nullable, default in columns:
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                default_str = f", DEFAULT: {default}" if default else ""
                print(f"  {col_name} ({data_type}) {nullable}{default_str}")

if __name__ == "__main__":
    # List fields for each model
    models = [RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment]
    
    for model in models:
        list_model_fields(model)
    
    # List database columns
    list_database_columns()
