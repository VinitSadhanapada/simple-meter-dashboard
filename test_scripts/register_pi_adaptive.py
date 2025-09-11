#!/usr/bin/env python3
"""
Adaptive Pi registration that works with existing table structure
"""
import sys
sys.path.append('/home/isha/deepak/MFM_offline_setup')

def get_table_columns(db, table_name):
    """Get the actual columns that exist in the table"""
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = [row[0] for row in cursor.fetchall()]
        return columns
    except Exception as e:
        print(f"❌ Error getting table columns: {e}")
        return []

def register_pi_adaptive(db, pi_name, pi_ip, location):
    """Register Pi using only the columns that actually exist"""
    
    # Get existing columns
    existing_columns = get_table_columns(db, 'dcms_pi_setup')
    print(f"🔍 Existing columns: {existing_columns}")
    
    if not existing_columns:
        print("❌ Could not get table structure")
        return None
    
    # Define all possible field mappings
    field_mappings = {
        'pi_name': pi_name,
        'pi_ip': pi_ip,
        'location': location,
        'is_active': True,
        'ssh_username': 'pi',
        'ssh_key_path': '/home/pi/.ssh/id_rsa',
        'ssh_password': '',
        'description': f'Raspberry Pi at {location}',
        'contact_person': 'System Administrator',
        'installation_date': '2024-01-01',
        'cpu_usage': 0.0,
        'memory_usage': 0.0,
        'disk_usage': 0.0,
        'uptime_hours': 0,
        'connection_status': 'online'
    }
    
    # Filter to only include existing columns (excluding id and auto-generated ones)
    available_fields = {}
    for column in existing_columns:
        if column in field_mappings and column not in ['id', 'created_at', 'updated_at', 'last_connected']:
            available_fields[column] = field_mappings[column]
    
    # Always handle last_connected specially if it exists
    if 'last_connected' in existing_columns:
        available_fields['last_connected'] = 'CURRENT_TIMESTAMP'
    
    print(f"📋 Fields to insert: {list(available_fields.keys())}")
    
    # Build dynamic query
    columns_list = list(available_fields.keys())
    placeholders = []
    values = []
    
    for column in columns_list:
        if column == 'last_connected':
            placeholders.append('CURRENT_TIMESTAMP')
        else:
            placeholders.append('%s')
            values.append(available_fields[column])
    
    columns_str = ', '.join(columns_list)
    placeholders_str = ', '.join(placeholders)
    
    # Build UPDATE SET clause for conflict resolution
    update_fields = []
    for column in columns_list:
        if column not in ['pi_name']:  # Don't update the unique key
            if column == 'last_connected':
                update_fields.append(f"{column} = CURRENT_TIMESTAMP")
            else:
                update_fields.append(f"{column} = EXCLUDED.{column}")
    
    update_str = ', '.join(update_fields)
    
    query = f"""
    INSERT INTO dcms_pi_setup ({columns_str})
    VALUES ({placeholders_str})
    ON CONFLICT (pi_name) 
    DO UPDATE SET {update_str}
    RETURNING id;
    """
    
    print(f"🔧 Generated query: {query}")
    print(f"📊 Values: {values}")
    
    try:
        cursor = db.conn.cursor()
        cursor.execute(query, values)
        pi_setup_id = cursor.fetchone()[0]
        db.conn.commit()
        print(f"✅ Pi registered successfully: {pi_name} (ID: {pi_setup_id})")
        return pi_setup_id
        
    except Exception as e:
        print(f"❌ Error registering Pi: {e}")
        db.conn.rollback()
        return None

# Test the adaptive registration
if __name__ == "__main__":
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
        pi_setup_id = register_pi_adaptive(db, "Test pi 11", "172.20.10.2", "KONDRAI")
        if pi_setup_id:
            print(f"🎉 Successfully registered Pi with ID: {pi_setup_id}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")