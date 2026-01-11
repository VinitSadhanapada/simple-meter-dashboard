import json
import os
import requests
from io import StringIO
import logging
import uuid

logger = logging.getLogger(__name__)

# Paramiko is optional: if not installed, we'll disable SSH deployment gracefully
try:
    import paramiko  # type: ignore
    _PARAMIKO_AVAILABLE = True
except ImportError as e:  # pragma: no cover
    _PARAMIKO_AVAILABLE = False
    logger.warning(
        "Paramiko not available (%s). Configuration deployments will be skipped.", e
    )
from django.conf import settings
from django.utils import timezone
from .models import RaspberryPi, MeterDevice, SystemConfiguration, ConfigurationDeployment
from .serializers import MeterDeviceJSONSerializer


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
        # Normalize config path to be absolute
        raw_path = raspberry_pi.config_path or self.default_config_path
        config_path = raw_path if str(raw_path).startswith('/') else f'/{raw_path}'
        return {
            'username': raspberry_pi.ssh_username or self.default_ssh_username,
            'password': raspberry_pi.ssh_password or self.default_ssh_password,
            'key_path': raspberry_pi.ssh_key_path or self.default_ssh_key_path,
            'port': raspberry_pi.ssh_port or 22,
            'config_path': config_path,
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

            # Deploy to Raspberry Pi (legacy strict JSON only)
            content = json.dumps(device_config, indent=2)
            success = self._deploy_file_to_pi(
                raspberry_pi,
                'device_config.json',
                content
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

    def deploy_system_config(self, raspberry_pi_id, excludes: dict | None = None):
        """Deploy config.json to a specific Raspberry Pi.
        If excludes is provided, conditionally omit sections from the pushed JSON.
        excludes keys: reading, mqtt, usb_copy, cloud_sync, logging, legacy_network (bools)
        """
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
            excludes = excludes or {}
            # Apply section excludes by removing relevant keys
            if excludes.get('reading'):
                for k in [
                    'SIMULATION_MODE', 'READING_INTERVAL', 'INTER_DEVICE_DELAY',
                    'PORT', 'ENABLE_RTC', 'ENABLE_CSV_WRITE'
                ]:
                    config_data.pop(k, None)
            if excludes.get('mqtt'):
                config_data.pop('ENABLE_MQTT', None)
                config_data.pop('MQTT', None)
            if excludes.get('usb_copy'):
                config_data.pop('usb_copy', None)
            if excludes.get('cloud_sync'):
                config_data.pop('cloud_sync', None)
            if excludes.get('logging'):
                config_data.pop('LOG_LEVEL', None)
            if excludes.get('legacy_network'):
                config_data.pop('DB_SERVER_IP', None)
                config_data.pop('SERVER_API_IP', None)

            # Deploy to Raspberry Pi (strict JSON only)
            content = json.dumps(config_data, indent=2)
            success = self._deploy_file_to_pi(
                raspberry_pi,
                'config.json',
                content
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

    def run_deployment(self, deployment_id: int):
        """Execute a ConfigurationDeployment respecting exclude flags for SYSTEM_CONFIG.
        Updates status and timestamps on the deployment object.
        """
        try:
            deployment = ConfigurationDeployment.objects.get(id=deployment_id)
            pi = deployment.raspberry_pi
            deployment.status = 'IN_PROGRESS'
            deployment.error_message = ''
            deployment.save()

            if deployment.deployment_type == 'DEVICE_CONFIG':
                result = self.deploy_device_config(pi.id)
                ok = bool(result and result.status == 'SUCCESS')
            elif deployment.deployment_type == 'SYSTEM_CONFIG':
                excludes = {
                    'reading': deployment.exclude_reading,
                    'mqtt': deployment.exclude_mqtt,
                    'usb_copy': deployment.exclude_usb_copy,
                    'cloud_sync': deployment.exclude_cloud_sync,
                    'logging': deployment.exclude_logging,
                    'legacy_network': deployment.exclude_legacy_network,
                }
                # Run and then reflect status on original deployment row
                # We call internal flow but override status here for the provided row.
                try:
                    raspberry_pi = pi
                    system_config, _ = SystemConfiguration.objects.get_or_create(raspberry_pi=raspberry_pi)
                    config_data = system_config.to_json()
                    if excludes.get('reading'):
                        for k in ['SIMULATION_MODE', 'READING_INTERVAL', 'INTER_DEVICE_DELAY', 'PORT', 'ENABLE_RTC', 'ENABLE_CSV_WRITE']:
                            config_data.pop(k, None)
                    if excludes.get('mqtt'):
                        config_data.pop('ENABLE_MQTT', None)
                        config_data.pop('MQTT', None)
                    if excludes.get('usb_copy'):
                        config_data.pop('usb_copy', None)
                    if excludes.get('cloud_sync'):
                        config_data.pop('cloud_sync', None)
                    if excludes.get('logging'):
                        config_data.pop('LOG_LEVEL', None)
                    if excludes.get('legacy_network'):
                        config_data.pop('DB_SERVER_IP', None)
                        config_data.pop('SERVER_API_IP', None)
                    content = json.dumps(config_data, indent=2)
                    ok = self._deploy_file_to_pi(raspberry_pi, 'config.json', content)
                except Exception as e:
                    ok = False
                    deployment.error_message = str(e)
            elif deployment.deployment_type == 'BOTH':
                # Deploy device config first
                res_dev = self.deploy_device_config(pi.id)
                ok_dev = bool(res_dev and res_dev.status == 'SUCCESS')
                # Then system config with excludes
                excludes = {
                    'reading': deployment.exclude_reading,
                    'mqtt': deployment.exclude_mqtt,
                    'usb_copy': deployment.exclude_usb_copy,
                    'cloud_sync': deployment.exclude_cloud_sync,
                    'logging': deployment.exclude_logging,
                    'legacy_network': deployment.exclude_legacy_network,
                }
                res_sys = self.deploy_system_config(pi.id, excludes)
                ok_sys = bool(res_sys and res_sys.status == 'SUCCESS')
                ok = ok_dev and ok_sys
                if not ok:
                    msgs = []
                    if not ok_dev:
                        msgs.append('Device config failed')
                    if not ok_sys:
                        msgs.append('System config failed')
                    deployment.error_message = '; '.join(msgs)
            else:
                ok = False
                deployment.error_message = f"Unknown deployment_type: {deployment.deployment_type}"

            deployment.status = 'SUCCESS' if ok else 'FAILED'
            deployment.completed_at = timezone.now()
            deployment.save()
            return deployment
        except Exception as e:
            try:
                deployment = ConfigurationDeployment.objects.get(id=deployment_id)
                deployment.status = 'FAILED'
                deployment.error_message = str(e)
                deployment.completed_at = timezone.now()
                deployment.save()
            except Exception:
                pass
            return None

    def deploy_both_configs(self, raspberry_pi_id, excludes: dict | None = None):
        """Deploy both device_config.json and config.json to a specific Raspberry Pi.
        If excludes provided, they are applied to the system config portion.
        """
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
                # Deploy device config (strict JSON only)
                content_device = json.dumps(device_config, indent=2)
                success_device = self._deploy_file_to_pi(
                    raspberry_pi,
                    'device_config.json',
                    content_device,
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
                excludes = excludes or {}
                if excludes.get('reading'):
                    for k in ['SIMULATION_MODE', 'READING_INTERVAL', 'INTER_DEVICE_DELAY', 'PORT', 'ENABLE_RTC', 'ENABLE_CSV_WRITE']:
                        config_data.pop(k, None)
                if excludes.get('mqtt'):
                    config_data.pop('ENABLE_MQTT', None)
                    config_data.pop('MQTT', None)
                if excludes.get('usb_copy'):
                    config_data.pop('usb_copy', None)
                if excludes.get('cloud_sync'):
                    config_data.pop('cloud_sync', None)
                if excludes.get('logging'):
                    config_data.pop('LOG_LEVEL', None)
                if excludes.get('legacy_network'):
                    config_data.pop('DB_SERVER_IP', None)
                    config_data.pop('SERVER_API_IP', None)
                content_system = json.dumps(config_data, indent=2)
                success_system = self._deploy_file_to_pi(
                    raspberry_pi,
                    'config.json',
                    content_system,
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
        """Deploy a file to Raspberry Pi via SSH.
        Returns False immediately if Paramiko is unavailable.
        """
        if not _PARAMIKO_AVAILABLE:
            logger.warning(
                "Skipping deployment of %s to %s because Paramiko is not installed.",
                filename,
                raspberry_pi.pi_ip,
            )
            return False

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
                logger.info(
                    "Connecting to %s using SSH key: %s", raspberry_pi.pi_ip, ssh_config['key_path']
                )
            else:
                connect_kwargs['password'] = ssh_config['password']
                logger.info(
                    "Connecting to %s using password authentication", raspberry_pi.pi_ip
                )

            ssh.connect(**connect_kwargs)
            # Ensure directory exists (running as the ssh user)
            ssh.exec_command(f'mkdir -p {ssh_config["config_path"]}')
            sftp = ssh.open_sftp()
            remote_path = f"{ssh_config['config_path']}/{filename}"
            try:
                # Try normal SFTP write first
                with sftp.file(remote_path, 'w') as remote_file:
                    remote_file.write(content)
                sftp.close()
                ssh.close()
                logger.info("Successfully deployed %s to %s", filename, raspberry_pi.pi_ip)
                return True
            except IOError as e:
                logger.warning("Permission error writing %s to %s: %s", remote_path, raspberry_pi.pi_ip, e)
                # Try direct sudo write using tee (requires passwordless sudo for the ssh user)
                try:
                    # Open a pty so sudo can run without tty issues
                    cmd = f"sudo tee {remote_path} > /dev/null && sudo chown {ssh_config['username']}:{ssh_config['username']} {remote_path} && sudo chmod 644 {remote_path}"
                    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
                    # send content to stdin of the remote tee
                    stdin.write(content)
                    stdin.channel.shutdown_write()
                    exit_status = stdout.channel.recv_exit_status()
                    stderr_out = stderr.read().decode()
                    if exit_status == 0:
                        ssh.close()
                        logger.info("Successfully deployed %s to %s via sudo tee", filename, raspberry_pi.pi_ip)
                        return True
                    else:
                        logger.warning("sudo tee failed for %s on %s: %s", remote_path, raspberry_pi.pi_ip, stderr_out)
                except Exception as e2:
                    logger.warning("sudo-tee attempt failed for %s on %s: %s", remote_path, raspberry_pi.pi_ip, e2)

                # Fallback: upload to /tmp and move into place with sudo
                try:
                    tmp_name = f"/tmp/{filename}.{uuid.uuid4().hex}"
                    with sftp.file(tmp_name, 'w') as tmpf:
                        tmpf.write(content)
                    sftp.close()
                    move_cmd = (
                        f"sudo mv {tmp_name} {remote_path} && "
                        f"sudo chown {ssh_config['username']}:{ssh_config['username']} {remote_path} && "
                        f"sudo chmod 644 {remote_path}"
                    )
                    stdin, stdout, stderr = ssh.exec_command(move_cmd)
                    exit_status = stdout.channel.recv_exit_status()
                    stderr_out = stderr.read().decode()
                    if exit_status == 0:
                        ssh.close()
                        logger.info("Successfully deployed %s to %s via sudo move", filename, raspberry_pi.pi_ip)
                        return True
                    else:
                        logger.error("Failed to move %s into place: %s", tmp_name, stderr_out)
                        ssh.close()
                        return False
                except Exception as e3:
                    logger.error("Fallback deploy failed for %s to %s: %s", filename, raspberry_pi.pi_ip, e3)
                    try:
                        sftp.close()
                    except Exception:
                        pass
                    ssh.close()
                    return False
        except Exception as e:
            logger.error(
                "Failed to deploy %s to %s: %s", filename, raspberry_pi.pi_ip, e
            )
            try:
                ssh.close()
            except Exception:
                pass
            return False

    def test_pi_connection(self, raspberry_pi):
        """Test SSH connection to a Raspberry Pi. Returns False if Paramiko missing."""
        if not _PARAMIKO_AVAILABLE:
            return False, "Paramiko not installed"
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
            result = stdout.read().decode().strip()
            ssh.close()
            return True, result
        except Exception as e:
            return False, str(e)

    def get_pi_status(self, raspberry_pi):
        """Get current status and configuration files from Raspberry Pi.
        Returns error if Paramiko unavailable.
        """
        if not _PARAMIKO_AVAILABLE:
            return False, {"error": "Paramiko not installed"}
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
            # Check for either strict JSON or JSONC variants so status shows
            # presence even if the Pi still has an older `*.jsonc` file.
            for filename in ['device_config.json', 'device_config.jsonc', 'config.json', 'config.jsonc']:
                file_path = f"{ssh_config['config_path']}/{filename}"
                stdin, stdout, stderr = ssh.exec_command(
                    f'test -f {file_path} && echo "exists" || echo "missing"'
                )
                status[filename] = stdout.read().decode().strip()
            stdin, stdout, stderr = ssh.exec_command('uptime')
            status['uptime'] = stdout.read().decode().strip()
            stdin, stdout, stderr = ssh.exec_command('df -h /')
            status['disk_usage'] = stdout.read().decode().strip()
            ssh.close()
            return True, status
        except Exception as e:
            return False, {"error": str(e)}
