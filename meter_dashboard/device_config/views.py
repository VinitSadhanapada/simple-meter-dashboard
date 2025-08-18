from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import os
import socket
import paramiko
import time
import threading
from pathlib import Path
import logging

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

        except Exception as e:
            logger.error(f"Error loading device configs: {e}")

        context = {
            'pi_configs': devices,  # For backward compatibility
            'devices': devices,     # For DCMS templates
            'page_title': 'Device Configuration Management',
            'total_devices': len(devices),
            'online_devices': len([d for d in devices if d['connection_status'] == 'online']),
            'active_devices': len([d for d in devices if d['is_active']]),
        }

        return render(request, 'device_config/device_config.html', context)

    def _check_device_status(self, config):
        """Check live status of device via SSH"""
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

            # Get system uptime for last connected info
            stdin, stdout, stderr = ssh.exec_command('uptime')
            uptime_info = stdout.read().decode().strip()

            ssh.close()
            return 'online', 'Just now'

        except Exception as e:
            logger.debug(
                f"Device {config.get('pi_name', 'Unknown')} offline: {e}")
            return 'offline', 'Never'


class AddPiView(View):
    """Add new Pi configuration"""

    def get(self, request):
        """Display add Pi form"""
        context = {
            'page_title': 'Add New Device',
            'form_title': 'Add Raspberry Pi Device',
        }
        return render(request, 'device_config/add_pi.html', context)

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
            return redirect('device_config:device_config')

        except Exception as e:
            logger.error(f"Error adding Pi: {e}")
            messages.error(request, f"Error adding Pi: {str(e)}")
            return redirect('device_config:add_pi')

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
            return redirect('device_config:device_config')

        context = {
            'pi_config': pi_config,
            'device': pi_config,  # For DCMS template compatibility
            'pi_id': pi_id,
            'device_id': pi_id,   # For DCMS template compatibility
            'page_title': f'Edit Device: {pi_config.get("pi_name", "Unknown")}',
            'form_title': f'Edit {pi_config.get("pi_name", "Device")}',
        }
        return render(request, 'device_config/edit_pi.html', context)

    def post(self, request, pi_id):
        """Handle Pi configuration update"""
        try:
            # Load existing configs
            config_file = Path(__file__).parent.parent / 'device_configs.json'
            with open(config_file, 'r') as f:
                configs = json.load(f)

            if pi_id >= len(configs):
                messages.error(request, "Pi configuration not found")
                return redirect('device_config:device_config')

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
            return redirect('device_config:device_config')

        except Exception as e:
            logger.error(f"Error updating Pi: {e}")
            messages.error(request, f"Error updating Pi: {str(e)}")
            return redirect('device_config:edit_pi', pi_id=pi_id)

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

        return redirect('device_config:device_config')


