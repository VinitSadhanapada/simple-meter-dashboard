


from django.db import models
from django.core.validators import RegexValidator
import json

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
		max_length=100, blank=True, help_text="SSH password (leave blank if using key)")
	ssh_key_path = models.CharField(
		max_length=500, blank=True, help_text="Path to SSH private key file")
	ssh_port = models.PositiveIntegerField(
		default=22, help_text="SSH port number")
	config_path = models.CharField(max_length=200, default='/home/pi/meter_config',
								   help_text="Path where config files are stored on Pi")
	ssh_status = models.BooleanField(default=False, help_text="Last known SSH status (auto-updated)")

	last_updated = models.DateTimeField(auto_now=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = "Raspberry Pi"
		verbose_name_plural = "Raspberry Pis"

	def __str__(self):
		return f"{self.pi_name} ({self.pi_ip})"


class MeterDevice(models.Model):
	"""Model to store meter device configuration"""
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
		unique_together = ['meter_address', 'raspberry_pi']
		verbose_name = "Meter Device"
		verbose_name_plural = "Meter Devices"

	def __str__(self):
		return f"{self.meter_name} - {self.meter_model} (Address: {self.meter_address})"

	def clean(self):
		from django.core.exceptions import ValidationError
		if not self.raspberry_pi_id:
			return
		self.location = self.raspberry_pi.location
		if MeterDevice.objects.exclude(pk=self.pk).filter(raspberry_pi=self.raspberry_pi, meter_address=self.meter_address).exists():
			raise ValidationError(
				f"A meter with address {self.meter_address} already exists for this Raspberry Pi."
			)

	def save(self, *args, **kwargs):
		if self.raspberry_pi:
			self.location = self.raspberry_pi.location
		super().save(*args, **kwargs)

	@classmethod
	def get_available_meter_models(cls):
		predefined = [model[0] for model in cls.PREDEFINED_METER_MODELS]
		custom_models = cls.objects.exclude(
			meter_model__in=predefined
		).values_list('meter_model', flat=True).distinct()
		all_models = list(set(predefined + list(custom_models)))
		all_models.sort()
		return [(model, model) for model in all_models]

	@classmethod
	def get_predefined_choices(cls):
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
	last_updated = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = "System Configuration"
		verbose_name_plural = "System Configurations"

	def __str__(self):
		return f"Config for {self.raspberry_pi.pi_name}"

	def to_json(self):
		return {
			"SIMULATION_MODE": self.simulation_mode,
			"READING_INTERVAL": self.reading_interval,
			"INTER_DEVICE_DELAY": self.inter_device_delay,
			"PORT": self.port,
			"ENABLE_MQTT": self.enable_mqtt,
			"ENABLE_RTC": self.enable_rtc
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
		verbose_name = "Configuration Deployment"
		verbose_name_plural = "Configuration Deployments"
		ordering = ['-deployed_at']

	def __str__(self):
		return f"{self.deployment_type} to {self.raspberry_pi.pi_name} - {self.status}"
