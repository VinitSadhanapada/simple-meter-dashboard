#!/usr/bin/env python3
"""
Quick superuser creation script for the meter dashboard
"""
from django.contrib.auth.models import User
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/isha/deepak/MFM_offline_setup/meter_dashboard')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')
django.setup()


def create_superuser():
    """Create a default superuser if none exists"""

    # Check if any superuser exists
    if User.objects.filter(is_superuser=True).exists():
        print("✅ Superuser already exists!")
        superusers = User.objects.filter(is_superuser=True)
        for user in superusers:
            print(f"   👤 Username: {user.username}, Email: {user.email}")
        return

    # Create default superuser
    try:
        user = User.objects.create_superuser(
            username='admin',
            email='admin@meter-dashboard.local',
            password='admin123'  # Change this in production!
        )

        print("🎉 Superuser created successfully!")
        print(f"   👤 Username: {user.username}")
        print(f"   📧 Email: {user.email}")
        print(f"   🔑 Password: admin123")
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        print("   You can change it in Django admin or using:")
        print("   python3 manage.py changepassword admin")

    except Exception as e:
        print(f"❌ Error creating superuser: {e}")


if __name__ == "__main__":
    create_superuser()
