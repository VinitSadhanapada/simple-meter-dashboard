#!/usr/bin/env python3
"""
Generate encryption key for Django field encryption
"""
from cryptography.fernet import Fernet


def generate_key():
    """Generate a new encryption key"""
    key = Fernet.generate_key()
    print("🔐 Generated new encryption key for Django field encryption")
    print("=" * 60)
    print(f"Key: {key.decode()}")
    print("=" * 60)
    print("\n📝 Add this to your .env file:")
    print(f"FIELD_ENCRYPTION_KEY={key.decode()}")
    print("\n⚠️  IMPORTANT: Keep this key secure and backed up!")
    print("   - If you lose this key, encrypted data cannot be recovered")
    print("   - Don't commit this key to version control")
    print("   - Store it securely in your environment configuration")
    return key.decode()


if __name__ == "__main__":
    generate_key()
