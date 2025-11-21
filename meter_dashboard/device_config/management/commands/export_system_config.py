from django.core.management.base import BaseCommand
from device_config.signals import export_system_config, SYSTEM_CONFIG_PATH
import os

class Command(BaseCommand):
    help = "Export system (polling) configuration JSON for all Raspberry Pis"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(f"Exporting system configs to: {SYSTEM_CONFIG_PATH}"))
        export_system_config()
        exists = os.path.exists(SYSTEM_CONFIG_PATH)
        size = os.path.getsize(SYSTEM_CONFIG_PATH) if exists else 0
        if exists:
            self.stdout.write(self.style.SUCCESS(f"System config export successful (size={size} bytes)."))
        else:
            self.stdout.write(self.style.ERROR("Export function ran but file does not exist. Check logs for errors."))
