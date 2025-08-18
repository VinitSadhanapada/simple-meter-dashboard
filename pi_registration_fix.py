# Quick inline fix for Pi registration in main script
# Add this to offline_rpi_dashboard_db.py after the imports

def register_pi_with_existing_structure(db, pi_name, pi_ip, location):
    """Register Pi using minimal required fields that exist in table"""

    # Try the most basic insertion with fields that should exist
    try:
        cursor = db.conn.cursor()

        # Basic query with only essential fields + ssh_username (which seems required)
        query = """
        INSERT INTO dcms_pi_setup (pi_name, pi_ip, location, ssh_username, is_active)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (pi_name) 
        DO UPDATE SET 
            pi_ip = EXCLUDED.pi_ip,
            location = EXCLUDED.location,
            is_active = EXCLUDED.is_active
        RETURNING id;
        """

        cursor.execute(query, (pi_name, pi_ip, location, 'pi', True))
        pi_setup_id = cursor.fetchone()[0]
        db.conn.commit()
        return pi_setup_id

    except Exception as e:
        # If that fails, try even more minimal
        try:
            query = """
            INSERT INTO dcms_pi_setup (pi_name, pi_ip, location, ssh_username)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (pi_name) 
            DO UPDATE SET pi_ip = EXCLUDED.pi_ip, location = EXCLUDED.location
            RETURNING id;
            """

            cursor = db.conn.cursor()
            cursor.execute(query, (pi_name, pi_ip, location, 'pi'))
            pi_setup_id = cursor.fetchone()[0]
            db.conn.commit()
            return pi_setup_id

        except Exception as e2:
            print(f"❌ Error registering Pi: {e2}")
            return None
