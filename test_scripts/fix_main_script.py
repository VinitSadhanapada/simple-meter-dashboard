#!/usr/bin/env python3
"""
Direct fix for offline_rpi_dashboard_db.py Pi registration
"""


def update_pi_registration_in_main_script():
    """Update the register_pi_simple function in the main script"""

    script_path = '/home/isha/deepak/MFM_offline_setup/offline_rpi_dashboard_db.py'

    # The correct registration function based on your table structure
    new_function = '''def register_pi_simple(db, pi_name, pi_ip, location):
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
        return None'''

    try:
        # Read the file
        with open(script_path, 'r') as f:
            content = f.read()

        # Find the start and end of the register_pi_simple function
        start_marker = "def register_pi_simple(db, pi_name, pi_ip, location):"
        start_pos = content.find(start_marker)

        if start_pos == -1:
            print("❌ Could not find register_pi_simple function")
            return False

        # Find the end of the function (next function or end of file)
        # Look for the next function definition or end of file
        lines = content[start_pos:].split('\n')
        end_line = 1  # At least include the def line

        for i, line in enumerate(lines[1:], 1):
            if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                # Found start of next function or code block
                end_line = i
                break

        if end_line == 1:
            # Didn't find next function, take everything to end
            end_pos = len(content)
        else:
            end_pos = start_pos + len('\n'.join(lines[:end_line]))

        # Replace the function
        new_content = content[:start_pos] + \
            new_function + '\n\n' + content[end_pos:]

        # Write back to file
        with open(script_path, 'w') as f:
            f.write(new_content)

        print("✅ Updated register_pi_simple function in main script")
        print(
            "📊 Added required fields: config_path, ssh_username, ssh_password, ssh_key_path")

        return True

    except Exception as e:
        print(f"❌ Error updating main script: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Fixing Pi registration in main script...")
    update_pi_registration_in_main_script()
