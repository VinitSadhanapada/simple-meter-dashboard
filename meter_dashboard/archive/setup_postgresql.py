#!/usr/bin/env python3
"""
PostgreSQL Database Setup Helper

This script helps you configure and test your PostgreSQL connection.
"""

import os
import subprocess
import sys


def check_postgresql_installed():
    """Check if PostgreSQL is installed"""
    try:
        result = subprocess.run(['psql', '--version'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ PostgreSQL client not found")
            return False
    except FileNotFoundError:
        print("❌ PostgreSQL client not found")
        return False


def install_postgresql():
    """Install PostgreSQL on Ubuntu/Debian"""
    print("🔧 Installing PostgreSQL...")
    commands = [
        "sudo apt update",
        "sudo apt install -y postgresql postgresql-contrib",
        "sudo systemctl start postgresql",
        "sudo systemctl enable postgresql"
    ]

    for cmd in commands:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error running command: {cmd}")
            print(f"Error: {result.stderr}")
            return False

    print("✅ PostgreSQL installed successfully")
    return True


def create_database():
    """Create the meter_dashboard database"""
    print("🗄️ Creating database...")

    # Commands to run as postgres user
    commands = [
        "sudo -u postgres createdb meter_dashboard",
        "sudo -u postgres psql -c \"CREATE USER meter_user WITH PASSWORD 'meter_password';\""
        "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE meter_dashboard TO meter_user;\""
    ]

    for cmd in commands:
        print(f"Running: {cmd}")
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and "already exists" not in result.stderr:
            print(f"⚠️ Command may have failed: {cmd}")
            print(f"Output: {result.stderr}")


def test_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")

    # Test with psql
    test_cmd = "psql -h localhost -U meter_user -d meter_dashboard -c '\\dt'"
    print(f"Test command: {test_cmd}")
    print("Note: You'll be prompted for the password (meter_password)")


def create_env_file():
    """Create .env file with database settings"""
    env_content = """# PostgreSQL Database Configuration
DB_NAME=meter_dashboard
DB_USER=meter_user
DB_PASSWORD=meter_password
DB_HOST=localhost
DB_PORT=5432

# Django Settings
DEBUG=True
SECRET_KEY=django-insecure-oj5u3*o#et2qytr%ujc&4=yukmyq2473z%%x54^+)j7&w1cw+h
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    print("✅ Created .env file with database configuration")


def main():
    print("🚀 PostgreSQL Database Setup Helper")
    print("=" * 50)

    # Check if PostgreSQL is installed
    if not check_postgresql_installed():
        response = input("PostgreSQL not found. Install it? (y/n): ")
        if response.lower() == 'y':
            if not install_postgresql():
                print("❌ Failed to install PostgreSQL")
                return
        else:
            print("❌ PostgreSQL is required to continue")
            return

    # Create database and user
    response = input("Create database and user? (y/n): ")
    if response.lower() == 'y':
        create_database()

    # Create .env file
    response = input("Create .env file with database settings? (y/n): ")
    if response.lower() == 'y':
        create_env_file()

    print("\n💡 Next Steps:")
    print("1. Update .env file with your PostgreSQL credentials")
    print("2. Test connection: psql -h localhost -U meter_user -d meter_dashboard")
    print("3. Run Django migrations: python3 manage.py migrate")
    print("4. Test Django connection: python3 manage.py dbshell")

    print("\n🔧 Quick Django Commands:")
    print("   python3 manage.py makemigrations")
    print("   python3 manage.py migrate")
    print("   python3 manage.py dbshell")
    print("   python3 manage.py describe_table --all")


if __name__ == "__main__":
    main()