class DeployConfigView(View):
    """Deploy configuration to Pi via SSH - FULL IMPLEMENTATION"""

    def post(self, request, pi_id):
        """Deploy configuration to specific Pi via SSH"""
        try:
            pi_config = self._get_pi_config(pi_id)
            if not pi_config:
                return JsonResponse({'success': False, 'error': 'Pi configuration not found'})

            # Test connection first
            if not self._test_ssh_connection(pi_config):
                return JsonResponse({'success': False, 'error': 'Cannot connect to Pi via SSH. Check credentials and network.'})

            # Generate device_config.jsonc for this Pi - EXACT FORMAT ONLY
            device_config = []
            for meter in pi_config['meters']:
                device_config.append({
                    'meter_name': meter['meter_name'],
                    'meter_address': meter['meter_address'],
                    'meter_model': meter['meter_model'],
                    'location': meter['location'],
                    'pi_ip': pi_config['pi_ip'],
                    'pi_name': pi_config['pi_name']
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
            device_config_content = f'''// Device configuration for {pi_config["pi_name"]}
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

            # Also copy other necessary config files if they exist
            local_config_files = [
                Path(__file__).parent.parent.parent / 'config.jsonc',
                Path(__file__).parent.parent.parent / 'macros.py',
                Path(__file__).parent.parent.parent / 'postgres_helper.py'
            ]

            for local_file in local_config_files:
                if local_file.exists():
                    try:
                        remote_file = f'{config_path}/{local_file.name}'
                        sftp.put(str(local_file), remote_file)
                        ssh.exec_command(f'chmod 644 {remote_file}')
                    except Exception as e:
                        logger.warning(
                            f"Could not upload {local_file.name}: {e}")

            # Clean up temp file
            os.remove(temp_file)

            # Restart MFM service if it exists
            try:
                stdin, stdout, stderr = ssh.exec_command(
                    'sudo systemctl restart mfm-dashboard || echo "Service not found"')
                restart_output = stdout.read().decode().strip()
            except:
                pass

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


class LiveStatusView(View):
    """AJAX endpoint for live status updates"""

    def get(self, request):
        """Get live status of all devices"""
        try:
            config_file = Path(__file__).parent.parent / 'device_configs.json'
            if not config_file.exists():
                return JsonResponse({'devices': []})

            with open(config_file, 'r') as f:
                pi_configs = json.load(f)

            devices_status = []

            # Check status of each device in parallel for faster response
            def check_device(i, config):
                connection_status, last_connected = self._check_device_status(
                    config)
                return {
                    'id': i,
                    'pi_name': config.get('pi_name', ''),
                    'connection_status': connection_status,
                    'last_connected': last_connected,
                    'status': 'Online' if connection_status == 'online' else 'Offline'
                }

            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(check_device, i, config)
                           for i, config in enumerate(pi_configs)]
                for future in concurrent.futures.as_completed(futures):
                    devices_status.append(future.result())

            # Sort by device ID to maintain order
            devices_status.sort(key=lambda x: x['id'])

            return JsonResponse({
                'devices': devices_status,
                'total_devices': len(devices_status),
                'online_devices': len([d for d in devices_status if d['connection_status'] == 'online'])
            })

        except Exception as e:
            logger.error(f"Error getting live status: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    def _check_device_status(self, config):
        """Check live status of device via SSH"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Try SSH connection with short timeout for status check
            if config.get('ssh_key_path') and os.path.exists(config['ssh_key_path']):
                ssh.connect(
                    hostname=config['pi_ip'],
                    username=config.get('ssh_username', 'pi'),
                    key_filename=config['ssh_key_path'],
                    timeout=2
                )
            else:
                ssh.connect(
                    hostname=config['pi_ip'],
                    username=config.get('ssh_username', 'pi'),
                    password=config.get('ssh_password', ''),
                    timeout=2
                )

            ssh.close()
            return 'online', 'Just now'

        except Exception:
            return 'offline', 'Connection failed'


class DeployAllView(View):
    """Deploy configuration to all active devices"""

    def post(self, request):
        """Deploy to all active devices"""
        try:
            config_file = Path(__file__).parent.parent / 'device_configs.json'
            if not config_file.exists():
                return JsonResponse({'success': False, 'error': 'No devices configured'})

            with open(config_file, 'r') as f:
                pi_configs = json.load(f)

            results = []

            for i, config in enumerate(pi_configs):
                if not config.get('is_active', True):
                    continue

                # Generate device config
                device_config = []
                for meter in config.get('meters', []):
                    device_config.append({
                        'meter_name': meter['meter_name'],
                        'meter_address': meter['meter_address'],
                        'meter_model': meter['meter_model'],
                        'location': meter['location'],
                        'pi_name': config['pi_name'],
                        'pi_ip': config['pi_ip']
                    })

                # Deploy to this Pi
                deploy_view = DeployConfigView()
                success, message = deploy_view._deploy_to_pi(
                    config, device_config)

                results.append({
                    'pi_name': config['pi_name'],
                    'success': success,
                    'message': message
                })

            successful = len([r for r in results if r['success']])
            total = len(results)

            return JsonResponse({
                'success': True,
                'message': f"Deployment complete: {successful}/{total} devices successful",
                'results': results
            })

        except Exception as e:
            logger.error(f"Error in bulk deployment: {e}")
            return JsonResponse({'success': False, 'error': str(e)})


# Compatibility aliases for DCMS templates
AddDeviceView = AddPiView
EditDeviceView = EditPiView
DeleteDeviceView = DeletePiView


class DeviceDashboardView(View):
    """Old-style device dashboard view"""

    def get(self, request):
        """Display old-style device dashboard"""
        return DeviceConfigView().get(request)


# Add URL alias for old-style dashboard
DeviceDashboardOldView = DeviceDashboardView


class PiDetailView(View):
    """Pi detail view for URLs like /device-config/pi/2/"""

    def get(self, request, pi_id):
        """Display detailed view of a specific Pi"""
        pi_config = self._get_pi_config(pi_id)
        if not pi_config:
            messages.error(request, "Pi configuration not found")
            return redirect('device_config:device_list')

        # Check live connection status
        connection_status, last_connected = self._check_device_status(
            pi_config)

        device = {
            'id': pi_id,
            'pi_name': pi_config.get('pi_name', ''),
            'pi_ip': pi_config.get('pi_ip', ''),
            'location': pi_config.get('location', ''),
            'ssh_username': pi_config.get('ssh_username', 'pi'),
            'ssh_password': pi_config.get('ssh_password', ''),
            'ssh_key_path': pi_config.get('ssh_key_path', ''),
            'config_path': pi_config.get('config_path', ''),
            'description': pi_config.get('description', ''),
            'contact_person': pi_config.get('contact_person', ''),
            'is_active': pi_config.get('is_active', True),
            'meters': pi_config.get('meters', []),
            'meter_count': len(pi_config.get('meters', [])),
            'last_connected': last_connected,
            'connection_status': connection_status,
            'status': 'Online' if connection_status == 'online' else 'Offline',
            'status_class': 'success' if connection_status == 'online' else 'danger'
        }

        context = {
            'device': device,
            'pi_config': pi_config,  # For backward compatibility
            'pi_id': pi_id,
            'page_title': f'Device Details: {device["pi_name"]}',
        }

        return render(request, 'device_config/pi_detail.html', context)

    def _get_pi_config(self, pi_id):
        """Get Pi configuration by ID"""
        try:
            config_file = Path(__file__).parent.parent / 'device_configs.json'
            with open(config_file, 'r') as f:
                configs = json.load(f)
            return configs[pi_id] if pi_id < len(configs) else None
        except:
            return None

    def _check_device_status(self, config):
        """Check live status of device via SSH"""
        try:
            import paramiko
            ssh_available = True
        except ImportError:
            ssh_available = False

        if not ssh_available:
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
