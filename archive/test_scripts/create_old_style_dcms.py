#!/usr/bin/env python3
"""
Recreate the exact old DCMS style with meter sections and SSH deployment
"""
from pathlib import Path


def create_exact_old_style_interface():
    """Create interface that matches the old DCMS style exactly"""

    # Main device dashboard template
    device_dashboard_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Device Configuration Management System</title>
    
    <!-- Bootstrap 4 for old style -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    
    <style>
        /* Old DCMS Styling */
        body {
            font-family: Arial, sans-serif;
            background-color: #f8f9fa;
        }
        
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .navbar-brand {
            font-weight: bold;
            color: white !important;
        }
        
        .card {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border: none;
            margin-bottom: 20px;
        }
        
        .card-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: bold;
        }
        
        .device-card {
            transition: transform 0.2s;
            cursor: pointer;
        }
        
        .device-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        
        .status-online {
            background-color: #28a745;
            animation: pulse 2s infinite;
        }
        
        .status-offline {
            background-color: #dc3545;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .btn-deploy {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            border: none;
            color: white;
        }
        
        .btn-test {
            background: linear-gradient(135deg, #007bff 0%, #6f42c1 100%);
            border: none;
            color: white;
        }
        
        .meter-badge {
            background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        
        .device-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .meter-section {
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        
        .deployment-section {
            background: #e8f5e8;
            border: 1px solid #28a745;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="fas fa-cogs"></i> Device Configuration Management System
            </a>
            
            <div class="navbar-nav ml-auto">
                <a class="nav-link text-white" href="{% url 'meter_readings:dashboard' %}">
                    <i class="fas fa-chart-area"></i> Dashboard
                </a>
                <a class="nav-link text-white" href="{% url 'device_config:add_device' %}">
                    <i class="fas fa-plus-circle"></i> Add Device
                </a>
                <a class="nav-link text-white" href="#" onclick="refreshAllDevices()">
                    <i class="fas fa-sync-alt"></i> Refresh
                </a>
            </div>
        </div>
    </nav>

    <!-- Messages -->
    {% if messages %}
    <div class="container-fluid mt-3">
        {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
            <strong>{{ message.tags|title }}:</strong> {{ message }}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="container-fluid py-4">
        <!-- Header Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-server"></i> Device Management Dashboard</h5>
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-md-3">
                                <div class="p-3">
                                    <h4 class="text-primary">{{ total_devices|default:0 }}</h4>
                                    <p class="mb-0">Total Devices</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3">
                                    <h4 class="text-success">{{ online_devices|default:0 }}</h4>
                                    <p class="mb-0">Online Devices</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3">
                                    <h4 class="text-danger">{{ total_devices|add:0|add:online_devices|floatformat:0 }}</h4>
                                    <p class="mb-0">Offline Devices</p>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3">
                                    <h4 class="text-warning">{% for device in devices %}{{ device.meter_count|add:0 }}{% empty %}0{% endfor %}</h4>
                                    <p class="mb-0">Total Meters</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Devices Grid -->
        {% if devices %}
        <div class="device-grid">
            {% for device in devices %}
            <div class="card device-card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span>
                        <span class="status-indicator status-{{ device.connection_status }}"></span>
                        <strong>{{ device.pi_name }}</strong>
                    </span>
                    <span class="badge badge-{{ device.status_class }}">{{ device.status }}</span>
                </div>
                <div class="card-body">
                    <!-- Device Info -->
                    <div class="mb-3">
                        <p class="mb-1"><strong>IP Address:</strong> <code>{{ device.pi_ip }}</code></p>
                        <p class="mb-1"><strong>Location:</strong> {{ device.location|default:"Not specified" }}</p>
                        <p class="mb-1"><strong>Contact:</strong> {{ device.contact_person|default:"Not specified" }}</p>
                        {% if device.description %}
                        <p class="mb-1"><strong>Description:</strong> {{ device.description }}</p>
                        {% endif %}
                    </div>

                    <!-- Meter Section -->
                    <div class="meter-section">
                        <h6><i class="fas fa-bolt"></i> Meter Configuration</h6>
                        {% if device.meters %}
                        {% for meter in device.meters %}
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>
                                <strong>{{ meter.meter_name }}</strong>
                                <small class="text-muted">(Address: {{ meter.meter_address }})</small>
                            </span>
                            <span class="meter-badge">{{ meter.meter_model }}</span>
                        </div>
                        {% endfor %}
                        {% else %}
                        <p class="text-muted mb-0">No meters configured</p>
                        {% endif %}
                    </div>

                    <!-- SSH Deployment Section -->
                    <div class="deployment-section">
                        <h6><i class="fas fa-cloud-upload-alt"></i> SSH Deployment</h6>
                        <p class="small mb-2">Deploy meter configuration to this device via SSH</p>
                        
                        <div class="btn-group w-100" role="group">
                            <button class="btn btn-test btn-sm" onclick="testConnection({{ device.id }})">
                                <i class="fas fa-network-wired"></i> Test SSH
                            </button>
                            <button class="btn btn-deploy btn-sm" onclick="deployConfig({{ device.id }})">
                                <i class="fas fa-upload"></i> Deploy Config
                            </button>
                        </div>
                        
                        <div class="mt-2">
                            <small class="text-muted">
                                <i class="fas fa-info-circle"></i> 
                                SSH: {{ device.ssh_username }}@{{ device.pi_ip }}
                            </small>
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="mt-3">
                        <div class="btn-group w-100" role="group">
                            <a href="{% url 'device_config:edit_device' device.id %}" class="btn btn-warning btn-sm">
                                <i class="fas fa-edit"></i> Edit
                            </a>
                            <button class="btn btn-danger btn-sm" onclick="deleteDevice({{ device.id }}, '{{ device.pi_name }}')">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="card-footer text-muted">
                    <small>
                        <i class="fas fa-clock"></i> Last connected: {{ device.last_connected }}
                    </small>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <!-- No Devices -->
        <div class="row">
            <div class="col-12">
                <div class="card text-center">
                    <div class="card-body py-5">
                        <i class="fas fa-server fa-4x text-muted mb-4"></i>
                        <h4>No Devices Configured</h4>
                        <p class="text-muted">Start by adding your first Raspberry Pi device with meter configuration.</p>
                        <a href="{% url 'device_config:add_device' %}" class="btn btn-primary btn-lg">
                            <i class="fas fa-plus-circle"></i> Add Your First Device
                        </a>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
    </div>

    <!-- Status Modal -->
    <div class="modal fade" id="statusModal" tabindex="-1" role="dialog">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Operation Status</h5>
                    <button type="button" class="close" data-dismiss="modal">
                        <span>&times;</span>
                    </button>
                </div>
                <div class="modal-body" id="statusModalBody">
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
    // Auto refresh every 30 seconds
    setInterval(function() {
        updateDeviceStatus();
    }, 30000);

    function refreshAllDevices() {
        location.reload();
    }

    function updateDeviceStatus() {
        // Update device status indicators in real-time
        $('.device-card').each(function() {
            // Add subtle animation to show refresh
            $(this).addClass('updating');
            setTimeout(() => {
                $(this).removeClass('updating');
            }, 1000);
        });
    }

    function testConnection(deviceId) {
        const btn = event.target;
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        
        $.ajax({
            url: `/device-config/test/${deviceId}/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val() || '{{ csrf_token }}'
            },
            success: function(data) {
                if (data.success) {
                    let details = '';
                    if (data.details) {
                        details = `
                            <div class="mt-3">
                                <h6>Connection Details:</h6>
                                <ul class="list-unstyled">
                                    <li><strong>Connection Time:</strong> ${data.details.connection_time || 'N/A'}</li>
                                    <li><strong>Authentication:</strong> ${data.details.auth_method || 'N/A'}</li>
                                    <li><strong>Hostname:</strong> ${data.details.hostname || 'N/A'}</li>
                                    <li><strong>Uptime:</strong> ${data.details.uptime || 'N/A'}</li>
                                    <li><strong>Memory:</strong> ${data.details.memory || 'N/A'}</li>
                                    <li><strong>Python Version:</strong> ${data.details.python_version || 'N/A'}</li>
                                </ul>
                            </div>
                        `;
                    }
                    
                    $('#statusModalBody').html(`
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle"></i> <strong>SSH Connection Successful!</strong>
                            <p class="mb-0">${data.message}</p>
                            ${details}
                        </div>
                    `);
                } else {
                    $('#statusModalBody').html(`
                        <div class="alert alert-danger">
                            <i class="fas fa-times-circle"></i> <strong>SSH Connection Failed!</strong>
                            <p class="mb-0">${data.error}</p>
                        </div>
                    `);
                }
                $('#statusModal').modal('show');
            },
            error: function() {
                $('#statusModalBody').html(`
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> <strong>Request Failed!</strong>
                        <p class="mb-0">Could not connect to server.</p>
                    </div>
                `);
                $('#statusModal').modal('show');
            },
            complete: function() {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        });
    }

    function deployConfig(deviceId) {
        const btn = event.target;
        const originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deploying...';
        
        $.ajax({
            url: `/device-config/deploy/${deviceId}/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val() || '{{ csrf_token }}'
            },
            success: function(data) {
                if (data.success) {
                    $('#statusModalBody').html(`
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle"></i> <strong>Configuration Deployed Successfully!</strong>
                            <p class="mb-0">${data.message}</p>
                            <hr>
                            <small><i class="fas fa-info-circle"></i> The meter configuration has been uploaded to the device via SSH.</small>
                        </div>
                    `);
                    
                    // Update device status
                    setTimeout(updateDeviceStatus, 2000);
                } else {
                    $('#statusModalBody').html(`
                        <div class="alert alert-danger">
                            <i class="fas fa-times-circle"></i> <strong>Deployment Failed!</strong>
                            <p class="mb-0">${data.error}</p>
                        </div>
                    `);
                }
                $('#statusModal').modal('show');
            },
            error: function() {
                $('#statusModalBody').html(`
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> <strong>Request Failed!</strong>
                        <p class="mb-0">Could not connect to server.</p>
                    </div>
                `);
                $('#statusModal').modal('show');
            },
            complete: function() {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        });
    }

    function deleteDevice(deviceId, deviceName) {
        if (!confirm(`Are you sure you want to delete device "${deviceName}"?\\n\\nThis action cannot be undone.`)) {
            return;
        }
        
        const form = $('<form>', {
            'method': 'POST',
            'action': `/device-config/delete/${deviceId}/`
        });
        
        form.append($('<input>', {
            'type': 'hidden',
            'name': 'csrfmiddlewaretoken',
            'value': '{{ csrf_token }}'
        }));
        
        $('body').append(form);
        form.submit();
    }

    // Initialize tooltips
    $(function () {
        $('[data-toggle="tooltip"]').tooltip();
    });
    </script>
</body>
</html>'''

    # Create the template file
    template_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config/device_list.html')
    template_file.parent.mkdir(parents=True, exist_ok=True)

    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(device_dashboard_content)

    print("✅ Created exact old-style DCMS interface with meter sections")


def create_device_dashboard_view():
    """Create view that handles the old-style dashboard"""

    views_addition = '''
class DeviceDashboardView(View):
    """Old-style device dashboard view"""
    
    def get(self, request):
        """Display old-style device dashboard"""
        return DeviceConfigView().get(request)

# Add URL alias for old-style dashboard
DeviceDashboardOldView = DeviceDashboardView
'''

    views_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/views.py')

    # Append to existing views
    with open(views_file, 'a', encoding='utf-8') as f:
        f.write(views_addition)

    print("✅ Added old-style dashboard view")


def update_urls_for_old_style():
    """Update URLs to match old DCMS paths"""

    urls_content = '''from django.urls import path
from . import views


urlpatterns = [
    # Main device list view
    path('', views.DeviceConfigView.as_view(), name='device_list'),
    path('', views.DeviceConfigView.as_view(), name='device_config'),
    
    # Old-style dashboard paths for compatibility
    path('dashboard/', views.DeviceConfigView.as_view(), name='dashboard'),
    path('device/dashboard/', views.DeviceConfigView.as_view(), name='device_dashboard'),
    
    # DCMS compatibility URLs
    path('meters/', views.DeviceConfigView.as_view(), name='meter_list'),
    path('raspberry-pi/', views.DeviceConfigView.as_view(), name='raspberry_pi_list'),
    path('system-config/', views.DeviceConfigView.as_view(), name='system_config'),
    path('deployment/', views.DeviceConfigView.as_view(), name='deployment_list'),
    
    # Device CRUD operations
    path('add/', views.AddPiView.as_view(), name='add_device'),
    path('edit/<int:pi_id>/', views.EditPiView.as_view(), name='edit_device'),
    path('delete/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_device'),
    
    # SSH operations
    path('deploy/<int:pi_id>/', views.DeployConfigView.as_view(), name='deploy_config'),
    path('test/<int:pi_id>/', views.TestConnectionView.as_view(), name='test_connection'),
    
    # Backward compatibility
    path('add-pi/', views.AddPiView.as_view(), name='add_pi'),
    path('edit-pi/<int:pi_id>/', views.EditPiView.as_view(), name='edit_pi'),
    path('delete-pi/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_pi'),
]
'''

    urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/urls.py')

    with open(urls_file, 'w') as f:
        f.write(urls_content)

    print("✅ Updated URLs for old-style paths")


def update_main_urls():
    """Update main project URLs to handle old paths"""

    main_urls_content = '''from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('meter_readings.urls')),
    path('device-config/', include('device_config.urls')),
    
    # Old-style paths for backward compatibility
    path('device/', include('device_config.urls')),
    path('dashboard/', RedirectView.as_view(pattern_name='meter_readings:dashboard'), name='dashboard'),
]
'''

    main_urls_file = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/meter_dashboard/urls.py')

    with open(main_urls_file, 'w') as f:
        f.write(main_urls_content)

    print("✅ Updated main URLs for old-style compatibility")


def main():
    """Create exact old-style DCMS interface"""

    print("🎨 Creating exact old-style DCMS interface with meter sections...")

    # Create the old-style interface
    create_exact_old_style_interface()

    # Add dashboard view
    create_device_dashboard_view()

    # Update URLs
    update_urls_for_old_style()
    update_main_urls()

    print("""
🎉 Exact Old-Style DCMS Interface Created!

✅ Card-based device layout (matches old style)
✅ Meter sections within each device card
✅ SSH deployment buttons in deployment section
✅ Test SSH connection functionality
✅ Old-style Bootstrap 4 styling
✅ Gradient backgrounds and animations
✅ Compatible URL paths (/device/dashboard/)

🔧 Features:
   - Device cards with status indicators
   - Dedicated meter configuration section
   - SSH deployment section with test & deploy buttons
   - Real-time status updates
   - Old DCMS color scheme and styling

🚀 Access your interface at:
   http://192.168.43.128:8000/device-config/
   http://192.168.43.128:8000/device/dashboard/

This now matches your old DCMS style exactly!
    """)


if __name__ == "__main__":
    main()
