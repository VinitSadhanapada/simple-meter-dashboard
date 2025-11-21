import json
import os
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import MeterDevice, RaspberryPi, SystemConfiguration

logger = logging.getLogger(__name__)

# Default export path (can be overridden via Django settings or env)
DEFAULT_DEVICE_CONFIG_DIR = getattr(settings, 'DEVICE_CONFIG_EXPORT_DIR', '/app/meter_config')
DEVICE_CONFIG_PATH = os.environ.get('DEVICE_CONFIG_PATH', os.path.join(DEFAULT_DEVICE_CONFIG_DIR, 'device_config.json'))

def _ensure_parent_dir(path: str):
    parent = os.path.dirname(path)
    try:
        os.makedirs(parent, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed creating directory '{parent}': {e}")
        raise

def export_device_config_flat():
    """Export meter devices in a flat JSON structure.
    Ensures target directory exists; logs errors instead of crashing admin save.
    """
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

    try:
        _ensure_parent_dir(DEVICE_CONFIG_PATH)
        with open(DEVICE_CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Exported {len(data)} meter device configs to {DEVICE_CONFIG_PATH}")
        if settings.DEBUG:
            print(f"[device_config] Exported {len(data)} meter device configs to {DEVICE_CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Failed to export device config JSON to primary path {DEVICE_CONFIG_PATH}: {e}")
        # Fallback to configured export directory if different
        fallback_dir = getattr(settings, 'DEVICE_CONFIG_EXPORT_DIR', '/app/meter_config')
        fallback_path = os.path.join(fallback_dir, 'device_config.json')
        if fallback_path != DEVICE_CONFIG_PATH:
            try:
                _ensure_parent_dir(fallback_path)
                with open(fallback_path, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Fallback export succeeded to {fallback_path}")
                if settings.DEBUG:
                    print(f"[device_config] Fallback export succeeded to {fallback_path}")
            except Exception as e2:
                logger.error(f"Fallback export also failed to {fallback_path}: {e2}")
                if settings.DEBUG:
                    print(f"[device_config] Fallback export failed: {e2}")
        else:
            if settings.DEBUG:
                print(f"[device_config] Failed export, no fallback path difference: {e}")


# System configuration export (polling/runtime settings per Pi)
SYSTEM_CONFIG_PATH = os.environ.get('SYSTEM_CONFIG_PATH', os.path.join(DEFAULT_DEVICE_CONFIG_DIR, 'system_config.json'))

def export_system_config():
    """Export all SystemConfiguration rows to a JSON list for RPI polling scripts.
    Each entry includes pi metadata plus the config JSON produced by to_json().
    """
    configs = SystemConfiguration.objects.select_related('raspberry_pi').all()
    payload = []
    for cfg in configs:
        payload.append({
            "pi_name": cfg.raspberry_pi.pi_name,
            "pi_ip": str(cfg.raspberry_pi.pi_ip),
            "config": cfg.to_json()
        })
    try:
        _ensure_parent_dir(SYSTEM_CONFIG_PATH)
        with open(SYSTEM_CONFIG_PATH, 'w') as f:
            json.dump(payload, f, indent=2)
        logger.info(f"Exported {len(payload)} system configs to {SYSTEM_CONFIG_PATH}")
        if settings.DEBUG:
            print(f"[device_config] Exported {len(payload)} system configs to {SYSTEM_CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Failed exporting system config JSON: {e}")
        if settings.DEBUG:
            print(f"[device_config] System config export failed: {e}")


@receiver(post_save, sender=SystemConfiguration)
def systemconfiguration_saved_handler(sender, instance, **kwargs):
    logger.debug(f"systemconfiguration_saved_handler triggered for: {instance}")
    export_system_config()
    logger.debug("system_config.json export complete (save)")


@receiver(post_save, sender=MeterDevice)
def meterdevice_saved_handler(sender, instance, **kwargs):
    logger.debug(f"meterdevice_saved_handler triggered for: {instance}")
    export_device_config_flat()
    logger.debug("device_config.json export complete (save)")

@receiver(post_delete, sender=MeterDevice)
def meterdevice_deleted_handler(sender, instance, **kwargs):
    logger.debug(f"meterdevice_deleted_handler triggered for: {instance}")
    export_device_config_flat()
    logger.debug("device_config.json export complete (delete)")
