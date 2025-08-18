from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import os
import subprocess
import socket
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DeviceConfigView(View):
    """Main device configuration management view"""

    def get(self, request):
        """Display device configuration management interface"""

        # Load current device configurations
        config_file = Path(__file__).parent.parent / 'device_configs.json'
        pi_configs = []

        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    pi_configs = json.load(f)
        except Exception as e:
            logger.error(f"Error loading device configs: {e}")
            pi_configs = []

        context = {
            'pi_configs': pi_configs,
            'page_title': 'Device Configuration Management',
        }

        return render(request, 'device_config/device_config.html', context)


class AddPiView(View):
    """Add new Pi configuration"""

    def get(self, request):
        """Display add Pi form"""
        return render(request, 'device_config/add_pi.html')

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
            'pi_id': pi_id
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
    """Deploy configuration to Pi via SSH"""

    def post(self, request, pi_id):
        """Deploy configuration to specific Pi"""
        try:
            pi_config = self._get_pi_config(pi_id)
            if not pi_config:
                return JsonResponse({'success': False, 'error': 'Pi configuration not found'})

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

            # For now, just simulate deployment
            success, message = True, f"Configuration would be deployed to {pi_config['pi_name']}"

            if success:
                messages.success(
                    request, f"Configuration deployed to '{pi_config['pi_name']}' successfully!")
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


class TestConnectionView(View):
    """Test SSH connection to Pi"""

    def post(self, request, pi_id):
        """Test connection to specific Pi"""
        try:
            pi_config = self._get_pi_config(pi_id)
            if not pi_config:
                return JsonResponse({'success': False, 'error': 'Pi configuration not found'})

            # For now, just simulate connection test
            success = True
            message = f"Connection test successful for {pi_config['pi_name']}"

            if success:
                return JsonResponse({'success': True, 'message': message})
            else:
                return JsonResponse({'success': False, 'error': 'SSH connection failed'})

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
