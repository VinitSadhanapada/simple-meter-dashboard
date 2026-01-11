from django.db import models

class RPI_30_08(models.Model):
    pi_name = models.CharField(max_length=100)
    pi_ip = models.GenericIPAddressField()
    location = models.CharField(max_length=200)
    ssh_username = models.CharField(max_length=100)
    ssh_password = models.CharField(max_length=100)
    ssh_key_path = models.CharField(max_length=200, blank=True)
    config_path = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.pi_name

class Meter_30_08(models.Model):
    rpi = models.ForeignKey(RPI_30_08, related_name='meters', on_delete=models.CASCADE)
    meter_name = models.CharField(max_length=100)
    meter_address = models.IntegerField()
    meter_model = models.CharField(max_length=100)
    location = models.CharField(max_length=200)

    def __str__(self):
        return self.meter_name
