from django.core.management.base import BaseCommand
from device_config.signals import export_device_config_flat, DEVICE_CONFIG_PATH
import os

class Command(BaseCommand):
    help = "Export meter device configuration JSON to the configured path and report status"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(f"Exporting meter device config to: {DEVICE_CONFIG_PATH}"))
        export_device_config_flat()
        exists = os.path.exists(DEVICE_CONFIG_PATH)
        size = os.path.getsize(DEVICE_CONFIG_PATH) if exists else 0
        if exists:
            self.stdout.write(self.style.SUCCESS(f"Export successful. File exists (size={size} bytes)."))
        else:
            self.stdout.write(self.style.ERROR("Export function ran but file does not exist. Check logs for errors."))
