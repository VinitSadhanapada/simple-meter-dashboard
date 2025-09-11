#!/usr/bin/env python3
"""
Debug script to check PostgresHelper structure and database connection
"""
import sys
sys.path.append('/home/isha/deepak/MFM_offline_setup')

def debug_postgres_helper():
    try:
        from postgres_helper import PostgresHelper
        
        DB_CONFIG = {
            'dbname': 'mfmdb',
            'user': 'mfmuser',
            'password': 'devi',
            'host': 'localhost',
            'port': 5432
        }
        
        print("🔍 Debugging PostgresHelper...")
        db = PostgresHelper(**DB_CONFIG)
        
        print(f"PostgresHelper attributes: {[attr for attr in dir(db) if not attr.startswith('_')]}")
        
        # Try to connect
        db.connect()
        print("✅ Connection successful")
        
        # Check connection attribute
        if hasattr(db, 'connection'):
            print("✅ Has 'connection' attribute")
            conn = db.connection
        elif hasattr(db, 'conn'):
            print("✅ Has 'conn' attribute")
            conn = db.conn
        elif hasattr(db, 'db'):
            print("✅ Has 'db' attribute") 
            conn = db.db
        else:
            print("❌ No connection attribute found")
            return
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL version: {version}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_postgres_helper()