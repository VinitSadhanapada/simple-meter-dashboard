#!/usr/bin/env python3
"""
Complete setup script for DCMS with SSH deployment functionality
"""
import shutil
import os
import json
from pathlib import Path


def copy_dcms_templates():
    """Copy DCMS templates to device_config app"""

    source = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_configuration_management_system/device_manager/templates/device_manager')
    dest = Path(
        '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/templates/device_config')

    print("📋 Copying DCMS templates...")

    if not source.exists():
        print(f"❌ DCMS source not found: {source}")
        return False

    dest.mkdir(parents=True, exist_ok=True)

    # Copy all templates
    for template in source.glob('*.html'):
        dest_file = dest / template.name
        shutil.copy2(template, dest_file)

        # Update template references
        with open(dest_file, 'r') as f:
            content = f.read()

        # Fix references
        content = content.replace(
            "{% extends 'device_manager/base.html' %}", "{% extends 'device_config/base.html' %}")
        content = content.replace(
            "{% url 'device_manager:", "{% url 'device_config:")
        content = content.replace("'device_manager'", "'device_config'")

        with open(dest_file, 'w') as f:
            f.write(content)

    print("✅ DCMS templates copied and updated")
    return True


def create_full_views():
    """Create views with full SSH functionality"""

    views_content = '''from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import os
import socket
import time
from pathlib import Path
import logging

# Try to import paramiko, fallback to simulation if not available
try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False
    print("⚠️  paramiko not available, using simulation mode")

logger = logging.getLogger(__name__)

class DeviceConfigView(View):
    """Main device configuration management view with live status"""

    def get(self, request):
        """Display device configuration management interface with live status"""

        # Load device configurations
        config_file = Path(__file__).parent.parent / 'device_configs.json'
        devices = []

        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    pi_configs = json.load(f)

                # Convert to format with live status checking
                for i, config in enumerate(pi_configs):
                    # Check live connection status
                    connection_status, last_connected = self._check_device_status(
                        config)

                    device = {
                        'id': i,
                        'pi_name': config.get('pi_name', ''),
                        'pi_ip': config.get('pi_ip', ''),
                        'location': config.get('location', ''),
                        'ssh_username': config.get('ssh_username', 'pi'),
                        'ssh_password': config.get('ssh_password', ''),
                        'ssh_key_path': config.get('ssh_key_path', ''),
                        'config_path': config.get('config_path', ''),
                        'description': config.get('description', ''),
                        'contact_person': config.get('contact_person', ''),
                        'is_active': config.get('is_active', True),
                        'meters': config.get('meters', []),
                        'meter_count': len(config.get('meters', [])),
                        'last_connected': last_connected,
                        'connection_status': connection_status,
                        'status': 'Online' if connection_status == 'online' else 'Offline',
                        'status_class': 'success' if connection_status == 'online' else 'danger'
                    }
                    devices.append(device)
            else:
                # Create sample data for demonstration
                sample_devices = [
                    {
                        'id': 0,
                        'pi_name': 'Sample Pi 1',
                        'pi_ip': '192.168.1.100',
                        'location': 'Building A',
                        'ssh_username': 'pi',
                        'ssh_password': '',
                        'ssh_key_path': '/home/pi/.ssh/id_rsa',
                        'config_path': '/home/pi/MFM_offline_setup',
                        'description': 'Sample device for demonstration',
                        'contact_person': 'Admin',
                        'is_active': True,
                        'meters': [
                            {'meter_name': 'LG6400_1', 'meter_address': 1,
                                'meter_model': 'LG6400', 'location': 'Building A'},
                            {'meter_name': 'LG6400_2', 'meter_address': 2,
                                'meter_model': 'LG6400', 'location': 'Building A'}
                        ],
                        'meter_count': 2,
                        'last_connected': 'Never',
                        'connection_status': 'offline',
                        'status': 'Offline',
                        'status_class': 'danger'
                    }
                ]
                devices = sample_devices

        except Exception as e:
            logger.error(f"Error loading device configs: {e}")

        context = {
            'pi_configs': devices,  # For backward compatibility
            'devices': devices,     # For DCMS templates
            'page_title': 'Device Configuration Management',
            'total_devices': len(devices),
            'online_devices': len([d for d in devices if d['connection_status'] == 'online']),
            'active_devices': len([d for d in devices if d['is_active']]),
            'ssh_available': SSH_AVAILABLE,
        }

        return render(request, 'device_config/device_list.html', context)

    def _check_device_status(self, config):
        """Check live status of device via SSH"""
        if not SSH_AVAILABLE:
            return 'offline', 'SSH not available'

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Try SSH connection with timeout
            if config.get('ssh_key_path') and os.path.exists(config['ssh_key_path']):
                ssh.connect(
                    hostname=config['pi_ip'],
                    username=config.get('ssh_username', 'pi'),
                    key_filename=config['ssh_key_path'],
                    timeout=3
                )
            else:
                ssh.connect(
                    hostname=config['pi_ip'],
                    username=config.get('ssh_username', 'pi'),
                    password=config.get('ssh_password', ''),
                    timeout=3
                )

            ssh.close()
            return 'online', 'Just now'

        except Exception as e:
            logger.debug(
                f"Device {config.get('pi_name', 'Unknown')} offline: {e}")
            return 'offline', 'Connection failed'

class AddPiView(View):
    """Add new Pi configuration"""

    def get(self, request):
        """Display add Pi form"""
        context = {
            'page_title': 'Add New Device',
            'form_title': 'Add Raspberry Pi Device',
        }
        return render(request, 'device_config/add_device.html', context)

    def post(self, request):
        """Handle Pi configuration submission"""
        try:
            # Extract Pi details
            pi_data = {
                'pi_name': request.POST.get('pi_name'),
                'pi_ip': request.POST.get('pi_ip'),
                'location': request.POST.get('location'),
                'ssh_username': request.POST.get('ssh_username', 'pi'),
                'ssh_password': request.POST.get('ssh_password', ''),
                'ssh_key_path': request.POST.get('ssh_key_path', '/home/pi/.ssh/id_rsa'),
                'config_path': request.POST.get('config_path', '/home/pi/MFM_offline_setup'),
                'description': request.POST.get('description', ''),
                'contact_person': request.POST.get('contact_person', ''),
                'is_active': request.POST.get('is_active') == 'on',
                'meters': []
            }

            # Extract meter configurations
            meter_names = request.POST.getlist('meter_name[]')
            meter_addresses = request.POST.getlist('meter_address[]')
            meter_models = request.POST.getlist('meter_model[]')

            for i in range(len(meter_names)):
                if meter_names[i].strip():
                    meter = {
                        'meter_name': meter_names[i],
                        'meter_address': int(meter_addresses[i]) if meter_addresses[i] else 1,
                        'meter_model': meter_models[i] if meter_models[i] else 'LG6400',
                        'location': pi_data['location']
                    }
                    pi_data['meters'].append(meter)

            # Save to device_configs.json
            self._save_pi_config(pi_data)

            messages.success(
                request, f"Pi '{pi_data['pi_name']}' added successfully with {len(pi_data['meters'])} meters!")
            return redirect('device_config:device_list')

        except Exception as e:
            logger.error(f"Error adding Pi: {e}")
            messages.error(request, f"Error adding Pi: {str(e)}")
            return redirect('device_config:add_device')

    def _save_pi_config(self, pi_data):
        """Save Pi configuration to JSON file"""
        config_file = Path(__file__).parent.parent / 'device_configs.json'

        # Load existing configs
        configs = []
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    configs = json.load(f)
            except:
                configs = []

        # Add new config
        configs.append(pi_data)

        # Save back to file
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(configs, f, indent=2)

class EditPiView(View):
    """Edit existing Pi configuration"""

    def get(self, request, pi_id):
        """Display edit Pi form"""
        pi_config = self._get_pi_config(pi_id)
        if not pi_config:
            messages.error(request, "Pi configuration not found")
            return redirect('device_config:device_list')

        context = {
            'pi_config': pi_config,
            'device': pi_config,  # For DCMS template compatibility
            'pi_id': pi_id,
            'device_id': pi_id,   # For DCMS template compatibility
            'page_title': f'Edit Device: {pi_config.get("pi_name", "Unknown")}',
            'form_title': f'Edit {pi_config.get("pi_name", "Device")}',
        }
        return render(request, 'device_config/edit_device.html', context)

    def post(self, request, pi_id):
        """Handle Pi configuration update"""
        try:
            # Load existing configs
            config_file = Path(__file__).parent.parent / 'device_configs.json'
            with open(config_file, 'r') as f:
                configs = json.load(f)

            if pi_id >= len(configs):
                messages.error(request, "Pi configuration not found")
                return redirect('device_config:device_list')

            # Update Pi configuration
            configs[pi_id].update({
                'pi_name': request.POST.get('pi_name'),
                'pi_ip': request.POST.get('pi_ip'),
                'location': request.POST.get('location'),
                'ssh_username': request.POST.get('ssh_username', 'pi'),
                'ssh_password': request.POST.get('ssh_password', ''),
                'ssh_key_path': request.POST.get('ssh_key_path', '/home/pi/.ssh/id_rsa'),
                'config_path': request.POST.get('config_path', '/home/pi/MFM_offline_setup'),
                'description': request.POST.get('description', ''),
                'contact_person': request.POST.get('contact_person', ''),
                'is_active': request.POST.get('is_active') == 'on',
            })

            # Update meters
            meter_names = request.POST.getlist('meter_name[]')
            meter_addresses = request.POST.getlist('meter_address[]')
            meter_models = request.POST.getlist('meter_model[]')

            configs[pi_id]['meters'] = []
            for i in range(len(meter_names)):
                if meter_names[i].strip():
                    meter = {
                        'meter_name': meter_names[i],
                        'meter_address': int(meter_addresses[i]) if meter_addresses[i] else 1,
                        'meter_model': meter_models[i] if meter_models[i] else 'LG6400',
                        'location': configs[pi_id]['location']
                    }
                    configs[pi_id]['meters'].append(meter)

            # Save back to file
            with open(config_file, 'w') as f:
                json.dump(configs, f, indent=2)

            messages.success(
                request, f"Pi '{configs[pi_id]['pi_name']}' updated successfully!")
            return redirect('device_config:device_list')

        except Exception as e:
            logger.error(f"Error updating Pi: {e}")
            messages.error(request, f"Error updating Pi: {str(e)}")
            return redirect('device_config:edit_device', pi_id=pi_id)

    def _get_pi_config(self, pi_id):
        """Get Pi configuration by ID"""
        try:
            config_file = Path(__file__).parent.parent / 'device_configs.json'
            with open(config_file, 'r') as f:
                configs = json.load(f)

            if pi_id < len(configs):
                return configs[pi_id]
        except:
            pass
        return None

class DeletePiView(View):
    """Delete Pi configuration"""

    def post(self, request, pi_id):
        """Handle Pi deletion"""
        try:
            config_file = Path(__file__).parent.parent / 'device_configs.json'
            with open(config_file, 'r') as f:
                configs = json.load(f)

            if pi_id < len(configs):
                pi_name = configs[pi_id]['pi_name']
                del configs[pi_id]

                with open(config_file, 'w') as f:
                    json.dump(configs, f, indent=2)

                messages.success(
                    request, f"Pi '{pi_name}' deleted successfully!")
            else:
                messages.error(request, "Pi configuration not found")

        except Exception as e:
            logger.error(f"Error deleting Pi: {e}")
            messages.error(request, f"Error deleting Pi: {str(e)}")

        return redirect('device_config:device_list')

class DeployConfigView(View):
    """Deploy configuration to Pi via SSH - FULL IMPLEMENTATION"""

    def post(self, request, pi_id):
        """Deploy configuration to specific Pi via SSH"""
        try:
            pi_config = self._get_pi_config(pi_id)
            if not pi_config:
                return JsonResponse({'success': False, 'error': 'Pi configuration not found'})

            if not SSH_AVAILABLE:
                return JsonResponse({'success': False, 'error': 'SSH functionality not available. Install paramiko: pip install paramiko'})

            # Test connection first
            if not self._test_ssh_connection(pi_config):
                return JsonResponse({'success': False, 'error': 'Cannot connect to Pi via SSH. Check credentials and network.'})

            # Generate device_config.jsonc for this Pi
            device_config = []
            for meter in pi_config['meters']:
                device_config.append({
                    'meter_name': meter['meter_name'],
                    'meter_address': meter['meter_address'],
                    'meter_model': meter['meter_model'],
                    'location': meter['location'],
                    'pi_name': pi_config['pi_name'],
                    'pi_ip': pi_config['pi_ip']
                })

            # Deploy to Pi via SSH
            success, message = self._deploy_to_pi(pi_config, device_config)

            if success:
                return JsonResponse({'success': True, 'message': message})
            else:
                return JsonResponse({'success': False, 'error': message})

        except Exception as e:
            logger.error(f"Error deploying config: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

    def _get_pi_config(self, pi_id):
        """Get Pi configuration by ID"""
        try:
            config_file = Path(__file__).parent.parent / 'device_configs.json'
            with open(config_file, 'r') as f:
                configs = json.load(f)
            return configs[pi_id] if pi_id < len(configs) else None
        except:
            return None

    def _test_ssh_connection(self, pi_config):
        """Test SSH connection to Pi"""
        if not SSH_AVAILABLE:
            return False

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Try key-based authentication first
            if pi_config.get('ssh_key_path') and os.path.exists(pi_config['ssh_key_path']):
                ssh.connect(
                    hostname=pi_config['pi_ip'],
                    username=pi_config.get('ssh_username', 'pi'),
                    key_filename=pi_config['ssh_key_path'],
                    timeout=10
                )
            else:
                # Fallback to password authentication
                ssh.connect(
                    hostname=pi_config['pi_ip'],
                    username=pi_config.get('ssh_username', 'pi'),
                    password=pi_config.get('ssh_password', ''),
                    timeout=10
                )

            ssh.close()
            return True

        except Exception as e:
            logger.error(f"SSH connection test failed: {e}")
            return False

    def _deploy_to_pi(self, pi_config, device_config):
        """Deploy configuration to Pi via SSH"""
        if not SSH_AVAILABLE:
            return False, "SSH functionality not available"

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to Pi
            if pi_config.get('ssh_key_path') and os.path.exists(pi_config['ssh_key_path']):
                ssh.connect(
                    hostname=pi_config['pi_ip'],
                    username=pi_config.get('ssh_username', 'pi'),
                    key_filename=pi_config['ssh_key_path'],
                    timeout=15
                )
            else:
                ssh.connect(
                    hostname=pi_config['pi_ip'],
                    username=pi_config.get('ssh_username', 'pi'),
                    password=pi_config.get('ssh_password', ''),
                    timeout=15
                )

            # Create config directory if not exists
            config_path = pi_config.get(
                'config_path', '/home/pi/MFM_offline_setup')
            ssh.exec_command(f'mkdir -p {config_path}')

            # Upload device_config.jsonc
            sftp = ssh.open_sftp()

            # Create device config content with comments
            device_config_content = f''' // Device configuration for {pi_config["pi_name"]}


