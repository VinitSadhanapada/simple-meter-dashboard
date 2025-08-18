#!/usr/bin/env python3
"""
Add back the missing Pi management functions to the main script
"""


def add_missing_functions():
    """Add the Pi management functions back to the main script"""

    script_path = '/home/isha/deepak/MFM_offline_setup/offline_rpi_dashboard_db.py'

    # The missing functions that need to be added
    missing_functions = '''
# Simple table creation function
def create_pi_setup_table_simple(db):
    """Create dcms_pi_setup table with essential fields only"""
    query = """
    CREATE TABLE IF NOT EXISTS dcms_pi_setup (
        id SERIAL PRIMARY KEY,
        pi_name VARCHAR(100) UNIQUE NOT NULL,
        pi_ip INET UNIQUE NOT NULL,
        location VARCHAR(100) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        last_connected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_dcms_pi_setup_location ON dcms_pi_setup(location);
    """

    try:
        cursor = db.conn.cursor()
        cursor.execute(query)
        db.conn.commit()
        logger.info("✅ dcms_pi_setup table ready")
    except Exception as e:
        logger.error(f"❌ Error creating dcms_pi_setup table: {e}")

def register_pi_simple(db, pi_name, pi_ip, location):
    """Register/update this Pi in the database with all required DCMS fields"""
    
    query = """
    INSERT INTO dcms_pi_setup (
        pi_name, pi_ip, location, ssh_username, ssh_password, 
        ssh_key_path, config_path, is_active, last_connected
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (pi_name) 
    DO UPDATE SET 
        pi_ip = EXCLUDED.pi_ip,
        location = EXCLUDED.location,
        ssh_username = EXCLUDED.ssh_username,
        ssh_password = EXCLUDED.ssh_password,
        ssh_key_path = EXCLUDED.ssh_key_path,
        config_path = EXCLUDED.config_path,
        is_active = EXCLUDED.is_active,
        last_connected = CURRENT_TIMESTAMP
    RETURNING id;
    """

    try:
        cursor = db.conn.cursor()
        
        # Provide all required fields including config_path
        values = (
            pi_name,                                    # pi_name
            pi_ip,                                     # pi_ip  
            location,                                  # location
            'pi',                                      # ssh_username
            '',                                        # ssh_password (empty string)
            '/home/pi/.ssh/id_rsa',                   # ssh_key_path
            '/home/isha/deepak/MFM_offline_setup',    # config_path (required!)
            True                                       # is_active
        )
        
        cursor.execute(query, values)
        pi_setup_id = cursor.fetchone()[0]
        db.conn.commit()
        logger.info(f"✅ Pi registered: {pi_name}")
        return pi_setup_id
        
    except Exception as e:
        logger.error(f"❌ Error registering Pi: {e}")
        return None

def insert_meter_reading_with_pi_simple(db, pi_setup_id, location, device_id, meter_name, reading_time,
                                        model, watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
                                        pf_ave, pf_r_ph, pf_y_ph, pf_b_ph, vln_average, v_r_ph,
                                        v_y_ph, v_b_ph, a_average, a_r_ph, a_y_ph, a_b_ph,
                                        frequency, wh_received, load_hours_delivered,
                                        no_of_interruption, on_hours, v_r_harmonics, v_y_harmonics,
                                        v_b_harmonics, a_r_harmonics, a_y_harmonics, a_b_harmonics):
    """Insert meter reading with Pi setup relationship"""

    # First try to add pi_setup_id column if it doesn't exist
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'meter_readings' AND column_name = 'pi_setup_id') THEN
                    ALTER TABLE meter_readings ADD COLUMN pi_setup_id INTEGER;
                END IF;
            END $$;
        """)
        db.conn.commit()
    except:
        pass  # Column might already exist

    # Insert the reading with pi_setup_id
    query = """
    INSERT INTO meter_readings (
        pi_setup_id, location, device_id, meter_name, reading_time, model,
        watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
        pf_ave, pf_r_ph, pf_y_ph, pf_b_ph,
        vln_average, v_r_ph, v_y_ph, v_b_ph,
        a_average, a_r_ph, a_y_ph, a_b_ph,
        frequency, wh_received, load_hours_delivered, no_of_interruption, on_hours,
        v_r_harmonics, v_y_harmonics, v_b_harmonics,
        a_r_harmonics, a_y_harmonics, a_b_harmonics
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """

    try:
        cursor = db.conn.cursor()
        cursor.execute(query, (
            pi_setup_id, location, device_id, meter_name, reading_time, model,
            watts_total, watts_r_ph, watts_y_ph, watts_b_ph,
            pf_ave, pf_r_ph, pf_y_ph, pf_b_ph,
            vln_average, v_r_ph, v_y_ph, v_b_ph,
            a_average, a_r_ph, a_y_ph, a_b_ph,
            frequency, wh_received, load_hours_delivered, no_of_interruption, on_hours,
            v_r_harmonics, v_y_harmonics, v_b_harmonics,
            a_r_harmonics, a_y_harmonics, a_b_harmonics
        ))
        db.conn.commit()
    except Exception as e:
        logger.error(f"❌ Error inserting meter reading: {e}")
        db.conn.rollback()

def float_or_none(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

def post_to_server(meter_data):
    import requests
    if not SERVER_CONFIG['enabled']:
        # Silently skip if disabled
        return True
    
    try:
        server_data = {k: v for k, v in {
            'device_id': str(meter_data.get("Device_ID", "")),
            'location': meter_data.get("Location", ""),
            'meter_name': meter_data.get("Meter_Name", ""),
            'time': meter_data.get("Time", ""),
            'model': meter_data.get("Model", ""),
            'watts_total': float_or_none(meter_data.get("Watts Total")),
            'watts_r_ph': float_or_none(meter_data.get("Watts R Ph")),
            'watts_y_ph': float_or_none(meter_data.get("Watts Y Ph")),
            'watts_b_ph': float_or_none(meter_data.get("Watts B Ph")),
            'pf_ave': float_or_none(meter_data.get("PF Ave")),
            'pf_r_ph': float_or_none(meter_data.get("PF R Ph")),
            'pf_y_ph': float_or_none(meter_data.get("PF Y Ph")),
            'pf_b_ph': float_or_none(meter_data.get("PF B Ph")),
            'vln_average': float_or_none(meter_data.get("VLN average")),
            'v_r_ph': float_or_none(meter_data.get("V R Ph")),
            'v_y_ph': float_or_none(meter_data.get("V Y Ph")),
            'v_b_ph': float_or_none(meter_data.get("V B Ph")),
            'a_average': float_or_none(meter_data.get("A average")),
            'a_r_ph': float_or_none(meter_data.get("A R Ph")),
            'a_y_ph': float_or_none(meter_data.get("A Y Ph")),
            'a_b_ph': float_or_none(meter_data.get("A B Ph")),
            'frequency': float_or_none(meter_data.get("Frequency")),
            'wh_received': float_or_none(meter_data.get("Wh received")),
            'load_hours_delivered': float_or_none(meter_data.get("Load Hours Delivered")),
            'no_of_interruption': float_or_none(meter_data.get("No of interruption")),
            'on_hours': meter_data.get("On Hours"),
            'v_r_harmonics': float_or_none(meter_data.get("V R Harmonics")),
            'v_y_harmonics': float_or_none(meter_data.get("V Y Harmonics")),
            'v_b_harmonics': float_or_none(meter_data.get("V B Harmonics")),
            'a_r_harmonics': float_or_none(meter_data.get("A R Harmonics")),
            'a_y_harmonics': float_or_none(meter_data.get("A Y Harmonics")),
            'a_b_harmonics': float_or_none(meter_data.get("A B Harmonics"))
        }.items() if v is not None}
        
        # Add server posting logic here if needed
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error posting to server: {e}")
        return False
'''

    try:
        with open(script_path, 'r') as f:
            content = f.read()

        # Find where to insert the functions (before the run_dashboard function)
        lines = content.split('\n')

        # Find run_dashboard function
        run_dashboard_line = None
        for i, line in enumerate(lines):
            if line.strip().startswith('def run_dashboard'):
                run_dashboard_line = i
                break

        if run_dashboard_line is None:
            print("❌ Could not find run_dashboard function")
            return False

        # Insert the missing functions before run_dashboard
        lines.insert(run_dashboard_line, missing_functions)

        # Write back
        with open(script_path, 'w') as f:
            f.write('\n'.join(lines))

        print("✅ Added missing Pi management functions")
        print("📋 Functions added: create_pi_setup_table_simple, register_pi_simple, insert_meter_reading_with_pi_simple")

        return True

    except Exception as e:
        print(f"❌ Error adding missing functions: {e}")
        return False


if __name__ == "__main__":
    add_missing_functions()
