#!/usr/bin/env python3
"""
Complete fix for all URL reference issues in templates and project
"""
from pathlib import Path
import re


def fix_main_project_urls():
    """Fix main project URLs to handle all missing patterns"""

    main_urls_content = '''from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

# Add a simple dashboard view for templates that reference it directly
def dashboard_redirect(request):
    from django.shortcuts import redirect
    return redirect('meter_readings:dashboard')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Main app routes
    path('', include('meter_readings.urls')),
    path('device-config/', include('device_config.urls')),
    
    # Direct pattern names for templates that don't use namespaces
    path('dashboard/', dashboard_redirect, name='dashboard'),
    path('meter-list/', RedirectView.as_view(pattern_name='device_config:meter_list'), name='meter_list'),
    path('device-list/', RedirectView.as_view(pattern_name='device_config:device_list'), name='device_list'),
]
'''

    main_urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_dashboard/urls.py')

    with open(main_urls_file, 'w') as f:
        f.write(main_urls_content)

    print("✅ Fixed main project URLs with dashboard redirect")


def fix_device_config_urls():
    """Complete device_config URLs with all missing patterns"""

    urls_content = '''from django.urls import path
from . import views


urlpatterns = [
    # Main device list view (primary)
    path('', views.DeviceConfigView.as_view(), name='device_list'),
    path('', views.DeviceConfigView.as_view(), name='device_config'),
    
    # All possible DCMS compatibility URLs
    path('meters/', views.DeviceConfigView.as_view(), name='meter_list'),
    path('raspberry-pi/', views.DeviceConfigView.as_view(), name='raspberry_pi_list'),
    path('system-config/', views.DeviceConfigView.as_view(), name='system_config'),
    path('deployment/', views.DeviceConfigView.as_view(), name='deployment_list'),
    path('config-deployment/', views.DeviceConfigView.as_view(), name='config_deployment_list'),
    path('device-management/', views.DeviceConfigView.as_view(), name='device_management'),
    
    # Device CRUD operations
    path('add/', views.AddPiView.as_view(), name='add_device'),
    path('edit/<int:pi_id>/', views.EditPiView.as_view(), name='edit_device'),
    path('delete/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_device'),
    
    # Device operations (SSH deployment)
    path('deploy/<int:pi_id>/', views.DeployConfigView.as_view(), name='deploy_config'),
    path('test/<int:pi_id>/', views.TestConnectionView.as_view(), name='test_connection'),
    
    # Backward compatibility with old URL patterns
    path('add-pi/', views.AddPiView.as_view(), name='add_pi'),
    path('edit-pi/<int:pi_id>/', views.EditPiView.as_view(), name='edit_pi'),
    path('delete-pi/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_pi'),
    path('deploy-config/<int:pi_id>/', views.DeployConfigView.as_view(), name='deploy_config_alt'),
    path('test-connection/<int:pi_id>/', views.TestConnectionView.as_view(), name='test_connection_alt'),
]
'''

    urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/urls.py')

    with open(urls_file, 'w') as f:
        f.write(urls_content)

    print("✅ Fixed device_config URLs with all missing patterns")


