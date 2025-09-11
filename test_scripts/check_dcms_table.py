#!/usr/bin/env python3
"""
Check dcms_pi_setup table structure and identify required fields
"""
import sys
sys.path.append('/home/isha/deepak/MFM_offline_setup')

def check_dcms_table_structure():
    """Check the existing dcms_pi_setup table structure"""
    
    try:
        from postgres_helper import PostgresHelper
        
        DB_CONFIG = {
            'dbname': 'mfmdb',
            'user': 'mfmuser',
            'password': 'devi',
            'host': 'localhost',
            'port': 5432
        }
        
        print("🔍 Checking dcms_pi_setup table structure...")
        db = PostgresHelper(**DB_CONFIG)
        db.connect()
        
        cursor = db.conn.cursor()
        
        # Get table structure
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'dcms_pi_setup' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ dcms_pi_setup table not found")
            return
        
        print("\n📊 dcms_pi_setup table structure:")
        print(f"{'Column':<25} {'Type':<15} {'Nullable':<10} {'Default':<20}")
        print("-" * 75)
        
        required_fields = []
        for col_name, data_type, nullable, default in columns:
            nullable_str = "YES" if nullable == "YES" else "NO"
            default_str = str(default) if default else "None"
            print(f"{col_name:<25} {data_type:<15} {nullable_str:<10} {default_str:<20}")
            
            if nullable == "NO" and default is None and col_name != 'id':
                required_fields.append(col_name)
        
        print(f"\n🔴 Required fields (NOT NULL, no default): {required_fields}")
        
        # Check existing Pi data to see what fields are typically populated
        cursor.execute("SELECT * FROM dcms_pi_setup LIMIT 3;")
        existing_data = cursor.fetchall()
        
        if existing_data:
            print(f"\n📋 Sample existing data:")
            for i, row in enumerate(existing_data):
                print(f"  Row {i+1}: {dict(zip([col[0] for col in columns], row))}")
        
        db.close()
        
        return required_fields, columns
        
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
        return [], []

if __name__ == "__main__":
    check_dcms_table_structure()