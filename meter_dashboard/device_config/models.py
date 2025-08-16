from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
import json
import os
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SSHKeyManager:
    """Utility class for managing SSH keys and connections to Raspberry Pi devices"""

    @staticmethod
    def generate_ssh_key(key_path: str, key_name: str = "pi_management") -> Tuple[bool, str]:
        """
        Generate SSH key pair if it doesn't exist

        Args:
            key_path: Directory where to store the key
            key_name: Name of the key file

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            import subprocess
            # Ensure the .ssh directory exists
            os.makedirs(key_path, mode=0o700, exist_ok=True)

            private_key_path = os.path.join(key_path, key_name)
            public_key_path = f"{private_key_path}.pub"

            # Check if key already exists
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                return True, f"SSH key already exists at {private_key_path}"

            # Generate new SSH key
            cmd = [
                "ssh-keygen",
                "-t", "rsa",
                "-b", "4096",
                "-f", private_key_path,
                "-N", "",  # No passphrase
                "-C", f"Django Device Manager - {key_name}"
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            # Set proper permissions
            os.chmod(private_key_path, 0o600)
            os.chmod(public_key_path, 0o644)

            logger.info(
                f"SSH key generated successfully at {private_key_path}")
            return True, f"SSH key generated successfully at {private_key_path}"

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to generate SSH key: {e.stderr}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error generating SSH key: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def copy_ssh_key_to_pi(pi_ip: str, username: str, password: str,
                           public_key_path: str, ssh_port: int = 22) -> Tuple[bool, str]:
        """
        Copy SSH public key to Raspberry Pi

        Args:
            pi_ip: IP address of the Pi
            username: SSH username
            password: SSH password
            public_key_path: Path to public key file
            ssh_port: SSH port number

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            import subprocess
            # Check if sshpass is available
            if subprocess.run(["which", "sshpass"], capture_output=True).returncode != 0:
                return False, "sshpass is not installed. Please install it: sudo apt install sshpass"

            # Check if public key exists
            if not os.path.exists(public_key_path):
                return False, f"Public key not found at {public_key_path}"

            # Copy SSH key using ssh-copy-id with sshpass
            cmd = [
                "sshpass", "-p", password,
                "ssh-copy-id",
                "-i", public_key_path,
                "-p", str(ssh_port),
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                f"{username}@{pi_ip}"
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            logger.info(f"SSH key copied successfully to {username}@{pi_ip}")
            return True, f"SSH key copied successfully to {username}@{pi_ip}"

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to copy SSH key to Pi: {e.stderr}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error copying SSH key: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def test_ssh_connection(pi_ip: str, username: str, private_key_path: str,
                            ssh_port: int = 22) -> Tuple[bool, str]:
        """
        Test SSH connection using private key

        Args:
            pi_ip: IP address of the Pi
            username: SSH username
            private_key_path: Path to private key file
            ssh_port: SSH port number

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            import subprocess
            cmd = [
                "ssh",
                "-i", private_key_path,
                "-p", str(ssh_port),
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "ConnectTimeout=10",
                f"{username}@{pi_ip}",
                "echo 'SSH connection successful'"
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True)

            if "SSH connection successful" in result.stdout:
                return True, "SSH connection successful"
            else:
                return False, "SSH connection failed - unexpected response"

        except subprocess.CalledProcessError as e:
            error_msg = f"SSH connection failed: {e.stderr}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error testing SSH connection: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


class RaspberryPi(models.Model):
    """Model to store Raspberry Pi information"""
    pi_name = models.CharField(max_length=100, unique=True)
    pi_ip = models.GenericIPAddressField(unique=True)
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    # SSH Configuration fields
    ssh_username = models.CharField(
        max_length=50, default='pi', help_text="SSH username for this Pi")
    ssh_password = models.CharField(
        max_length=100, blank=True, help_text="SSH password (temporary - used only for initial key setup)")
    ssh_key_path = models.CharField(
        max_length=500, blank=True, help_text="Path to SSH private key file")
    ssh_port = models.PositiveIntegerField(
        default=22, help_text="SSH port number")
    config_path = models.CharField(max_length=200, default='/home/pi/meter_config',
                                   help_text="Path where config files are stored on Pi")

    # SSH Key Setup Status
    ssh_key_configured = models.BooleanField(
        default=False, help_text="Whether SSH key has been set up for this Pi")
    ssh_setup_error = models.TextField(
        blank=True, help_text="Last error encountered during SSH setup")

    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'device_config_raspberrypi'
        verbose_name = "Raspberry Pi"
        verbose_name_plural = "Raspberry Pis"

    def __str__(self):
        return f"{self.pi_name} ({self.pi_ip})"

    def get_ssh_key_path(self):
        """Get the path to the SSH private key for this Pi"""
        if self.ssh_key_path:
            return self.ssh_key_path

        # Default path: ~/.ssh/pi_{pi_name}
        home = os.path.expanduser("~")
        key_name = f"pi_{self.pi_name.lower().replace(' ', '_')}"
        return os.path.join(home, ".ssh", key_name)

    def setup_ssh_key(self, force_regenerate=False):
        """
        Set up SSH key for this Raspberry Pi

        Args:
            force_regenerate: Whether to regenerate key even if it exists

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Clear previous errors
            self.ssh_setup_error = ""

            if not self.ssh_password:
                error_msg = "SSH password is required for initial key setup"
                self.ssh_setup_error = error_msg
                self.save()
                return False, error_msg

            # Get or set SSH key path
            private_key_path = self.get_ssh_key_path()
            public_key_path = f"{private_key_path}.pub"
            key_dir = os.path.dirname(private_key_path)
            key_name = os.path.basename(private_key_path)

            # Step 1: Generate SSH key if needed
            if force_regenerate or not os.path.exists(private_key_path):
                success, message = SSHKeyManager.generate_ssh_key(
                    key_dir, key_name)
                if not success:
                    self.ssh_setup_error = message
                    self.save()
                    return False, message

            # Step 2: Copy SSH key to Pi
            success, message = SSHKeyManager.copy_ssh_key_to_pi(
                pi_ip=self.pi_ip,
                username=self.ssh_username,
                password=self.ssh_password,
                public_key_path=public_key_path,
                ssh_port=self.ssh_port
            )

            if not success:
                self.ssh_setup_error = message
                self.save()
                return False, message

            # Step 3: Test SSH connection
            success, test_message = SSHKeyManager.test_ssh_connection(
                pi_ip=self.pi_ip,
                username=self.ssh_username,
                private_key_path=private_key_path,
                ssh_port=self.ssh_port
            )

            if success:
                # Update model
                self.ssh_key_path = private_key_path
                self.ssh_key_configured = True
                self.ssh_setup_error = ""
                self.save()

                return True, f"SSH key setup completed successfully. {message} {test_message}"
            else:
                error_msg = f"SSH key copied but connection test failed: {test_message}"
                self.ssh_setup_error = error_msg
                self.save()
                return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error during SSH setup: {str(e)}"
            self.ssh_setup_error = error_msg
            self.save()
            return False, error_msg

    def test_ssh_connection(self):
        """Test SSH connection to this Pi"""
        if not self.ssh_key_configured or not self.ssh_key_path:
            return False, "SSH key not configured. Please run setup_ssh_key() first."

        return SSHKeyManager.test_ssh_connection(
            pi_ip=self.pi_ip,
            username=self.ssh_username,
            private_key_path=self.ssh_key_path,
            ssh_port=self.ssh_port
        )


class MeterDevice(models.Model):
    """Model to store meter device configuration"""
    # Predefined meter models for common use
    PREDEFINED_METER_MODELS = [
        ('LG6400', 'LG6400'),
        ('LG+5220', 'LG+5220'),
        ('LG+5310', 'LG+5310'),
        ('LG+5230', 'LG+5230'),
        ('LG+5240', 'LG+5240'),
        ('LG+5250', 'LG+5250'),
    ]

    meter_name = models.CharField(max_length=100)
    meter_address = models.PositiveIntegerField()
    meter_model = models.CharField(
        max_length=100,
        help_text="Select from common models or enter a custom model name"
    )
    location = models.CharField(max_length=200)
    raspberry_pi = models.ForeignKey(
        RaspberryPi, on_delete=models.CASCADE, related_name='meters')
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'device_config_meterdevice'
        unique_together = ['meter_address', 'raspberry_pi']
        verbose_name = "Meter Device"
        verbose_name_plural = "Meter Devices"

    def __str__(self):
        return f"{self.meter_name} - {self.meter_model} (Address: {self.meter_address})"

    @classmethod
    def get_available_meter_models(cls):
        """Get all available meter models (predefined + custom ones from database)"""
        # Get predefined models
        predefined = [model[0] for model in cls.PREDEFINED_METER_MODELS]

        # Get custom models from database (excluding predefined ones)
        custom_models = cls.objects.exclude(
            meter_model__in=predefined
        ).values_list('meter_model', flat=True).distinct()

        # Combine and sort
        all_models = list(set(predefined + list(custom_models)))
        all_models.sort()

        return [(model, model) for model in all_models]

    @classmethod
    def get_predefined_choices(cls):
        """Get predefined meter model choices for forms"""
        return cls.PREDEFINED_METER_MODELS


class SystemConfiguration(models.Model):
    """Model to store system configuration for each Raspberry Pi"""
    raspberry_pi = models.OneToOneField(
        RaspberryPi, on_delete=models.CASCADE, related_name='system_config')
    simulation_mode = models.BooleanField(
        default=False, help_text="Set true to simulate readings")
    reading_interval = models.PositiveIntegerField(
        default=30, help_text="Seconds between reading cycles")
    inter_device_delay = models.FloatField(
        default=0.1, help_text="Delay (seconds) between device reads")
    port = models.CharField(
        max_length=50, default="/dev/ttyUSB0", help_text="Serial port for Modbus")
    enable_mqtt = models.BooleanField(
        default=False, help_text="Enable MQTT publishing")
    enable_rtc = models.BooleanField(
        default=True, help_text="Enable RTC for offline time keeping")

    LOG_LEVELS = [
        ('DEBUG', 'DEBUG'),
        ('INFO', 'INFO'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
        ('CRITICAL', 'CRITICAL'),
    ]
    log_level = models.CharField(
        max_length=10, choices=LOG_LEVELS, default='INFO', help_text="Logging level")
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'device_config_systemconfiguration'
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"

    def __str__(self):
        return f"Config for {self.raspberry_pi.pi_name}"

    def to_json(self):
        """Convert configuration to JSON format"""
        return {
            "SIMULATION_MODE": self.simulation_mode,
            "READING_INTERVAL": self.reading_interval,
            "INTER_DEVICE_DELAY": self.inter_device_delay,
            "PORT": self.port,
            "ENABLE_MQTT": self.enable_mqtt,
            "ENABLE_RTC": self.enable_rtc,
            "LOG_LEVEL": self.log_level
        }


class ConfigurationDeployment(models.Model):
    """Model to track configuration deployments to Raspberry Pis"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    raspberry_pi = models.ForeignKey(
        RaspberryPi, on_delete=models.CASCADE, related_name='deployments')
    deployment_type = models.CharField(max_length=20, choices=[
        ('DEVICE_CONFIG', 'Device Configuration'),
        ('SYSTEM_CONFIG', 'System Configuration'),
        ('BOTH', 'Both Configurations'),
    ])
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True)
    deployed_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'device_config_configurationdeployment'
        verbose_name = "Configuration Deployment"
        verbose_name_plural = "Configuration Deployments"
        ordering = ['-deployed_at']

    def __str__(self):
        return f"{self.deployment_type} to {self.raspberry_pi.pi_name} - {self.status}"