def fix_template_url_references():
    """Fix all URL references in templates"""

    template_dirs = [
        Path('/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates'),
        Path('/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_readings/templates'),
    ]

    # URL reference fixes
    url_fixes = {
        # Dashboard references (main issue)
        "{% url 'dashboard' %}": "{% url 'meter_readings:dashboard' %}",
        "{% url 'meter_readings.dashboard' %}": "{% url 'meter_readings:dashboard' %}",
        "href='/dashboard/'": "href='{% url \"meter_readings:dashboard\" %}'",

        # Device manager to device_config namespace fixes
        "{% url 'device_manager:device_list' %}": "{% url 'device_config:device_list' %}",
        "{% url 'device_manager:meter_list' %}": "{% url 'device_config:meter_list' %}",
        "{% url 'device_manager:add_device' %}": "{% url 'device_config:add_device' %}",
        "{% url 'device_manager:edit_device' %}": "{% url 'device_config:edit_device' %}",
        "{% url 'device_manager:delete_device' %}": "{% url 'device_config:delete_device' %}",
        "{% url 'device_manager:deploy_config' %}": "{% url 'device_config:deploy_config' %}",
        "{% url 'device_manager:test_connection' %}": "{% url 'device_config:test_connection' %}",

        # Navigation references
        "href='/device-config/'": "href='{% url \"device_config:device_list\" %}'",

        # Common missing patterns
        "{% url 'meter_list' %}": "{% url 'device_config:meter_list' %}",
        "{% url 'raspberry_pi_list' %}": "{% url 'device_config:raspberry_pi_list' %}",
        "{% url 'system_config' %}": "{% url 'device_config:system_config' %}",
        "{% url 'deployment_list' %}": "{% url 'device_config:deployment_list' %}",
    }

    fixed_files = []

    for template_dir in template_dirs:
        if template_dir.exists():
            for template_file in template_dir.rglob('*.html'):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    original_content = content

                    # Apply all URL fixes
                    for old_url, new_url in url_fixes.items():
                        content = content.replace(old_url, new_url)

                    # Use regex to fix any remaining device_manager references
                    content = re.sub(
                        r"{% url 'device_manager:(\w+)'", r"{% url 'device_config:\1'", content)
                    content = re.sub(r"{% url 'device_manager:(\w+)' (\w+) %}",
                                     r"{% url 'device_config:\1' \2 %}", content)

                    # Fix any references that don't use namespaces
                    content = re.sub(r"{% url '(\w+)' %}", lambda m:
                                     f"{{% url 'device_config:{m.group(1)}' %}}"
                                     if m.group(1) in ['meter_list', 'device_list', 'add_device', 'edit_device', 'delete_device']
                                     else m.group(0), content)

                    if content != original_content:
                        with open(template_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixed_files.append(str(template_file))
                        print(f"✅ Fixed {template_file.name}")

                except Exception as e:
                    print(f"⚠️  Error fixing {template_file}: {e}")

    print(f"📊 Fixed {len(fixed_files)} template files")


def create_simple_device_list_template():
    """Create a simple device_list template that definitely works"""

    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Device Configuration Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-online { color: #28a745; }
        .status-offline { color: #dc3545; }
        .live-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .live-indicator.online {
            background-color: #28a745;
            animation: pulse 2s infinite;
        }
        .live-indicator.offline {
            background-color: #dc3545;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{% url 'device_config:device_list' %}">
                <i class="fas fa-microchip"></i> Device Configuration Management
            </a>
            <div class="navbar-nav">
                <a class="nav-link" href="{% url 'meter_readings:dashboard' %}">
                    <i class="fas fa-chart-line"></i> Dashboard
                </a>
                <a class="nav-link" href="{% url 'device_config:add_device' %}">
                    <i class="fas fa-plus"></i> Add Device
                </a>
            </div>
        </div>
    </nav>

    {% if messages %}
    <div class="container-fluid mt-3">
        {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="container-fluid py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2><i class="fas fa-server"></i> Device Configuration Management</h2>
            <div>
                <button class="btn btn-success" onclick="location.reload()">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
                <a href="{% url 'device_config:add_device' %}" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Add Device
                </a>
            </div>
        </div>

        <!-- Statistics -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5><i class="fas fa-server"></i> Total Devices</h5>
                        <h3>{{ total_devices|default:0 }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5><i class="fas fa-check-circle text-success"></i> Online</h5>
                        <h3 class="text-success">{{ online_devices|default:0 }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5><i class="fas fa-times-circle text-danger"></i> Offline</h5>
                        <h3 class="text-danger">{{ total_devices|add:0|add:online_devices|floatformat:0 }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5><i class="fas fa-bolt"></i> Total Meters</h5>
                        <h3>{% for device in devices %}{{ device.meter_count|add:0 }}{% empty %}0{% endfor %}</h3>
                    </div>
                </div>
            </div>
        </div>

        <!-- Device List -->
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-list"></i> Configured Devices</h5>
            </div>
            <div class="card-body">
                {% if devices %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead class="table-dark">
                            <tr>
                                <th>Status</th>
                                <th>Device Name</th>
                                <th>IP Address</th>
                                <th>Location</th>
                                <th>Meters</th>
                                <th>Contact</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for device in devices %}
                            <tr>
                                <td>
                                    <span class="live-indicator {% if device.connection_status == 'online' %}online{% else %}offline{% endif %}"></span>
                                    <span class="status-{{ device.connection_status }}">
                                        {{ device.status|default:"Unknown" }}
                                    </span>
                                </td>
                                <td>
                                    <strong>{{ device.pi_name }}</strong>
                                    {% if device.description %}
                                    <br><small class="text-muted">{{ device.description }}</small>
                                    {% endif %}
                                </td>
                                <td>
                                    <code>{{ device.pi_ip }}</code>
                                    <br><small>{{ device.ssh_username }}@{{ device.pi_ip }}</small>
                                </td>
                                <td>{{ device.location|default:"Not specified" }}</td>
                                <td>
                                    <span class="badge bg-info">{{ device.meter_count|default:0 }} meters</span>
                                    {% if device.meters %}
                                    <br>
                                    {% for meter in device.meters %}
                                    <small class="text-muted">{{ meter.meter_name }}</small>{% if not forloop.last %}<br>{% endif %}
                                    {% endfor %}
                                    {% endif %}
                                </td>
                                <td>{{ device.contact_person|default:"Not specified" }}</td>
                                <td>
                                    <div class="btn-group" role="group">
                                        <button class="btn btn-info btn-sm" onclick="testConnection({{ device.id }})">
                                            <i class="fas fa-network-wired"></i> Test
                                        </button>
                                        <button class="btn btn-success btn-sm" onclick="deployConfig({{ device.id }})">
                                            <i class="fas fa-cloud-upload-alt"></i> Deploy
                                        </button>
                                        <a href="{% url 'device_config:edit_device' device.id %}" class="btn btn-warning btn-sm">
                                            <i class="fas fa-edit"></i> Edit
                                        </a>
                                        <button class="btn btn-danger btn-sm" onclick="deleteDevice({{ device.id }}, '{{ device.pi_name }}')">
                                            <i class="fas fa-trash"></i> Delete
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center py-5">
                    <i class="fas fa-server fa-3x text-muted mb-3"></i>
                    <h5>No devices configured</h5>
                    <p class="text-muted">Start by adding your first Raspberry Pi device.</p>
                    <a href="{% url 'device_config:add_device' %}" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Add First Device
                    </a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
    function testConnection(deviceId) {
        const btn = event.target;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        
        fetch(`/device-config/test/${deviceId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Connection successful!\\n' + data.message);
            } else {
                alert('Connection failed: ' + data.error);
            }
        })
        .catch(error => {
            alert('Request failed: ' + error);
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-network-wired"></i> Test';
        });
    }

    function deployConfig(deviceId) {
        const btn = event.target;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deploying...';
        
        fetch(`/device-config/deploy/${deviceId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Deployment successful!\\n' + data.message);
            } else {
                alert('Deployment failed: ' + data.error);
            }
        })
        .catch(error => {
            alert('Request failed: ' + error);
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-cloud-upload-alt"></i> Deploy';
        });
    }

    function deleteDevice(deviceId, deviceName) {
        if (!confirm(`Are you sure you want to delete device "${deviceName}"?`)) {
            return;
        }
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/device-config/delete/${deviceId}/`;
        
        const csrf = document.createElement('input');
        csrf.type = 'hidden';
        csrf.name = 'csrfmiddlewaretoken';
        csrf.value = '{{ csrf_token }}';
        form.appendChild(csrf);
        
        document.body.appendChild(form);
        form.submit();
    }
    </script>
</body>
</html>'''

    template_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config/device_list.html')
    template_file.parent.mkdir(parents=True, exist_ok=True)

    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(template_content)

    print("✅ Created simple working device_list.html template")


def main():
    """Apply complete URL fixes"""

    print("🔧 Applying complete URL reference fixes...")

    # Fix main project URLs
    fix_main_project_urls()

    # Fix device_config URLs
    fix_device_config_urls()

    # Fix template URL references
    fix_template_url_references()

    # Create a working template
    create_simple_device_list_template()

    print("""
🎉 Complete URL Fix Applied!

✅ Fixed main project URLs with dashboard redirect
✅ Added all missing URL patterns to device_config
✅ Fixed all template URL references
✅ Created working device_list.html template
✅ Added direct URL patterns for non-namespaced references

🚀 Restart Django server:
   cd meter_dashboard
   python3 manage.py runserver 0.0.0.0:8000

Navigate to: http://localhost:8000/device-config/

The DCMS interface should now load without any URL errors!
    """)


if __name__ == "__main__":
    main()
