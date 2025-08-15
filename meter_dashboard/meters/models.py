from django.db import models
from .encrypted_fields import EncryptedCharField


class DcmsPiSetup(models.Model):
    """
    DCMS Pi Setup table for managing Raspberry Pi devices
    """
    pi_name = models.CharField(max_length=100, unique=True)
    pi_ip = models.GenericIPAddressField(unique=True)
    location = models.CharField(max_length=100)
    ssh_username = models.CharField(max_length=50)
    ssh_password = EncryptedCharField(
        max_length=250, blank=True, help_text="Encrypted SSH password")  # Encrypted field
    ssh_key_path = EncryptedCharField(
        max_length=250, blank=True, help_text="Encrypted SSH key file path")  # Encrypted field
    config_path = models.CharField(max_length=255)  # Path to config file on Pi

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_connected = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'dcms_pi_setup'
        verbose_name = 'DCMS Pi Setup'
        verbose_name_plural = 'DCMS Pi Setups'

    def __str__(self):
        return f"{self.pi_name} ({self.pi_ip}) - {self.location}"


class EnvConfig(models.Model):
    """
    Environment configuration for each Pi device
    """
    pi_setup = models.OneToOneField(
        DcmsPiSetup,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='env_config'
    )
    simulation_mode = models.BooleanField(default=False)
    reading_interval = models.IntegerField(default=30)  # seconds
    inter_device_delay = models.FloatField(default=0.1)  # seconds
    port = models.CharField(max_length=100, default="/dev/ttyUSB0")
    enable_mqtt = models.BooleanField(default=False)
    enable_rtc = models.BooleanField(default=True)
    log_level = models.CharField(
        max_length=10,
        default="INFO",
        choices=[
            ('DEBUG', 'Debug'),
            ('INFO', 'Info'),
            ('WARNING', 'Warning'),
            ('ERROR', 'Error'),
            ('CRITICAL', 'Critical'),
        ]
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'env_config'
        verbose_name = 'Environment Config'
        verbose_name_plural = 'Environment Configs'

    def __str__(self):
        return f"Config for {self.pi_setup.pi_name}"


class MeterReading(models.Model):
    # Foreign key relationships to DCMS_PI_SETUP
    pi_setup = models.ForeignKey(
        DcmsPiSetup,
        on_delete=models.CASCADE,
        related_name='meter_readings'
    )

    # Original fields
    device_id = models.CharField(max_length=100)
    meter_name = models.CharField(max_length=100)
    time = models.DateTimeField()
    model = models.CharField(max_length=100)
    watts_total = models.FloatField()

    # Power measurements
    watts_r_ph = models.FloatField(null=True, blank=True)
    watts_y_ph = models.FloatField(null=True, blank=True)
    watts_b_ph = models.FloatField(null=True, blank=True)

    # Power factor
    pf_ave = models.FloatField(null=True, blank=True)
    pf_r_ph = models.FloatField(null=True, blank=True)
    pf_y_ph = models.FloatField(null=True, blank=True)
    pf_b_ph = models.FloatField(null=True, blank=True)

    # Voltage measurements
    vln_average = models.FloatField(null=True, blank=True)
    v_r_ph = models.FloatField(null=True, blank=True)
    v_y_ph = models.FloatField(null=True, blank=True)
    v_b_ph = models.FloatField(null=True, blank=True)

    # Current measurements
    a_average = models.FloatField(null=True, blank=True)
    a_r_ph = models.FloatField(null=True, blank=True)
    a_y_ph = models.FloatField(null=True, blank=True)
    a_b_ph = models.FloatField(null=True, blank=True)

    # Other measurements
    frequency = models.FloatField(null=True, blank=True)
    wh_received = models.FloatField(null=True, blank=True)
    load_hours_delivered = models.FloatField(null=True, blank=True)
    no_of_interruption = models.IntegerField(null=True, blank=True)
    on_hours = models.CharField(max_length=20, null=True, blank=True)

    # Harmonics
    v_r_harmonics = models.FloatField(null=True, blank=True)
    v_y_harmonics = models.FloatField(null=True, blank=True)
    v_b_harmonics = models.FloatField(null=True, blank=True)
    a_r_harmonics = models.FloatField(null=True, blank=True)
    a_y_harmonics = models.FloatField(null=True, blank=True)
    a_b_harmonics = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'meters_meterreading'
        indexes = [
            models.Index(fields=['pi_setup', 'time']),
            models.Index(fields=['device_id', 'time']),
            models.Index(fields=['time']),
            models.Index(fields=['meter_name']),
        ]

    def __str__(self):
        return f"{self.meter_name} - {self.pi_setup.pi_name} - {self.time}"

    # Properties to access related data easily
    @property
    def pi_name(self):
        return self.pi_setup.pi_name

    @property
    def pi_ip(self):
        return self.pi_setup.pi_ip

    @property
    def location(self):
        return self.pi_setup.location

    @property
    def config_path(self):
        return self.pi_setup.config_path


class DeviceConfig(models.Model):
    device_id = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=100)
    meter_name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField(default=502)

    # Configuration parameters
    reading_interval = models.IntegerField(default=60)  # seconds
    server_url = models.URLField()
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.device_id} - {self.location}"


class ConfigParameter(models.Model):
    device = models.ForeignKey(
        DeviceConfig, on_delete=models.CASCADE, related_name='parameters')
    key = models.CharField(max_length=100)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('device', 'key')

    def __str__(self):
        return f"{self.device.device_id} - {self.key}"


class Device(models.Model):
    pi_name = models.CharField(max_length=100)
    pi_ip = models.GenericIPAddressField(unique=True)
    location = models.CharField(max_length=100)


class Meter(models.Model):
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name='meters')
    meter_name = models.CharField(max_length=100)
    meter_address = models.IntegerField()
    meter_model = models.CharField(max_length=100)


class Config(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)
    SIMULATION_MODE = models.BooleanField(default=False)
    READING_INTERVAL = models.IntegerField(default=30)
    INTER_DEVICE_DELAY = models.FloatField(default=0.1)
    PORT = models.CharField(max_length=100, default="/dev/ttyUSB0")
    ENABLE_MQTT = models.BooleanField(default=False)
    ENABLE_RTC = models.BooleanField(default=True)
    LOG_LEVEL = models.CharField(max_length=10, default="INFO")
