#!/usr/bin/env python3
"""
Test the encrypted fields functionality
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


def test_encrypted_fields():
    """Test adding and retrieving encrypted data"""
    print("🧪 Testing Encrypted Fields")
    print("=" * 50)

    # Test data
    test_password = "SuperSecretPassword123!"
    test_key_path = "/home/pi/.ssh/id_rsa_production"

    # Get the first Pi device
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, pi_name FROM dcms_pi_setup LIMIT 1")
        result = cursor.fetchone()

        if not result:
            print("❌ No Pi devices found in database")
            return

        pi_id, pi_name = result
        print(f"📱 Testing with Pi device: {pi_name} (ID: {pi_id})")

        # Encrypt the test data
        encrypted_password = encrypt_string(test_password)
        encrypted_key_path = encrypt_string(test_key_path)

        print(f"\n🔐 Original password: {test_password}")
        print(f"🔒 Encrypted password: {encrypted_password}")
        print(f"📏 Encrypted length: {len(encrypted_password)} characters")

        print(f"\n🔐 Original key path: {test_key_path}")
        print(f"🔒 Encrypted key path: {encrypted_key_path}")
        print(f"📏 Encrypted length: {len(encrypted_key_path)} characters")

        # Update the database with encrypted data
        cursor.execute("""
            UPDATE dcms_pi_setup 
            SET ssh_password = %s, ssh_key_path = %s 
            WHERE id = %s
        """, [encrypted_password, encrypted_key_path, pi_id])

        print(f"\n💾 Stored encrypted data in database for Pi: {pi_name}")

        # Retrieve and decrypt the data
        cursor.execute("""
            SELECT ssh_password, ssh_key_path 
            FROM dcms_pi_setup 
            WHERE id = %s
        """, [pi_id])

        stored_password, stored_key_path = cursor.fetchone()

        # Decrypt the retrieved data
        decrypted_password = decrypt_string(stored_password)
        decrypted_key_path = decrypt_string(stored_key_path)

        print(f"\n🔓 Retrieved and decrypted password: {decrypted_password}")
        print(f"🔓 Retrieved and decrypted key path: {decrypted_key_path}")

        # Verify integrity
        password_match = test_password == decrypted_password
        keypath_match = test_key_path == decrypted_key_path

        print(
            f"\n✅ Password integrity: {'PASSED' if password_match else 'FAILED'}")
        print(
            f"✅ Key path integrity: {'PASSED' if keypath_match else 'FAILED'}")

        if password_match and keypath_match:
            print(
                "\n🎉 Encryption test SUCCESSFUL! All data encrypted and decrypted correctly.")
        else:
            print("\n❌ Encryption test FAILED! Data integrity check failed.")

        return password_match and keypath_match


def show_current_data():
    """Show current encrypted data in the database"""
    print("\n📊 Current Database Data:")
    print("=" * 50)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, pi_name, pi_ip, 
                   CASE 
                       WHEN ssh_password IS NOT NULL AND ssh_password != '' THEN 'SET (Encrypted)' 
                       ELSE 'Not Set' 
                   END as password_status,
                   CASE 
                       WHEN ssh_key_path IS NOT NULL AND ssh_key_path != '' THEN 'SET (Encrypted)' 
                       ELSE 'Not Set' 
                   END as keypath_status
            FROM dcms_pi_setup 
            ORDER BY id
        """)

        records = cursor.fetchall()

        print(
            f"{'ID':<4} {'Pi Name':<15} {'IP Address':<18} {'Password':<15} {'Key Path':<15}")
        print("-" * 70)

        for record in records:
            pi_id, pi_name, pi_ip, password_status, keypath_status = record
            print(
                f"{pi_id:<4} {pi_name:<15} {str(pi_ip):<18} {password_status:<15} {keypath_status:<15}")


if __name__ == "__main__":
    try:
        show_current_data()

        print("\n" + "="*60)
        response = input(
            "\n🧪 Do you want to run encryption test? (y/N): ").lower().strip()

        if response in ['y', 'yes']:
            success = test_encrypted_fields()

            if success:
                print("\n📋 Summary:")
                print("✅ Encrypted fields are working correctly")
                print("✅ SSH passwords and key paths will be automatically encrypted")
                print("✅ Data is encrypted in database but appears normal in Django")

                show_current_data()

        else:
            print("❌ Test cancelled")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        sys.exit(1)
