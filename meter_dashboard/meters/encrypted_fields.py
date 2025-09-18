#!/usr/bin/env python3
"""
Encrypted field implementation for Django models
Provides encryption for sensitive fields like passwords and SSH keys
"""
import base64
import os
from cryptography.fernet import Fernet
from django.db import models
from django.conf import settings


class EncryptionHelper:
    """Helper class for field-level encryption"""
    
    @staticmethod
    def get_encryption_key():
        """Get or create encryption key"""
        # Try to get key from settings first
        if hasattr(settings, 'FIELD_ENCRYPTION_KEY'):
            return settings.FIELD_ENCRYPTION_KEY.encode()
        
        # Check if key exists in environment
        env_key = os.getenv('FIELD_ENCRYPTION_KEY')
        if env_key:
            return env_key.encode()
        
        # Generate a new key (you should save this securely!)
        key = Fernet.generate_key()
        print(f"⚠️  Generated new encryption key: {key.decode()}")
        print("⚠️  Save this key securely and add it to your .env file:")
        print(f"FIELD_ENCRYPTION_KEY={key.decode()}")
        return key
    
    @staticmethod
    def encrypt_value(value):
        """Encrypt a string value"""
        if not value:
            return value
            
        key = EncryptionHelper.get_encryption_key()
        fernet = Fernet(key)
        encrypted_value = fernet.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted_value).decode()
    
    @staticmethod
    def decrypt_value(encrypted_value):
        """Decrypt a string value"""
        if not encrypted_value:
            return encrypted_value
            
        try:
            key = EncryptionHelper.get_encryption_key()
            fernet = Fernet(key)
            decoded_value = base64.urlsafe_b64decode(encrypted_value.encode())
            return fernet.decrypt(decoded_value).decode()
        except Exception as e:
            print(f"⚠️  Failed to decrypt value: {e}")
            return encrypted_value  # Return as-is if decryption fails


class EncryptedCharField(models.CharField):
    """
    A CharField that automatically encrypts/decrypts its content
    """
    
    def __init__(self, *args, **kwargs):
        # Increase max_length to accommodate encrypted data
        if 'max_length' in kwargs:
            kwargs['max_length'] = kwargs['max_length'] * 2  # Encrypted data is larger
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        """Called when loading data from the database"""
        if value is None:
            return value
        return EncryptionHelper.decrypt_value(value)
    
    def to_python(self, value):
        """Called during deserialization and form processing"""
        if isinstance(value, str) and value:
            # If it looks like encrypted data, decrypt it
            try:
                if len(value) > 50 and '=' in value:  # Likely encrypted
                    return EncryptionHelper.decrypt_value(value)
            except:
                pass
        return value
    
    def get_prep_value(self, value):
        """Called when saving to the database"""
        if value is None or value == '':
            return value
        return EncryptionHelper.encrypt_value(str(value))


class EncryptedTextField(models.TextField):
    """
    A TextField that automatically encrypts/decrypts its content
    """
    
    def from_db_value(self, value, expression, connection):
        """Called when loading data from the database"""
        if value is None:
            return value
        return EncryptionHelper.decrypt_value(value)
    
    def to_python(self, value):
        """Called during deserialization and form processing"""
        if isinstance(value, str) and value:
            # If it looks like encrypted data, decrypt it
            try:
                if len(value) > 50 and '=' in value:  # Likely encrypted
                    return EncryptionHelper.decrypt_value(value)
            except:
                pass
        return value
    
    def get_prep_value(self, value):
        """Called when saving to the database"""
        if value is None or value == '':
            return value
        return EncryptionHelper.encrypt_value(str(value))


# Utility functions for manual encryption/decryption
def encrypt_string(value):
    """Manually encrypt a string"""
    return EncryptionHelper.encrypt_value(value)


def decrypt_string(encrypted_value):
    """Manually decrypt a string"""
    return EncryptionHelper.decrypt_value(encrypted_value)


def generate_encryption_key():
    """Generate a new encryption key"""
    key = Fernet.generate_key()
    print(f"New encryption key: {key.decode()}")
    print("Add this to your .env file:")
    print(f"FIELD_ENCRYPTION_KEY={key.decode()}")
    return key.decode()


if __name__ == "__main__":
    # Test the encryption
    print("🔐 Testing Field Encryption")
    
    test_password = "mySecretPassword123"
    test_key_path = "/home/pi/.ssh/id_rsa"
    
    print(f"Original password: {test_password}")
    encrypted_pwd = encrypt_string(test_password)
    print(f"Encrypted password: {encrypted_pwd}")
    decrypted_pwd = decrypt_string(encrypted_pwd)
    print(f"Decrypted password: {decrypted_pwd}")
    
    print(f"\nOriginal key path: {test_key_path}")
    encrypted_path = encrypt_string(test_key_path)
    print(f"Encrypted key path: {encrypted_path}")
    decrypted_path = decrypt_string(encrypted_path)
    print(f"Decrypted key path: {decrypted_path}")
    
    print(f"\n✅ Encryption test {'PASSED' if test_password == decrypted_pwd else 'FAILED'}")
