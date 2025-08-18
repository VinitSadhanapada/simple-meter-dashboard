#!/usr/bin/env python3
"""
Enhanced Pi registration function with all DCMS required fields
"""

def register_pi_enhanced(db, pi_name, pi_ip, location):
    """Register/update this Pi in the database with all required DCMS fields"""
    
    # First try with all possible fields
    full_query = """
    INSERT INTO dcms_pi_setup (
        pi_name, pi_ip, location, is_active, last_connected,
        ssh_username, ssh_key_path, ssh_password,
        description, contact_person, installation_date,
        cpu_usage, memory_usage, disk_usage, uptime_hours, connection_status
    )
    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (pi_name) 
    DO UPDATE SET 
        pi_ip = EXCLUDED.pi_ip,
        location = EXCLUDED.location,
        is_active = EXCLUDED.is_active,
        last_connected = CURRENT_TIMESTAMP,
        connection_status = EXCLUDED.connection_status
    RETURNING id;
    """

    try:
        cursor = db.conn.cursor()
        
        # Prepare values with defaults for all potential fields
        values = (
            pi_name,                           # pi_name
            pi_ip,                            # pi_ip  
            location,                         # location
            True,                             # is_active
            'pi',                             # ssh_username (default)
            '/home/pi/.ssh/id_rsa',          # ssh_key_path (default)
            '',                               # ssh_password (empty string)
            f'Raspberry Pi at {location}',    # description
            'System Administrator',           # contact_person
            '2024-01-01',                     # installation_date
            0.0,                              # cpu_usage
            0.0,                              # memory_usage  
            0.0,                              # disk_usage
            0,                                # uptime_hours
            'online'                          # connection_status
        )
        
        cursor.execute(full_query, values)
        pi_setup_id = cursor.fetchone()[0]
        db.conn.commit()
        print(f"✅ Pi registered with full fields: {pi_name}")
        return pi_setup_id
        
    except Exception as e:
        print(f"⚠️  Full registration failed: {e}")
        
        # Try with minimal required fields
        try:
            minimal_query = """
            INSERT INTO dcms_pi_setup (pi_name, pi_ip, location, ssh_username)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (pi_name) 
            DO UPDATE SET 
                pi_ip = EXCLUDED.pi_ip,
                location = EXCLUDED.location,
                last_connected = CURRENT_TIMESTAMP
            RETURNING id;
            """
            
            cursor = db.conn.cursor()
            cursor.execute(minimal_query, (pi_name, pi_ip, location, 'pi'))
            pi_setup_id = cursor.fetchone()[0]
            db.conn.commit()
            print(f"✅ Pi registered (minimal): {pi_name}")
            return pi_setup_id
            
        except Exception as e2:
            print(f"❌ Error registering Pi: {e2}")
            return None

# Test the enhanced registration
if __name__ == "__main__":
    import sys
    sys.path.append('/home/isha/deepak/MFM_offline_setup')
    
    from postgres_helper import PostgresHelper
    
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
        
        # Test Pi registration
        pi_setup_id = register_pi_enhanced(db, "Test pi 11", "172.20.10.2", "KONDRAI")
        if pi_setup_id:
            print(f"🎉 Successfully registered Pi with ID: {pi_setup_id}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")