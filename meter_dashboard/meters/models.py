from django.db import models


class MeterReading(models.Model):
    location = models.CharField(max_length=100)
    device_id = models.CharField(max_length=100)
    meter_name = models.CharField(max_length=100)
    time = models.DateTimeField()
    model = models.CharField(max_length=100)
    watts_total = models.FloatField()
    # Add other fields as needed
    watts_r_ph = models.FloatField(null=True, blank=True)
    watts_y_ph = models.FloatField(null=True, blank=True)
    watts_b_ph = models.FloatField(null=True, blank=True)
    pf_ave = models.FloatField(null=True, blank=True)
    pf_r_ph = models.FloatField(null=True, blank=True)
    pf_y_ph = models.FloatField(null=True, blank=True)
    pf_b_ph = models.FloatField(null=True, blank=True)
    vln_average = models.FloatField(null=True, blank=True)
    v_r_ph = models.FloatField(null=True, blank=True)
    v_y_ph = models.FloatField(null=True, blank=True)
    v_b_ph = models.FloatField(null=True, blank=True)
    a_average = models.FloatField(null=True, blank=True)
    a_r_ph = models.FloatField(null=True, blank=True)
    a_y_ph = models.FloatField(null=True, blank=True)
    a_b_ph = models.FloatField(null=True, blank=True)
    frequency = models.FloatField(null=True, blank=True)
    wh_received = models.FloatField(null=True, blank=True)
    load_hours_delivered = models.FloatField(null=True, blank=True)
    no_of_interruption = models.IntegerField(null=True, blank=True)
    on_hours = models.CharField(max_length=20, null=True, blank=True)
    v_r_harmonics = models.FloatField(null=True, blank=True)
    v_y_harmonics = models.FloatField(null=True, blank=True)
    v_b_harmonics = models.FloatField(null=True, blank=True)
    a_r_harmonics = models.FloatField(null=True, blank=True)
    a_y_harmonics = models.FloatField(null=True, blank=True)
    a_b_harmonics = models.FloatField(null=True, blank=True)


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