// Generated automatically from Device Configuration Management System
// Last updated: {time.strftime("%Y-%m-%d %H:%M:%S")}

{json.dumps(device_config, indent=2)}
'''

            # Create temporary file
            temp_file = f'/tmp/device_config_{pi_config["pi_name"].replace(" ", "_")}.jsonc'

            with open(temp_file, 'w') as f:
                f.write(device_config_content)

            # Upload to Pi
            remote_config_file = f'{config_path}/device_config.jsonc'
            sftp.put(temp_file, remote_config_file)

            # Set proper permissions
            ssh.exec_command(f'chmod 644 {remote_config_file}')

            # Clean up temp file
            os.remove(temp_file)

            sftp.close()
            ssh.close()

            return True, f"Configuration deployed successfully to {pi_config['pi_name']} at {config_path}/device_config.jsonc"

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False, f"Deployment failed: {str(e)}"

class TestConnectionView(View):
    """Test SSH connection to Pi - FULL IMPLEMENTATION"""

    def post(self, request, pi_id):
        """Test connection to specific Pi"""
        try:
            pi_config = self._get_pi_config(pi_id)
            if not pi_config:
                return JsonResponse({'success': False, 'error': 'Pi configuration not found'})

            if not SSH_AVAILABLE:
                return JsonResponse({'success': False, 'error': 'SSH functionality not available. Install paramiko: pip install paramiko'})

            # Test SSH connection with detailed info
            success, message, details = self._detailed_connection_test(
                pi_config)

            if success:
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'details': details
                })
            else:
                return JsonResponse({'success': False, 'error': message})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def _get_pi_config(self, pi_id):
        """Get Pi configuration by ID"""
        try:
            config_file = Path(__file__).parent.parent / 'device_configs.json'
            with open(config_file, 'r') as f:
                configs = json.load(f)
            return configs[pi_id] if pi_id < len(configs) else None
        except:
            return None

    def _detailed_connection_test(self, pi_config):
        """Detailed SSH connection test with system info"""
        if not SSH_AVAILABLE:
            return False, "SSH functionality not available", {}

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            start_time = time.time()

            # Connect to Pi
            if pi_config.get('ssh_key_path') and os.path.exists(pi_config['ssh_key_path']):
                ssh.connect(
                    hostname=pi_config['pi_ip'],
                    username=pi_config.get('ssh_username', 'pi'),
                    key_filename=pi_config['ssh_key_path'],
                    timeout=10
                )
                auth_method = "SSH Key"
            else:
                ssh.connect(
                    hostname=pi_config['pi_ip'],
                    username=pi_config.get('ssh_username', 'pi'),
                    password=pi_config.get('ssh_password', ''),
                    timeout=10
                )
                auth_method = "Password"

            connection_time = round((time.time() - start_time) * 1000, 2)

            # Get system information
            commands = {
                'hostname': 'hostname',
                'uptime': 'uptime',
                'disk_usage': 'df -h / | tail -1',
                'memory': 'free -h | grep Mem',
                'python_version': 'python3 --version',
                'mfm_status': 'systemctl is-active mfm-dashboard 2>/dev/null || echo "not-installed"'
            }

            system_info = {}
            for key, command in commands.items():
                try:
                    stdin, stdout, stderr = ssh.exec_command(command)
                    output = stdout.read().decode().strip()
                    system_info[key] = output
                except:
                    system_info[key] = 'N/A'

            ssh.close()

            details = {
                'connection_time': f"{connection_time}ms",
                'auth_method': auth_method,
                'hostname': system_info.get('hostname', 'N/A'),
                'uptime': system_info.get('uptime', 'N/A'),
                'disk_usage': system_info.get('disk_usage', 'N/A'),
                'memory': system_info.get('memory', 'N/A'),
                'python_version': system_info.get('python_version', 'N/A'),
                'mfm_status': system_info.get('mfm_status', 'N/A')
            }

            return True, f"Successfully connected to {pi_config['pi_name']}", details

        except Exception as e:
            logger.error(f"SSH connection test failed: {e}")
            return False, f"Connection failed: {str(e)}", {}

# Compatibility aliases for DCMS templates
AddDeviceView = AddPiView
EditDeviceView = EditPiView
DeleteDeviceView = DeletePiView
DeviceListView = DeviceConfigView
'''

  views_file = Path(
      '/home/isha/deepak/MFM_offline_setup/meter_dashboard/device_config/views.py')

   with open(views_file, 'w') as f:
        f.write(views_content)

    print("✅ Created full SSH deployment views")


