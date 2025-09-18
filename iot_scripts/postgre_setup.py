import subprocess
import os

 # 1. Install PostgreSQL and contrib from local debs
DEBS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../packages_folder/postgres_debs'))
postgres_debs = [
    'postgresql',
    'postgresql-contrib'
]

def is_deb_installed(pkg):
    result = subprocess.run(['dpkg', '-s', pkg], capture_output=True)
    return result.returncode == 0

def install_postgres_debs():
    need_install = False
    for pkg in postgres_debs:
        if not is_deb_installed(pkg):
            need_install = True
            break
    if need_install:
        deb_files = [os.path.join(DEBS_DIR, f) for f in os.listdir(DEBS_DIR) if f.startswith('postgresql') and f.endswith('.deb')]
        if deb_files:
            print(f"Installing PostgreSQL .deb files from {DEBS_DIR}...")
            result = subprocess.run(['sudo', 'dpkg', '-i'] + deb_files)
            if result.returncode == 0:
                print("✅ PostgreSQL .deb packages installed.")
            else:
                print(f"❌ Error installing PostgreSQL .deb packages: {result.stderr}")
        else:
            print(f"No PostgreSQL .deb files found in {DEBS_DIR}.")
    else:
        print("PostgreSQL already installed. Skipping .deb installation.")

# 2. Start and enable PostgreSQL service

def enable_postgres_service():
    print("Starting and enabling PostgreSQL service...")
    subprocess.run(['sudo', 'systemctl', 'start', 'postgresql'])
    subprocess.run(['sudo', 'systemctl', 'enable', 'postgresql'])
    print("Checking PostgreSQL service status...")
    subprocess.run(['sudo', 'systemctl', 'status', 'postgresql', '--no-pager'])

if __name__ == "__main__":
    install_postgres_debs()
    enable_postgres_service()

    # Automated schema restore and verification
    import shutil
    DUMP_SRC = '/home/pi/Desktop/simple-meter-dashboard/postgresql_schema_dump/mfmdb.dump'
    DUMP_DST = '/tmp/mfmdb.dump'

    # Copy dump file to /tmp
    try:
        shutil.copy(DUMP_SRC, DUMP_DST)
        print(f"✅ Copied dump file to {DUMP_DST}")
    except Exception as e:
        print(f"❌ Failed to copy dump file: {e}")

    # Set permissions
    subprocess.run(['sudo', 'chown', 'postgres:postgres', DUMP_DST])
    subprocess.run(['sudo', 'chmod', '644', DUMP_DST])

    # Create database and user if missing
    subprocess.run(['sudo', '-u', 'postgres', 'psql', '-c', "CREATE DATABASE IF NOT EXISTS mfmdb;"])
    subprocess.run(['sudo', '-u', 'postgres', 'psql', '-c', "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mfmuser') THEN CREATE USER mfmuser WITH ENCRYPTED PASSWORD 'devi'; END IF; END $$;"])
    subprocess.run(['sudo', '-u', 'postgres', 'psql', '-c', "GRANT ALL PRIVILEGES ON DATABASE mfmdb TO mfmuser;"])

    # Restore schema
    print(f"Restoring database schema from {DUMP_DST}...")
    restore_cmd = ['sudo', '-u', 'postgres', 'pg_restore', '-d', 'mfmdb', DUMP_DST]
    result = subprocess.run(restore_cmd)
    if result.returncode == 0:
        print("✅ Database schema restored from mfmdb.dump.")
    else:
        print(f"❌ Error restoring database schema: {result.stderr}")

    # Verify meter_readings table exists
    verify_cmd = ['sudo', '-u', 'postgres', 'psql', '-d', 'mfmdb', '-c', '\dt']
    result = subprocess.run(verify_cmd, capture_output=True, text=True)
    if 'meter_readings' in result.stdout:
        print("✅ meter_readings table exists.")
    else:
        print("❌ meter_readings table not found.")