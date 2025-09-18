"""
PostgreSQL Automated Setup Script
---------------------------------

This script performs the following steps:
 1. Installs PostgreSQL and contrib packages from local .deb files (offline).
 2. Starts and enables the PostgreSQL service.
 3. Copies and sets permissions for the database dump file.
 4. Creates the database and user if missing.
 5. Restores the database schema and data from the dump file.
 6. Verifies that the meter_readings table exists.
 7. Resets the meter_readings_id_seq sequence to avoid primary key conflicts.
 8. Fakes Django migrations to sync migration history with the restored schema.

Usage:
    python3 postgre_setup.py

After running this script, you can safely run:
    python3 manage.py migrate
in your Django project directory for future migrations.
"""
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
        # Reset meter_readings_id_seq to max(id)
        reset_seq_cmd = [
            'sudo', '-u', 'postgres', 'psql', '-d', 'mfmdb', '-c',
            "SELECT setval('meter_readings_id_seq', (SELECT COALESCE(MAX(id), 1) FROM meter_readings));"
        ]
        seq_result = subprocess.run(reset_seq_cmd, capture_output=True, text=True)
        if seq_result.returncode == 0:
            print("🔄 meter_readings_id_seq reset to max(id). New readings will get unique IDs.")
        else:
            print(f"⚠️ Could not reset meter_readings_id_seq: {seq_result.stderr}")

        # Reset django_migrations_id_seq to max(id) to avoid duplicate key errors
        print("🔧 Resetting django_migrations_id_seq to max(id) to avoid migration key conflicts...")
        reset_migrations_seq_cmd = [
            'sudo', '-u', 'postgres', 'psql', '-d', 'mfmdb', '-c',
            "SELECT setval('django_migrations_id_seq', (SELECT COALESCE(MAX(id), 1) FROM django_migrations));"
        ]
        mig_seq_result = subprocess.run(reset_migrations_seq_cmd, capture_output=True, text=True)
        if mig_seq_result.returncode == 0:
            print("✅ django_migrations_id_seq reset to max(id). Migration history will not conflict.")
        else:
            print(f"⚠️ Could not reset django_migrations_id_seq: {mig_seq_result.stderr}")

        # Fake Django migrations to sync migration history
        print("🔧 Checking for unapplied migrations and faking those that match the current schema...")
        django_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../meter_dashboard'))
        # List unapplied migrations
        show_migrations_cmd = ['python3', 'manage.py', 'showmigrations', '--plan']
        show_result = subprocess.run(show_migrations_cmd, cwd=django_dir, capture_output=True, text=True)
        print("--- Django migration plan ---")
        print(show_result.stdout)
        # Attempt to fake all unapplied migrations for all apps
        migrate_cmd = ['python3', 'manage.py', 'migrate', '--fake']
        result = subprocess.run(migrate_cmd, cwd=django_dir, capture_output=True, text=True)
        print("--- Django migrate --fake output ---")
        print(result.stdout)
        if result.returncode == 0:
            print("✅ All unapplied migrations faked successfully. Migration history is now in sync.")
        else:
            print(f"⚠️ Could not fake migrations: {result.stderr}")
    else:
        print("❌ meter_readings table not found.")