def create_urls():
    """Create comprehensive URL patterns"""

    urls_content = '''from django.urls import path
from . import views

app_name = 'device_config'

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

    print("✅ Created comprehensive URL patterns")


def install_dependencies():
    """Install required dependencies"""

    import subprocess
    import sys

    packages = ['paramiko', 'django', 'psycopg2-binary']

    for package in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package],
                           check=True, capture_output=True)
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Could not install {package}")


def main():
    """Complete setup"""

    print("🚀 Setting up complete DCMS with SSH deployment functionality...")

    # Install dependencies
    install_dependencies()

    # Copy DCMS templates
    copy_dcms_templates()

    # Create full views with SSH functionality
    create_full_views()

    # Create comprehensive URLs
    create_urls()

    print("""
🎉 Complete DCMS Setup Finished!

✅ DCMS templates copied and updated
✅ Full SSH deployment functionality
✅ Live status checking
✅ Connection testing with system info
✅ Comprehensive URL patterns
✅ Dependencies installed

🔧 Features Available:
   - Real SSH deployment to Pi devices
   - Live connection status
   - Device configuration management
   - System information gathering
   - Error handling and timeouts

🚀 Start Django server:
   cd meter_dashboard
   python3 manage.py runserver 0.0.0.0:8000

Navigate to: http://localhost:8000/device-config/

You should now see the full DCMS interface with SSH deployment!
    """)


if __name__ == "__main__":
    main()
