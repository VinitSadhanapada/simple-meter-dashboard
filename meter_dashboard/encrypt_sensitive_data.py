#!/usr/bin/env python3
"""
Encrypt existing sensitive data in dcms_pi_setup table
This script will encrypt ssh_password and ssh_key_path fields
"""
from meters.encrypted_fields import encrypt_string, decrypt_string
from django.db import connection
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/isha/deepak/MFM_offline_setup/meter_dashboard')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')
django.setup()


def encrypt_existing_data():
    """Encrypt existing sensitive data in dcms_pi_setup table"""
    print("🔐 Encrypting existing sensitive data in dcms_pi_setup table")

    with connection.cursor() as cursor:
        # Get all records with non-encrypted ssh_password or ssh_key_path
        cursor.execute("""
            SELECT id, ssh_password, ssh_key_path 
            FROM dcms_pi_setup 
            WHERE (ssh_password IS NOT NULL AND ssh_password != '') 
               OR (ssh_key_path IS NOT NULL AND ssh_key_path != '')
        """)

        records = cursor.fetchall()

        if not records:
            print("✅ No data to encrypt or data is already encrypted")
            return

        print(f"📊 Found {len(records)} records to encrypt")

        for record_id, ssh_password, ssh_key_path in records:
            encrypted_password = None
            encrypted_key_path = None

            # Encrypt ssh_password if it exists and doesn't look encrypted
            if ssh_password and not (len(ssh_password) > 50 and '=' in ssh_password):
                print(f"🔒 Encrypting SSH password for record ID {record_id}")
                encrypted_password = encrypt_string(ssh_password)
            else:
                encrypted_password = ssh_password

            # Encrypt ssh_key_path if it exists and doesn't look encrypted
            if ssh_key_path and not (len(ssh_key_path) > 50 and '=' in ssh_key_path):
                print(f"🔑 Encrypting SSH key path for record ID {record_id}")
                encrypted_key_path = encrypt_string(ssh_key_path)
            else:
                encrypted_key_path = ssh_key_path

            # Update the record with encrypted data
            cursor.execute("""
                UPDATE dcms_pi_setup 
                SET ssh_password = %s, ssh_key_path = %s 
                WHERE id = %s
            """, [encrypted_password, encrypted_key_path, record_id])

        print(
            f"✅ Successfully encrypted sensitive data for {len(records)} records")


def verify_encryption():
    """Verify that encryption/decryption works correctly"""
    print("\n🔍 Verifying encryption...")

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, pi_name, ssh_password, ssh_key_path 
            FROM dcms_pi_setup 
            WHERE (ssh_password IS NOT NULL AND ssh_password != '') 
               OR (ssh_key_path IS NOT NULL AND ssh_key_path != '')
            LIMIT 3
        """)

        records = cursor.fetchall()

        for record_id, pi_name, encrypted_password, encrypted_key_path in records:
            print(f"\n📱 Pi Device: {pi_name} (ID: {record_id})")

            if encrypted_password:
                try:
                    decrypted_password = decrypt_string(encrypted_password)
                    print(
                        f"   🔓 Password: {'✅ Decryption successful' if decrypted_password else '❌ Decryption failed'}")
                    print(
                        f"   📝 Encrypted length: {len(encrypted_password)} chars")
                except Exception as e:
                    print(f"   ❌ Password decryption error: {e}")

            if encrypted_key_path:
                try:
                    decrypted_path = decrypt_string(encrypted_key_path)
                    print(
                        f"   🔓 Key path: {'✅ Decryption successful' if decrypted_path else '❌ Decryption failed'}")
                    print(
                        f"   📝 Encrypted length: {len(encrypted_key_path)} chars")
                except Exception as e:
                    print(f"   ❌ Key path decryption error: {e}")


def show_encryption_status():
    """Show current encryption status"""
    print("📊 Current encryption status:")

    with connection.cursor() as cursor:
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM dcms_pi_setup")
        total_records = cursor.fetchone()[0]

        # Count records with passwords
        cursor.execute(
            "SELECT COUNT(*) FROM dcms_pi_setup WHERE ssh_password IS NOT NULL AND ssh_password != ''")
        password_records = cursor.fetchone()[0]

        # Count records with key paths
        cursor.execute(
            "SELECT COUNT(*) FROM dcms_pi_setup WHERE ssh_key_path IS NOT NULL AND ssh_key_path != ''")
        keypath_records = cursor.fetchone()[0]

        # Estimate encrypted records (those with long strings containing '=')
        cursor.execute(
            "SELECT COUNT(*) FROM dcms_pi_setup WHERE ssh_password IS NOT NULL AND LENGTH(ssh_password) > 50 AND ssh_password LIKE '%=%'")
        encrypted_passwords = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM dcms_pi_setup WHERE ssh_key_path IS NOT NULL AND LENGTH(ssh_key_path) > 50 AND ssh_key_path LIKE '%=%'")
        encrypted_keypaths = cursor.fetchone()[0]

        print(f"   📈 Total Pi devices: {total_records}")
        print(f"   🔑 Records with SSH passwords: {password_records}")
        print(f"   🗝️  Records with SSH key paths: {keypath_records}")
        print(f"   🔐 Likely encrypted passwords: {encrypted_passwords}")
        print(f"   🔒 Likely encrypted key paths: {encrypted_keypaths}")


if __name__ == "__main__":
    try:
        show_encryption_status()
        print("\n" + "="*60)

        # Ask for confirmation
        response = input(
            "\n🔐 Do you want to encrypt existing sensitive data? (y/N): ").lower().strip()

        if response in ['y', 'yes']:
            encrypt_existing_data()
            verify_encryption()
            print("\n✅ Encryption process completed!")
        else:
            print("❌ Encryption cancelled")

    except Exception as e:
        print(f"\n❌ Error during encryption: {e}")
        sys.exit(1)
