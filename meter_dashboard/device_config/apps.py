from django.apps import AppConfig


<<<<<<< HEAD

class DeviceManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'device_config'

    def ready(self):
        # Import signals to ensure they are registered
        from . import signals
=======
class DeviceManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'device_config'
>>>>>>> clubbed_mfm_dcms_16-aug
