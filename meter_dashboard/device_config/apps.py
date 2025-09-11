from django.apps import AppConfig



class DeviceManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'device_config'

    def ready(self):
        # Import signals to ensure they are registered
        from . import signals
