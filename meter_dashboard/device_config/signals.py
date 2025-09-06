import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import MeterDevice, RaspberryPi

DEVICE_CONFIG_PATH = '/home/pi/meter_config/device_config.json'

def export_device_config_flat():
    meters = MeterDevice.objects.select_related('raspberry_pi').all()
    data = []
    for m in meters:
        data.append({
            "meter_name": m.meter_name,
            "meter_address": m.meter_address,
            "meter_model": m.meter_model,
            "location": m.raspberry_pi.location,
            "pi_ip": str(m.raspberry_pi.pi_ip),
            "pi_name": m.raspberry_pi.pi_name
        })
    with open(DEVICE_CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)

@receiver(post_save, sender=MeterDevice)
def meterdevice_saved_handler(sender, instance, **kwargs):
    print("[DEBUG] meterdevice_saved_handler triggered for:", instance)
    export_device_config_flat()
    print("[DEBUG] device_config.json export complete (save)")

@receiver(post_delete, sender=MeterDevice)
def meterdevice_deleted_handler(sender, instance, **kwargs):
    print("[DEBUG] meterdevice_deleted_handler triggered for:", instance)
    export_device_config_flat()
    print("[DEBUG] device_config.json export complete (delete)")
