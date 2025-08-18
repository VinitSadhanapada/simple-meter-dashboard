#!/usr/bin/env python3
"""
Complete setup for device configuration management system
"""
from pathlib import Path


def update_main_urls():
    """Update main Django URLs to include device config"""

    urls_content = '''
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('meter_readings.urls')),
    path('device-config/', include('device_config.urls')),  # New device config URLs
]
'''

    return urls_content


def create_edit_pi_template():
    """Create edit Pi template (similar to add but with existing data)"""
    return '''
{% extends 'device_config/base.html' %}

{% block title %}Edit Pi Configuration{% endblock %}

{% block content %}
<div class="row">
    <div class="col-lg-8 offset-lg-2">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-edit"></i> Edit Pi Configuration: {{ pi_config.pi_name }}
                </h5>
            </div>
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}
                    
                    <!-- Pi Basic Information -->
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="pi_name" class="form-label">Pi Name *</label>
                                <input type="text" class="form-control" id="pi_name" name="pi_name" value="{{ pi_config.pi_name }}" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="pi_ip" class="form-label">Pi IP Address *</label>
                                <input type="text" class="form-control" id="pi_ip" name="pi_ip" value="{{ pi_config.pi_ip }}" required>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="location" class="form-label">Location *</label>
                                <input type="text" class="form-control" id="location" name="location" value="{{ pi_config.location }}" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="contact_person" class="form-label">Contact Person</label>
                                <input type="text" class="form-control" id="contact_person" name="contact_person" value="{{ pi_config.contact_person|default:'' }}">
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="description" class="form-label">Description</label>
                        <textarea class="form-control" id="description" name="description" rows="2">{{ pi_config.description|default:'' }}</textarea>
                    </div>
                    
                    <!-- SSH Configuration -->
                    <h6 class="border-bottom pb-2 mb-3">SSH Configuration</h6>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="ssh_username" class="form-label">SSH Username</label>
                                <input type="text" class="form-control" id="ssh_username" name="ssh_username" value="{{ pi_config.ssh_username|default:'pi' }}">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="ssh_password" class="form-label">SSH Password</label>
                                <input type="password" class="form-control" id="ssh_password" name="ssh_password" value="{{ pi_config.ssh_password|default:'' }}">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="ssh_key_path" class="form-label">SSH Key Path</label>
                                <input type="text" class="form-control" id="ssh_key_path" name="ssh_key_path" value="{{ pi_config.ssh_key_path|default:'/home/pi/.ssh/id_rsa' }}">
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="config_path" class="form-label">Configuration Path</label>
                        <input type="text" class="form-control" id="config_path" name="config_path" value="{{ pi_config.config_path|default:'/home/pi/MFM_offline_setup' }}">
                    </div>
                    
                    <!-- Pi Status -->
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="is_active" name="is_active" {% if pi_config.is_active %}checked{% endif %}>
                            <label class="form-check-label" for="is_active">
                                Pi is active and should receive deployments
                            </label>
                        </div>
                    </div>
                    
                    <!-- Meter Configurations -->
                    <h6 class="border-bottom pb-2 mb-3">Meter Configurations</h6>
                    <div id="meters-container">
                        {% for meter in pi_config.meters %}
                        <div class="meter-row">
                            <div class="row">
                                <div class="col-md-5">
                                    <div class="mb-3">
                                        <label class="form-label">Meter Name</label>
                                        <input type="text" class="form-control" name="meter_name[]" value="{{ meter.meter_name }}">
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Modbus Address</label>
                                        <input type="number" class="form-control" name="meter_address[]" value="{{ meter.meter_address }}" min="1" max="247">
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Meter Model</label>
                                        <select class="form-select" name="meter_model[]">
                                            <option value="LG6400" {% if meter.meter_model == 'LG6400' %}selected{% endif %}>LG6400</option>
                                            <option value="LG6900" {% if meter.meter_model == 'LG6900' %}selected{% endif %}>LG6900</option>
                                            <option value="LG+5220" {% if meter.meter_model == 'LG+5220' %}selected{% endif %}>LG+5220</option>
                                            <option value="Generic" {% if meter.meter_model == 'Generic' %}selected{% endif %}>Generic</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-1">
                                    <div class="mb-3">
                                        <label class="form-label">&nbsp;</label>
                                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeMeter(this)">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {% empty %}
                        <div class="meter-row">
                            <div class="row">
                                <div class="col-md-5">
                                    <div class="mb-3">
                                        <label class="form-label">Meter Name</label>
                                        <input type="text" class="form-control" name="meter_name[]" placeholder="e.g., Main Meter 01">
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Modbus Address</label>
                                        <input type="number" class="form-control" name="meter_address[]" value="1" min="1" max="247">
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label class="form-label">Meter Model</label>
                                        <select class="form-select" name="meter_model[]">
                                            <option value="LG6400">LG6400</option>
                                            <option value="LG6900">LG6900</option>
                                            <option value="LG+5220">LG+5220</option>
                                            <option value="Generic">Generic</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-1">
                                    <div class="mb-3">
                                        <label class="form-label">&nbsp;</label>
                                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeMeter(this)">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    
                    <div class="mb-3">
                        <button type="button" class="btn btn-outline-secondary" onclick="addMeter()">
                            <i class="fas fa-plus"></i> Add Another Meter
                        </button>
                    </div>
                    
                    <!-- Form Actions -->
                    <div class="d-flex justify-content-between">
                        <a href="{% url 'device_config:device_config' %}" class="btn btn-secondary">
                            <i class="fas fa-arrow-left"></i> Cancel
                        </a>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Update Pi Configuration
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
function addMeter() {
    const container = document.getElementById('meters-container');
    const meterRow = document.createElement('div');
    meterRow.className = 'meter-row';
    meterRow.innerHTML = `
        <div class="row">
            <div class="col-md-5">
                <div class="mb-3">
                    <label class="form-label">Meter Name</label>
                    <input type="text" class="form-control" name="meter_name[]" placeholder="e.g., Main Meter 02">
                </div>
            </div>
            <div class="col-md-3">
                <div class="mb-3">
                    <label class="form-label">Modbus Address</label>
                    <input type="number" class="form-control" name="meter_address[]" value="1" min="1" max="247">
                </div>
            </div>
            <div class="col-md-3">
                <div class="mb-3">
                    <label class="form-label">Meter Model</label>
                    <select class="form-select" name="meter_model[]">
                        <option value="LG6400">LG6400</option>
                        <option value="LG6900">LG6900</option>
                        <option value="LG+5220">LG+5220</option>
                        <option value="Generic">Generic</option>
                    </select>
                </div>
            </div>
            <div class="col-md-1">
                <div class="mb-3">
                    <label class="form-label">&nbsp;</label>
                    <button type="button" class="btn btn-outline-danger d-block" onclick="removeMeter(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    container.appendChild(meterRow);
}

function removeMeter(button) {
    const meterRow = button.closest('.meter-row');
    const container = document.getElementById('meters-container');
    
    if (container.children.length > 1) {
        meterRow.remove();
    } else {
        alert('At least one meter configuration is required');
    }
}
</script>
{% endblock %}
'''


