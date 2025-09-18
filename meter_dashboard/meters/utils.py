import requests
import json
from .models import Config, Meter


def push_config_to_pi(device):
    config = Config.objects.get(device=device)
    meters = Meter.objects.filter(device=device)

    device_config = [
        {
            "meter_name": m.meter_name,
            "meter_address": m.meter_address,
            "meter_model": m.meter_model,
            "location": device.location,
            "pi_ip": device.pi_ip,
            "pi_name": device.pi_name
        } for m in meters
    ]

    config_json = {
        "SIMULATION_MODE": config.SIMULATION_MODE,
        "READING_INTERVAL": config.READING_INTERVAL,
        "INTER_DEVICE_DELAY": config.INTER_DEVICE_DELAY,
        "PORT": config.PORT,
        "ENABLE_MQTT": config.ENABLE_MQTT,
        "ENABLE_RTC": config.ENABLE_RTC,
        "LOG_LEVEL": config.LOG_LEVEL
    }

    payload = {
        "device_config": device_config,
        "config": config_json
    }

    url = f"http://{device.pi_ip}:8080/update-config"
    response = requests.post(url, json=payload)
    return response.status_code
