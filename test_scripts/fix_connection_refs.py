#!/usr/bin/env python3
"""
Fix script to update connection references in offline_rpi_dashboard_db.py
"""

def fix_connection_references():
    """Replace all db.connection with db.conn in the script"""
    
    script_path = '/home/isha/deepak/MFM_offline_setup/offline_rpi_dashboard_db.py'
    
    try:
        # Read the file
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Replace all instances of db.connection with db.conn
        updated_content = content.replace('db.connection', 'db.conn')
        
        # Write back to file
        with open(script_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ Fixed all db.connection references to db.conn")
        
        # Count replacements made
        original_count = content.count('db.connection')
        print(f"📊 Replaced {original_count} instances")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing connection references: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing PostgresHelper connection references...")
    fix_connection_references()