#!/usr/bin/env python3
"""
Check where device data is stored and what fields are included
"""
from pathlib import Path
import json


def check_device_storage():
    """Check where device data is being stored"""

    # Check if JSON file exists
    config_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_configs.json')

    print("🔍 DEVICE DATA STORAGE ANALYSIS:")
    print("=" * 50)

    if config_file.exists():
        print(f"📁 Storage Location: {config_file}")
        print("📊 Storage Type: JSON FILE (not database)")

        try:
            with open(config_file, 'r') as f:
                data = json.load(f)

            print(f"\n📈 Total Devices: {len(data)}")

            if data:
                print("\n🏷️  FIELDS BEING STORED:")
                first_device = data[0]
                for field, value in first_device.items():
                    print(f"   • {field}: {type(value).__name__}")

                print(f"\n📄 SAMPLE DEVICE DATA:")
                print(json.dumps(first_device, indent=2))
            else:
                print("\n📭 No devices configured yet")

        except Exception as e:
            print(f"❌ Error reading file: {e}")
    else:
        print("📁 Storage Location: FILE NOT FOUND")
        print("📊 Storage Type: JSON FILE (will be created on first device)")


def show_field_mapping():
    """Show what each field is used for"""

    print(f"\n🏷️  FIELD PURPOSES:")
    print("=" * 50)

    fields = {
        "pi_name": "Device identifier/name (REQUIRED)",
        "pi_ip": "IP address for SSH connection (REQUIRED)",
        "location": "Physical location description",
        "ssh_username": "SSH login username (default: pi)",
        "ssh_password": "SSH password (optional if using key)",
        "ssh_key_path": "Path to SSH private key",
        "config_path": "Target path for deployment",
        "description": "Optional device description",
        "contact_person": "Person responsible for device",
        "is_active": "Whether device should receive deployments",
        "meters": "List of meter configurations"
    }

    for field, purpose in fields.items():
        print(f"   • {field:15} → {purpose}")


def check_database_tables():
    """Check if there are any database tables for devices"""

    print(f"\n🗄️  DATABASE TABLE CHECK:")
    print("=" * 50)

    # Check if there's a models.py with device models
    models_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/models.py')

    if models_file.exists():
        with open(models_file, 'r') as f:
            content = f.read()

        if 'class' in content and 'Model' in content:
            print("📋 Django models found in models.py:")
            # Extract model classes
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith('class ') and 'Model' in line:
                    print(f"   • {line.strip()}")
        else:
            print("📋 No Django models found - using JSON storage")
    else:
        print("📋 No models.py file - using JSON storage")

    # Check migrations
    migrations_dir = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/migrations')
    if migrations_dir.exists():
        migrations = list(migrations_dir.glob('*.py'))
        migrations = [m for m in migrations if m.name != '__init__.py']
        print(f"📄 Migrations found: {len(migrations)}")
        for migration in migrations:
            print(f"   • {migration.name}")
    else:
        print("📄 No migrations directory - no database tables")


def show_why_extra_fields():
    """Explain why there are extra fields"""

    print(f"\n❓ WHY EXTRA FIELDS:")
    print("=" * 50)
    print("""
The add-pi form includes extra fields because:

1. 🎯 COMPREHENSIVE DEVICE MANAGEMENT:
   • Contact Person: Who to contact for device issues
   • Description: What this device is used for
   • Location: Where the device is physically located

2. 🔧 OPERATIONAL REQUIREMENTS:
   • Better tracking of device purposes
   • Contact information for maintenance
   • Documentation for device management

3. 📊 DCMS COMPATIBILITY:
   • Fields match original DCMS system
   • Maintains same level of detail
   • Professional device management

4. 🚀 DEPLOYMENT TRACKING:
   • Description helps identify device purpose
   • Location helps with physical access
   • Contact helps with troubleshooting
    """)


def create_minimal_form():
    """Create a minimal form with only essential fields"""

    minimal_template = '''{% extends 'device_config/base.html' %}

{% block title %}Add Device - Minimal{% endblock %}

{% block content %}
<div class="container">
    <div class="row justify-content-center">
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-plus"></i> Add Device (Minimal)</h5>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        
                        <!-- Essential Fields Only -->
                        <div class="mb-3">
                            <label for="pi_name" class="form-label">Device Name *</label>
                            <input type="text" class="form-control" id="pi_name" name="pi_name" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="pi_ip" class="form-label">IP Address *</label>
                            <input type="text" class="form-control" id="pi_ip" name="pi_ip" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="ssh_username" class="form-label">SSH Username</label>
                            <input type="text" class="form-control" id="ssh_username" name="ssh_username" value="pi">
                        </div>
                        
                        <div class="mb-3">
                            <label for="ssh_password" class="form-label">SSH Password</label>
                            <input type="password" class="form-control" id="ssh_password" name="ssh_password">
                        </div>
                        
                        <!-- Single Meter -->
                        <h6 class="border-bottom pb-2 mb-3">Meter Configuration</h6>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Meter Name</label>
                                    <input type="text" class="form-control" name="meter_name[]" value="Main_Meter_1">
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Address</label>
                                    <input type="number" class="form-control" name="meter_address[]" value="1">
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Model</label>
                                    <select class="form-select" name="meter_model[]">
                                        <option value="LG6400">LG6400</option>
                                        <option value="LG6320">LG6320</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Hidden fields with defaults -->
                        <input type="hidden" name="location" value="Not specified">
                        <input type="hidden" name="contact_person" value="">
                        <input type="hidden" name="description" value="">
                        <input type="hidden" name="ssh_key_path" value="/home/pi/.ssh/id_rsa">
                        <input type="hidden" name="config_path" value="/home/pi/MFM_offline_setup">
                        <input type="hidden" name="is_active" value="on">
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Save Device
                            </button>
                            <a href="{% url 'device_config:device_list' %}" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

    minimal_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config/add_device_minimal.html')

    with open(minimal_file, 'w', encoding='utf-8') as f:
        f.write(minimal_template)

    print("✅ Created minimal add device form")
    print(f"📁 Location: {minimal_file}")


def main():
    """Analyze device storage and fields"""

    print("🔍 DEVICE FIELD AND STORAGE ANALYSIS")
    print("=" * 60)

    # Check where data is stored
    check_device_storage()

    # Show field purposes
    show_field_mapping()

    # Check database tables
    check_database_tables()

    # Explain why extra fields
    show_why_extra_fields()

    # Create minimal form option
    create_minimal_form()

    print(f"\n💡 SUMMARY:")
    print("=" * 50)
    print("• Data stored in: JSON FILE (not database)")
    print("• Location: /home/isha/deepak/MFM_offline_setup/meter_dashboard/device_configs.json")
    print("• Extra fields: For better device management")
    print("• Minimal form: Created for simple device addition")
    print("\n🔗 Access minimal form: http://0.0.0.0:8000/device-config/add/ (only essential fields)")


if __name__ == "__main__":
    main()
