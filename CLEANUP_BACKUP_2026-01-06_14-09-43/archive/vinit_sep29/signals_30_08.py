import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models_30_08 import Meter_30_08

DEVICE_CONFIG_PATH = '/home/pi/meter_config/device_config.json'

def export_device_config_flat():
    meters = Meter_30_08.objects.select_related('rpi').all()
    data = []
    for m in meters:
        data.append({
            "meter_name": m.meter_name,
            "meter_address": m.meter_address,
            "meter_model": m.meter_model,
            "location": m.location,
            "pi_ip": str(m.rpi.pi_ip),
            "pi_name": m.rpi.pi_name
        })
    with open(DEVICE_CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)

@receiver(post_save, sender=Meter_30_08)
def meter_saved_handler(sender, instance, **kwargs):
    print("[DEBUG] meter_saved_handler triggered for:", instance)
    export_device_config_flat()
    print("[DEBUG] device_config.json export complete (save)")

@receiver(post_delete, sender=Meter_30_08)
def meter_deleted_handler(sender, instance, **kwargs):
    print("[DEBUG] meter_deleted_handler triggered for:", instance)
    export_device_config_flat()
    print("[DEBUG] device_config.json export complete (delete)")
