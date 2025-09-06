import json
import os
import requests
import paramiko
from io import StringIO
from django.conf import settings
from django.utils import timezone
from .models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment
from .serializers import MeterDeviceJSONSerializer
import logging

logger = logging.getLogger(__name__)


class ConfigurationDeploymentService:
    """Service to handle deployment of configurations to Raspberry Pi devices"""

    def __init__(self):
        # Keep global defaults for backward compatibility
        self.default_ssh_username = getattr(settings, 'PI_SSH_USERNAME', 'pi')
        self.default_ssh_password = getattr(
            settings, 'PI_SSH_PASSWORD', 'raspberry')
        self.default_ssh_key_path = getattr(settings, 'PI_SSH_KEY_PATH', None)
        self.default_config_path = getattr(
            settings, 'PI_CONFIG_PATH', '/home/pi/meter_config/')

    def _get_pi_ssh_config(self, raspberry_pi):
        """Get SSH configuration for a specific Pi, with fallback to defaults"""
        return {
            'username': raspberry_pi.ssh_username or self.default_ssh_username,
            'password': raspberry_pi.ssh_password or self.default_ssh_password,
            'key_path': raspberry_pi.ssh_key_path or self.default_ssh_key_path,
            'port': raspberry_pi.ssh_port or 22,
            'config_path': raspberry_pi.config_path or self.default_config_path,
        }

    def deploy_device_config(self, raspberry_pi_id):
        """Deploy device_config.json to a specific Raspberry Pi"""
        try:
            raspberry_pi = RaspberryPi.objects.get(
                id=raspberry_pi_id, is_active=True)

            # Create deployment record
            deployment = ConfigurationDeployment.objects.create(
                raspberry_pi=raspberry_pi,
                deployment_type='DEVICE_CONFIG',
                status='IN_PROGRESS'
            )

            # Generate device config JSON
            meters = MeterDevice.objects.filter(
                raspberry_pi=raspberry_pi, is_active=True)
            device_config = [MeterDeviceJSONSerializer(
                meter).data for meter in meters]

            # Deploy to Raspberry Pi
            success = self._deploy_file_to_pi(
                raspberry_pi,
                'device_config.json',
                json.dumps(device_config, indent=2)
            )

            # Update deployment status
            deployment.status = 'SUCCESS' if success else 'FAILED'
            deployment.completed_at = timezone.now()
            if not success:
                deployment.error_message = "Failed to deploy device configuration"
            deployment.save()

            return deployment

        except Exception as e:
            logger.error(
                f"Error deploying device config to Pi {raspberry_pi_id}: {str(e)}")
            if 'deployment' in locals():
                deployment.status = 'FAILED'
                deployment.error_message = str(e)
                deployment.completed_at = timezone.now()
                deployment.save()
            return None

    def deploy_system_config(self, raspberry_pi_id):
        """Deploy config.json to a specific Raspberry Pi"""
        try:
            raspberry_pi = RaspberryPi.objects.get(
                id=raspberry_pi_id, is_active=True)

            # Create deployment record
            deployment = ConfigurationDeployment.objects.create(
                raspberry_pi=raspberry_pi,
                deployment_type='SYSTEM_CONFIG',
                status='IN_PROGRESS'
            )

            # Get or create system configuration
            system_config, created = SystemConfiguration.objects.get_or_create(
                raspberry_pi=raspberry_pi
            )

            # Generate system config JSON
            config_data = system_config.to_json()

            # Deploy to Raspberry Pi
            success = self._deploy_file_to_pi(
                raspberry_pi,
                'config.json',
                json.dumps(config_data, indent=2)
            )

            # Update deployment status
            deployment.status = 'SUCCESS' if success else 'FAILED'
            deployment.completed_at = timezone.now()
            if not success:
                deployment.error_message = "Failed to deploy system configuration"
            deployment.save()

            return deployment

        except Exception as e:
            logger.error(
                f"Error deploying system config to Pi {raspberry_pi_id}: {str(e)}")
            if 'deployment' in locals():
                deployment.status = 'FAILED'
                deployment.error_message = str(e)
                deployment.completed_at = timezone.now()
                deployment.save()
            return None

    def deploy_both_configs(self, raspberry_pi_id):
        """Deploy both device_config.json and config.json to a specific Raspberry Pi"""
        try:
            raspberry_pi = RaspberryPi.objects.get(
                id=raspberry_pi_id, is_active=True)

            # Create deployment record
            deployment = ConfigurationDeployment.objects.create(
                raspberry_pi=raspberry_pi,
                deployment_type='BOTH',
                status='IN_PROGRESS'
            )

            success_device = True
            success_system = True
            error_messages = []

            # Deploy device config
            try:
                meters = MeterDevice.objects.filter(
                    raspberry_pi=raspberry_pi, is_active=True)
                device_config = [MeterDeviceJSONSerializer(
                    meter).data for meter in meters]
                success_device = self._deploy_file_to_pi(
                    raspberry_pi,
                    'device_config.json',
                    json.dumps(device_config, indent=2)
                )
                if not success_device:
                    error_messages.append(
                        "Failed to deploy device configuration")
            except Exception as e:
                success_device = False
                error_messages.append(f"Device config error: {str(e)}")

            # Deploy system config
            try:
                system_config, created = SystemConfiguration.objects.get_or_create(
                    raspberry_pi=raspberry_pi
                )
                config_data = system_config.to_json()
                success_system = self._deploy_file_to_pi(
                    raspberry_pi,
                    'config.json',
                    json.dumps(config_data, indent=2)
                )
                if not success_system:
                    error_messages.append(
                        "Failed to deploy system configuration")
            except Exception as e:
                success_system = False
                error_messages.append(f"System config error: {str(e)}")

            # Update deployment status
            overall_success = success_device and success_system
            deployment.status = 'SUCCESS' if overall_success else 'FAILED'
            deployment.completed_at = timezone.now()
            if error_messages:
                deployment.error_message = "; ".join(error_messages)
            deployment.save()

            return deployment

        except Exception as e:
            logger.error(
                f"Error deploying both configs to Pi {raspberry_pi_id}: {str(e)}")
            if 'deployment' in locals():
                deployment.status = 'FAILED'
                deployment.error_message = str(e)
                deployment.completed_at = timezone.now()
                deployment.save()
            return None

    def _deploy_file_to_pi(self, raspberry_pi, filename, content):
        """Deploy a file to Raspberry Pi via SSH"""
        try:
            # Get SSH configuration for this specific Pi
            ssh_config = self._get_pi_ssh_config(raspberry_pi)

            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to Raspberry Pi - support both key and password auth
            connect_kwargs = {
                'hostname': raspberry_pi.pi_ip,
                'username': ssh_config['username'],
                'port': ssh_config['port'],
                'timeout': 30
            }

            if ssh_config['key_path'] and os.path.exists(ssh_config['key_path']):
                # Use SSH key authentication
                connect_kwargs['key_filename'] = ssh_config['key_path']
                logger.info(
                    f"Connecting to {raspberry_pi.pi_ip} using SSH key: {ssh_config['key_path']}")
            else:
                # Use password authentication
                connect_kwargs['password'] = ssh_config['password']
                logger.info(
                    f"Connecting to {raspberry_pi.pi_ip} using password authentication")

            ssh.connect(**connect_kwargs)

            # Create config directory if it doesn't exist
            ssh.exec_command(f'mkdir -p {ssh_config["config_path"]}')

            # Upload file
            sftp = ssh.open_sftp()
            remote_path = f"{ssh_config['config_path']}/{filename}"

            # Write content to remote file
            with sftp.file(remote_path, 'w') as remote_file:
                remote_file.write(content)

            sftp.close()
            ssh.close()

            logger.info(
                f"Successfully deployed {filename} to {raspberry_pi.pi_ip}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to deploy {filename} to {raspberry_pi.pi_ip}: {str(e)}")
            return False

    def test_pi_connection(self, raspberry_pi):
        """Test SSH connection to a Raspberry Pi"""
        try:
            # Get SSH configuration for this specific Pi
            ssh_config = self._get_pi_ssh_config(raspberry_pi)

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                'hostname': raspberry_pi.pi_ip,
                'username': ssh_config['username'],
                'port': ssh_config['port'],
                'timeout': 10
            }

            if ssh_config['key_path'] and os.path.exists(ssh_config['key_path']):
                connect_kwargs['key_filename'] = ssh_config['key_path']
            else:
                connect_kwargs['password'] = ssh_config['password']

            ssh.connect(**connect_kwargs)

            # Test command
            stdin, stdout, stderr = ssh.exec_command(
                'echo "Connection test successful"')
            result = stdout.read().decode()

            ssh.close()
            return True, result.strip()

        except Exception as e:
            return False, str(e)

    def get_pi_status(self, raspberry_pi):
        """Get current status and configuration files from Raspberry Pi"""
        try:
            # Get SSH configuration for this specific Pi
            ssh_config = self._get_pi_ssh_config(raspberry_pi)

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                'hostname': raspberry_pi.pi_ip,
                'username': ssh_config['username'],
                'port': ssh_config['port'],
                'timeout': 10
            }

            if ssh_config['key_path'] and os.path.exists(ssh_config['key_path']):
                connect_kwargs['key_filename'] = ssh_config['key_path']
            else:
                connect_kwargs['password'] = ssh_config['password']

            ssh.connect(**connect_kwargs)

            status = {}

            # Check if config files exist
            for filename in ['device_config.json', 'config.json']:
                file_path = f"{ssh_config['config_path']}/{filename}"
                stdin, stdout, stderr = ssh.exec_command(
                    f'test -f {file_path} && echo "exists" || echo "missing"')
                status[filename] = stdout.read().decode().strip()

            # Get system uptime
            stdin, stdout, stderr = ssh.exec_command('uptime')
            status['uptime'] = stdout.read().decode().strip()

            # Get disk usage
            stdin, stdout, stderr = ssh.exec_command('df -h /')
            status['disk_usage'] = stdout.read().decode().strip()

            ssh.close()
            return True, status

        except Exception as e:
            return False, {"error": str(e)}
