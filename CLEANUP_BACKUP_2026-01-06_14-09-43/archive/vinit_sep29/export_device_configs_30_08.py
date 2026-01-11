import json
from .models_30_08 import RPI_30_08

def export_device_configs_json(filepath):
    data = []
    for rpi in RPI_30_08.objects.prefetch_related('meters').all():
        rpi_dict = {
            "pi_name": rpi.pi_name,
            "pi_ip": "10.108.215.59",
            "location": rpi.location,
            "ssh_username": rpi.ssh_username,
            "ssh_password": rpi.ssh_password,
            "ssh_key_path": rpi.ssh_key_path,
            "config_path": rpi.config_path,
            "description": rpi.description,
            "contact_person": rpi.contact_person,
            "is_active": rpi.is_active,
            "meters": [
                {
                    "meter_name": m.meter_name,
                    "meter_address": m.meter_address,
                    "meter_model": m.meter_model,
                    "location": m.location
                } for m in rpi.meters.all()
            ]
        }
        data.append(rpi_dict)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