def create_app_init():
    """Create app configuration for device_config"""
    return '''
from django.apps import AppConfig

class DeviceConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'device_config'
    verbose_name = 'Device Configuration Management'
'''


def setup_complete_system():
    """Complete setup of device configuration management system"""

    base_dir = Path('/home/isha/deepak/MFM_offline_setup/meter_dashboard')

    print("🚀 Setting up complete device configuration management system...")

    # 1. Create device_config app
    app_dir = base_dir / 'device_config'
    app_dir.mkdir(exist_ok=True)

    print("📁 Creating app structure...")

    # Create __init__.py
    (app_dir / '__init__.py').touch()

    # Create apps.py
    with open(app_dir / 'apps.py', 'w', encoding='utf-8') as f:
        f.write(create_app_init())

    # 2. Create templates
    template_dir = app_dir / 'templates' / 'device_config'
    template_dir.mkdir(parents=True, exist_ok=True)

    # Create edit_pi.html template
    with open(template_dir / 'edit_pi.html', 'w', encoding='utf-8') as f:
        f.write(create_edit_pi_template())

    print("🎨 Templates created!")

    # 3. Update main URLs
    main_urls_file = base_dir / 'meter_dashboard' / 'urls.py'
    try:
        with open(main_urls_file, 'w', encoding='utf-8') as f:
            f.write(update_main_urls())
        print("🔗 Main URLs updated!")
    except Exception as e:
        print(f"⚠️  Could not update main URLs: {e}")
        print("📝 Please manually add to meter_dashboard/urls.py:")
        print("    path('device-config/', include('device_config.urls')),")

    # 4. Update settings.py to include the new app
    settings_file = base_dir / 'meter_dashboard' / 'settings.py'
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings_content = f.read()

        if "'device_config'," not in settings_content:
            # Add device_config to INSTALLED_APPS
            updated_content = settings_content.replace(
                "'meter_readings',",
                "'meter_readings',\\n    'device_config',"
            )

            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            print("⚙️  Settings updated to include device_config app!")
        else:
            print("✅ device_config already in settings")

    except Exception as e:
        print(f"⚠️  Could not update settings: {e}")
        print("📝 Please manually add 'device_config' to INSTALLED_APPS in settings.py")

    # 5. Install required package
    print("📦 Installing required packages...")
    import subprocess
    try:
        subprocess.run(['pip3', 'install', 'paramiko'], check=True)
        print("✅ paramiko installed for SSH functionality")
    except:
        print("⚠️  Please install paramiko manually: pip3 install paramiko")

    print("""
🎉 Device Configuration Management System Setup Complete!

🔗 Access at: http://localhost:8000/device-config/

📋 Features included:
   ✅ Add/Edit/Delete Pi configurations
   ✅ Manage multiple meters per Pi
   ✅ SSH connection testing
   ✅ Configuration deployment via SSH
   ✅ Modern Bootstrap UI
   ✅ Real-time status monitoring

🚀 Next steps:
   1. Restart Django server: python3 manage.py runserver 0.0.0.0:8000
   2. Navigate to http://localhost:8000/device-config/
   3. Add your first Pi configuration
   4. Deploy config to Pi via SSH

💡 The system will generate device_config.jsonc files and deploy them to your Pis automatically!
    """)


if __name__ == "__main__":
    setup_complete_system()
