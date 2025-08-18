#!/usr/bin/env python3
"""
Simple one-time database setup for foreign key relationships
"""
import sys
sys.path.append('/home/isha/deepak/MFM_offline_setup')
from postgres_helper import PostgresHelper

def setup_database():
    """Set up database tables with proper relationships"""
    
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
        
        # Create dcms_pi_setup table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dcms_pi_setup (
                id SERIAL PRIMARY KEY,
                pi_name VARCHAR(100) UNIQUE NOT NULL,
                pi_ip INET UNIQUE NOT NULL,
                location VARCHAR(100) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                last_connected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Add pi_setup_id to meter_readings if it doesn't exist
        cursor.execute("""
            ALTER TABLE meter_readings 
            ADD COLUMN IF NOT EXISTS pi_setup_id INTEGER REFERENCES dcms_pi_setup(id);
        """)
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_meter_readings_pi_setup ON meter_readings(pi_setup_id);
            CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_location ON dcms_pi_setup(location);
        """)
        
        db.connection.commit()
        print("✅ Database setup completed successfully!")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    setup_database()
