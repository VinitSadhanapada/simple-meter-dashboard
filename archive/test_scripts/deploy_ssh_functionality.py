#!/usr/bin/env python3
"""
Deploy the full SSH functionality and live status views
"""


def deploy_full_functionality():
    """Replace views with full SSH deployment functionality"""

    from pathlib import Path
    import shutil

    # Backup old views
    old_views = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/views.py')
    new_views = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/views_full.py')

    if old_views.exists():
        shutil.move(str(old_views), str(old_views.parent / 'views_backup.py'))
        print("✅ Backed up old views")

    if new_views.exists():
        shutil.move(str(new_views), str(old_views))
        print("✅ Deployed new views with SSH functionality")

    # Update URLs to include new endpoints
    urls_content = '''from django.urls import path
from . import views


urlpatterns = [
    # Main views
    path('', views.DeviceConfigView.as_view(), name='device_list'),
    path('', views.DeviceConfigView.as_view(), name='device_config'),
    
    # DCMS compatibility URLs
    path('meters/', views.DeviceConfigView.as_view(), name='meter_list'),
    path('raspberry-pi/', views.DeviceConfigView.as_view(), name='raspberry_pi_list'),
    path('system-config/', views.DeviceConfigView.as_view(), name='system_config'),
    path('deployment/', views.DeviceConfigView.as_view(), name='deployment_list'),
    
    # Device CRUD
    path('add/', views.AddPiView.as_view(), name='add_device'),
    path('edit/<int:pi_id>/', views.EditPiView.as_view(), name='edit_device'),
    path('delete/<int:pi_id>/', views.DeletePiView.as_view(), name='delete_device'),
    
    # Device operations (SSH deployment)
    path('deploy/<int:pi_id>/', views.DeployConfigView.as_view(), name='deploy_config'),
    path('test/<int:pi_id>/', views.TestConnectionView.as_view(), name='test_connection'),
    
    # AJAX endpoints for live functionality
    path('live-status/', views.LiveStatusView.as_view(), name='live_status'),
    path('deploy-all/', views.DeployAllView.as_view(), name='deploy_all'),
    
    # Backward compatibility
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

    print("✅ Updated URLs with live status endpoints")


def create_javascript_for_live_status():
    """Create JavaScript for live status updates"""

    js_content = '''
// Live status functionality for DCMS
$(document).ready(function() {
    
    // Auto-refresh device status every 30 seconds
    if (window.location.pathname.includes('device-config')) {
        setInterval(updateDeviceStatus, 30000);
    }
    
    // Manual refresh button
    $('#refresh-status').click(function() {
        updateDeviceStatus();
    });
    
    // Deploy all button
    $('#deploy-all').click(function() {
        if (confirm('Deploy configuration to all active devices?')) {
            deployToAll();
        }
    });
    
});

function updateDeviceStatus() {
    $.get('/device-config/live-status/', function(data) {
        if (data.devices) {
            data.devices.forEach(function(device) {
                const row = $(`tr[data-device-id="${device.id}"]`);
                if (row.length) {
                    // Update status badge
                    const statusBadge = row.find('.status-badge');
                    statusBadge.removeClass('badge-success badge-danger badge-warning');
                    
                    if (device.connection_status === 'online') {
                        statusBadge.addClass('badge-success').text('Online');
                    } else {
                        statusBadge.addClass('badge-danger').text('Offline');
                    }
                    
                    // Update last connected
                    row.find('.last-connected').text(device.last_connected);
                }
            });
            
            // Update summary counters
            $('#total-devices').text(data.total_devices);
            $('#online-devices').text(data.online_devices);
        }
    }).fail(function() {
        console.log('Failed to update device status');
    });
}

function deployToAll() {
    const deployBtn = $('#deploy-all');
    deployBtn.prop('disabled', true).text('Deploying...');
    
    $.post('/device-config/deploy-all/', function(data) {
        if (data.success) {
            alert('Bulk deployment completed!\\n' + data.message);
            
            // Show detailed results
            if (data.results && data.results.length > 0) {
                let resultText = '\\nDetailed Results:\\n';
                data.results.forEach(function(result) {
                    resultText += `${result.pi_name}: ${result.success ? 'Success' : 'Failed'} - ${result.message}\\n`;
                });
                console.log(resultText);
            }
        } else {
            alert('Deployment failed: ' + data.error);
        }
    }).fail(function() {
        alert('Deployment request failed');
    }).always(function() {
        deployBtn.prop('disabled', false).text('Deploy All');
    });
}

function testConnection(deviceId) {
    const testBtn = $(`.test-connection[data-device-id="${deviceId}"]`);
    testBtn.prop('disabled', true).text('Testing...');
    
    $.post(`/device-config/test/${deviceId}/`, function(data) {
        if (data.success) {
            alert(`Connection successful!\\n${data.message}\\n\\nDetails:\\n` +
                  `Connection Time: ${data.details?.connection_time || 'N/A'}\\n` +
                  `Auth Method: ${data.details?.auth_method || 'N/A'}\\n` +
                  `Hostname: ${data.details?.hostname || 'N/A'}\\n` +
                  `Uptime: ${data.details?.uptime || 'N/A'}`);
        } else {
            alert('Connection failed: ' + data.error);
        }
    }).fail(function() {
        alert('Connection test request failed');
    }).always(function() {
        testBtn.prop('disabled', false).text('Test');
    });
}

function deployConfig(deviceId) {
    const deployBtn = $(`.deploy-config[data-device-id="${deviceId}"]`);
    deployBtn.prop('disabled', true).text('Deploying...');
    
    $.post(`/device-config/deploy/${deviceId}/`, function(data) {
        if (data.success) {
            alert('Deployment successful!\\n' + data.message);
            updateDeviceStatus(); // Refresh status
        } else {
            alert('Deployment failed: ' + data.error);
        }
    }).fail(function() {
        alert('Deployment request failed');
    }).always(function() {
        deployBtn.prop('disabled', false).text('Deploy');
    });
}
'''

    # Save JavaScript to static files
    static_dir = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/static/device_config/js')
    static_dir.mkdir(parents=True, exist_ok=True)

    with open(static_dir / 'live_status.js', 'w') as f:
        f.write(js_content)

    print("✅ Created JavaScript for live status functionality")


def main():
    """Deploy full SSH functionality"""

    print("🚀 Deploying full SSH deployment and live status functionality...")

    deploy_full_functionality()
    create_javascript_for_live_status()

    print("""
🎉 Full SSH Deployment Functionality Deployed!

✅ Real SSH deployment to Pi devices
✅ Live status checking via SSH
✅ Connection testing with detailed system info
✅ Bulk deployment to all devices
✅ Auto-refresh device status every 30 seconds
✅ JavaScript for interactive functionality

🔧 Features Added:
   - SSH key and password authentication
   - Real file deployment (device_config.jsonc)
   - Live connection status checking
   - Detailed connection testing
   - Bulk operations
   - Error handling and timeouts

🚀 Start Django server:
   cd meter_dashboard
   python3 manage.py runserver 0.0.0.0:8000

Navigate to: http://localhost:8000/device-config/

The interface will now show live status and allow real SSH deployments!
    """)


if __name__ == "__main__":
    main()
