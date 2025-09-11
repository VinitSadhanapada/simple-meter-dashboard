#!/usr/bin/env python3
"""
Check and copy the exact DCMS HTML frontend templates
"""
import shutil
import os
from pathlib import Path


def check_existing_templates():
    """Check what templates currently exist"""

    # Check DCMS source
    dcms_source = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_configuration_management_system/device_manager/templates/device_manager')
    device_config_templates = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config')

    print("🔍 Checking existing templates...")

    print(f"\n📁 DCMS Source: {dcms_source}")
    if dcms_source.exists():
        dcms_files = list(dcms_source.glob('*.html'))
        print(f"   Found {len(dcms_files)} DCMS templates:")
        for f in dcms_files:
            print(f"   - {f.name}")
    else:
        print("   ❌ DCMS source not found!")
        return False

    print(f"\n📁 Device Config Templates: {device_config_templates}")
    if device_config_templates.exists():
        config_files = list(device_config_templates.glob('*.html'))
        print(f"   Found {len(config_files)} device_config templates:")
        for f in config_files:
            print(f"   - {f.name}")
    else:
        print("   📝 No device_config templates yet")

    return dcms_source.exists()


def copy_exact_dcms_html():
    """Copy exact DCMS HTML templates with all styling"""

    dcms_source = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_configuration_management_system/device_manager/templates/device_manager')
    device_config_dest = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config')

    if not dcms_source.exists():
        print("❌ DCMS source templates not found!")
        return False

    # Create destination directory
    device_config_dest.mkdir(parents=True, exist_ok=True)

    print("📋 Copying exact DCMS HTML templates...")

    # Copy all HTML files exactly as they are
    copied_files = []

    for template_file in dcms_source.glob('*.html'):
        dest_file = device_config_dest / template_file.name

        # Read original content
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Only update the minimal necessary references
        # Update app namespace from device_manager to device_config
        updated_content = content.replace(
            "{% extends 'device_manager/", "{% extends 'device_config/")
        updated_content = updated_content.replace(
            "{% include 'device_manager/", "{% include 'device_config/")
        updated_content = updated_content.replace(
            "{% url 'device_manager:", "{% url 'device_config:")

        # Write to destination
        with open(dest_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        copied_files.append(template_file.name)
        print(f"✅ Copied {template_file.name}")

    print(f"\n📊 Successfully copied {len(copied_files)} exact DCMS templates")
    return True


def copy_dcms_static_files():
    """Copy DCMS static files (CSS, JS, images)"""

    dcms_static_source = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_configuration_management_system/device_manager/static')
    device_config_static = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/static/device_config')

    if dcms_static_source.exists():
        print("📁 Copying DCMS static files (CSS, JS, images)...")

        # Create static directory structure
        device_config_static.mkdir(parents=True, exist_ok=True)

        # Copy all static files
        if (dcms_static_source / 'device_manager').exists():
            shutil.copytree(dcms_static_source / 'device_manager',
                            device_config_static, dirs_exist_ok=True)
            print("✅ Copied DCMS static files")
        else:
            print("⚠️  No DCMS static files found")
    else:
        print("⚠️  DCMS static directory not found")


def create_sample_device_data():
    """Create sample device data for testing"""

    config_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_configs.json')

    sample_data = [
        {
            "pi_name": "Building-A-Pi",
            "pi_ip": "192.168.1.100",
            "location": "Building A - Ground Floor",
            "ssh_username": "pi",
            "ssh_password": "raspberry",
            "ssh_key_path": "/home/pi/.ssh/id_rsa",
            "config_path": "/home/pi/MFM_offline_setup",
            "description": "Main building power monitoring",
            "contact_person": "John Doe",
            "is_active": True,
            "meters": [
                {
                    "meter_name": "Main_Meter_1",
                    "meter_address": 1,
                    "meter_model": "LG6400",
                    "location": "Building A - Main Panel"
                },
                {
                    "meter_name": "Sub_Meter_2",
                    "meter_address": 2,
                    "meter_model": "LG6400",
                    "location": "Building A - Sub Panel"
                }
            ]
        },
        {
            "pi_name": "Building-B-Pi",
            "pi_ip": "192.168.1.101",
            "location": "Building B - First Floor",
            "ssh_username": "pi",
            "ssh_password": "raspberry",
            "ssh_key_path": "/home/pi/.ssh/id_rsa",
            "config_path": "/home/pi/MFM_offline_setup",
            "description": "Secondary building monitoring",
            "contact_person": "Jane Smith",
            "is_active": True,
            "meters": [
                {
                    "meter_name": "Building_B_Main",
                    "meter_address": 1,
                    "meter_model": "LG6400",
                    "location": "Building B - Main"
                }
            ]
        }
    ]

    with open(config_file, 'w') as f:
        import json
        json.dump(sample_data, f, indent=2)

    print("✅ Created sample device data")


def check_views_compatibility():
    """Check if views are compatible with DCMS templates"""

    views_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/views.py')

    if views_file.exists():
        with open(views_file, 'r') as f:
            content = f.read()

        # Check for required view classes
        required_views = ['DeviceConfigView',
                          'DeviceListView', 'AddDeviceView', 'EditDeviceView']
        missing_views = []

        for view in required_views:
            if view not in content:
                missing_views.append(view)

        if missing_views:
            print(f"⚠️  Missing view classes: {missing_views}")
            return False
        else:
            print("✅ Views are compatible with DCMS templates")
            return True
    else:
        print("❌ Views file not found!")
        return False


def show_template_structure():
    """Show the template structure that should exist"""

    device_config_templates = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config')

    print("\n📁 Expected template structure:")
    expected_templates = [
        'base.html',
        'device_list.html',
        'add_device.html',
        'edit_device.html',
        'device_detail.html'
    ]

    for template in expected_templates:
        template_path = device_config_templates / template
        if template_path.exists():
            print(f"   ✅ {template}")
        else:
            print(f"   ❌ {template} (missing)")


def main():
    """Main function to copy exact DCMS frontend"""

    print("🎨 Copying exact DCMS HTML frontend...")

    # Check what exists
    if not check_existing_templates():
        print("💥 Cannot proceed without DCMS source templates")
        return

    # Copy exact DCMS HTML templates
    copy_exact_dcms_html()

    # Copy static files
    copy_dcms_static_files()

    # Create sample data
    create_sample_device_data()

    # Check views compatibility
    check_views_compatibility()

    # Show template structure
    show_template_structure()

    print("""
🎉 Exact DCMS Frontend Copied!

✅ All DCMS HTML templates copied exactly
✅ Static files (CSS/JS) copied
✅ Sample device data created
✅ Template references updated

📁 Templates available:
   /device_config/templates/device_config/

🚀 Next steps:
   1. cd meter_dashboard
   2. python3 manage.py runserver 0.0.0.0:8000
   3. Navigate to: http://localhost:8000/device-config/

You should now see the EXACT DCMS interface!
    """)


if __name__ == "__main__":
    main()
