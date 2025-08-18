
import json
import os
import paramiko
from django.conf import settings
from django.utils import timezone
from .models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment
import logging

logger = logging.getLogger(__name__)

class ConfigurationDeploymentService:
	"""Service to handle deployment of configurations to Raspberry Pi devices"""

	def __init__(self):
		self.default_ssh_username = getattr(settings, 'PI_SSH_USERNAME', 'pi')
		self.default_ssh_password = getattr(settings, 'PI_SSH_PASSWORD', 'raspberry')
		self.default_ssh_key_path = getattr(settings, 'PI_SSH_KEY_PATH', None)
		self.default_config_path = getattr(settings, 'PI_CONFIG_PATH', '/home/pi/meter_config/')

	def _get_pi_ssh_config(self, raspberry_pi):
		return {
			'username': raspberry_pi.ssh_username or self.default_ssh_username,
			'password': raspberry_pi.ssh_password or self.default_ssh_password,
			'key_path': raspberry_pi.ssh_key_path or self.default_ssh_key_path,
			'port': raspberry_pi.ssh_port or 22,
			'config_path': raspberry_pi.config_path or self.default_config_path,
		}

	def deploy_device_config(self, raspberry_pi_id):
		try:
			raspberry_pi = RaspberryPi.objects.get(id=raspberry_pi_id, is_active=True)
			deployment = ConfigurationDeployment.objects.create(
				raspberry_pi=raspberry_pi,
				deployment_type='DEVICE_CONFIG',
				status='IN_PROGRESS'
			)
			meters = MeterDevice.objects.filter(raspberry_pi=raspberry_pi, is_active=True)
			device_config = [
				{
					'meter_name': m.meter_name,
					'meter_address': m.meter_address,
					'meter_model': m.meter_model,
					'location': m.location,
					'pi_ip': raspberry_pi.pi_ip,
					'pi_name': raspberry_pi.pi_name
				} for m in meters
			]
			success = self._deploy_file_to_pi(
				raspberry_pi,
				'device_config.json',
				json.dumps(device_config, indent=2)
			)
			deployment.status = 'SUCCESS' if success else 'FAILED'
			deployment.completed_at = timezone.now()
			if not success:
				deployment.error_message = "Failed to deploy device configuration"
			deployment.save()
			return deployment
		except Exception as e:
			logger.error(f"Error deploying device config to Pi {raspberry_pi_id}: {str(e)}")
			if 'deployment' in locals():
				deployment.status = 'FAILED'
				deployment.error_message = str(e)
				deployment.completed_at = timezone.now()
				deployment.save()
			return None

	def deploy_system_config(self, raspberry_pi_id):
		try:
			raspberry_pi = RaspberryPi.objects.get(id=raspberry_pi_id, is_active=True)
			deployment = ConfigurationDeployment.objects.create(
				raspberry_pi=raspberry_pi,
				deployment_type='SYSTEM_CONFIG',
				status='IN_PROGRESS'
			)
			system_config, created = SystemConfiguration.objects.get_or_create(raspberry_pi=raspberry_pi)
			config_data = system_config.to_json()
			success = self._deploy_file_to_pi(
				raspberry_pi,
				'config.json',
				json.dumps(config_data, indent=2)
			)
			deployment.status = 'SUCCESS' if success else 'FAILED'
			deployment.completed_at = timezone.now()
			if not success:
				deployment.error_message = "Failed to deploy system configuration"
			deployment.save()
			return deployment
		except Exception as e:
			logger.error(f"Error deploying system config to Pi {raspberry_pi_id}: {str(e)}")
			if 'deployment' in locals():
				deployment.status = 'FAILED'
				deployment.error_message = str(e)
				deployment.completed_at = timezone.now()
				deployment.save()
			return None

	def deploy_both_configs(self, raspberry_pi_id):
		try:
			raspberry_pi = RaspberryPi.objects.get(id=raspberry_pi_id, is_active=True)
			deployment = ConfigurationDeployment.objects.create(
				raspberry_pi=raspberry_pi,
				deployment_type='BOTH',
				status='IN_PROGRESS'
			)
			success_device = True
			success_system = True
			error_messages = []
			try:
				meters = MeterDevice.objects.filter(raspberry_pi=raspberry_pi, is_active=True)
				device_config = [
					{
						'meter_name': m.meter_name,
						'meter_address': m.meter_address,
						'meter_model': m.meter_model,
						'location': m.location,
						'pi_ip': raspberry_pi.pi_ip,
						'pi_name': raspberry_pi.pi_name
					} for m in meters
				]
				success_device = self._deploy_file_to_pi(
					raspberry_pi,
					'device_config.json',
					json.dumps(device_config, indent=2)
				)
				if not success_device:
					error_messages.append("Failed to deploy device configuration")
			except Exception as e:
				success_device = False
				error_messages.append(f"Device config error: {str(e)}")
			try:
				system_config, created = SystemConfiguration.objects.get_or_create(raspberry_pi=raspberry_pi)
				config_data = system_config.to_json()
				success_system = self._deploy_file_to_pi(
					raspberry_pi,
					'config.json',
					json.dumps(config_data, indent=2)
				)
				if not success_system:
					error_messages.append("Failed to deploy system configuration")
			except Exception as e:
				success_system = False
				error_messages.append(f"System config error: {str(e)}")
			overall_success = success_device and success_system
			deployment.status = 'SUCCESS' if overall_success else 'FAILED'
			deployment.completed_at = timezone.now()
			if error_messages:
				deployment.error_message = "; ".join(error_messages)
			deployment.save()
			return deployment
		except Exception as e:
			logger.error(f"Error deploying both configs to Pi {raspberry_pi_id}: {str(e)}")
			if 'deployment' in locals():
				deployment.status = 'FAILED'
				deployment.error_message = str(e)
				deployment.completed_at = timezone.now()
				deployment.save()
			return None

	def _deploy_file_to_pi(self, raspberry_pi, filename, content):
		try:
			ssh_config = self._get_pi_ssh_config(raspberry_pi)
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			connect_kwargs = {
				'hostname': raspberry_pi.pi_ip,
				'username': ssh_config['username'],
				'port': ssh_config['port'],
				'timeout': 30
			}
			if ssh_config['key_path'] and os.path.exists(ssh_config['key_path']):
				connect_kwargs['key_filename'] = ssh_config['key_path']
			else:
				connect_kwargs['password'] = ssh_config['password']
			ssh.connect(**connect_kwargs)
			ssh.exec_command(f'mkdir -p {ssh_config["config_path"]}')
			sftp = ssh.open_sftp()
			remote_path = f"{ssh_config['config_path']}/{filename}"
			with sftp.file(remote_path, 'w') as remote_file:
				remote_file.write(content)
			sftp.close()
			ssh.close()
			return True
		except Exception as e:
			logger.error(f"Failed to deploy {filename} to {raspberry_pi.pi_ip}: {str(e)}")
			return False

	def test_pi_connection(self, raspberry_pi):
		try:
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
			stdin, stdout, stderr = ssh.exec_command('echo "Connection test successful"')
			result = stdout.read().decode()
			ssh.close()
			return True, result.strip()
		except Exception as e:
			return False, str(e)

	def get_pi_status(self, raspberry_pi):
		try:
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
			for filename in ['device_config.json', 'config.json']:
				file_path = f"{ssh_config['config_path']}/{filename}"
				stdin, stdout, stderr = ssh.exec_command(f'test -f {file_path} && echo "exists" || echo "missing"')
				status[filename] = stdout.read().decode().strip()
			stdin, stdout, stderr = ssh.exec_command('uptime')
			status['uptime'] = stdout.read().decode().strip()
			stdin, stdout, stderr = ssh.exec_command('df -h /')
			status['disk_usage'] = stdout.read().decode().strip()
			ssh.close()
			return True, status
		except Exception as e:
			return False, {"error": str(e)}
