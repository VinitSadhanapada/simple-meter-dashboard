default_app_config = 'device_config.apps.DeviceManagerConfig'

# Ensure signals are always imported
try:
	import meter_dashboard.device_config.signals
except ImportError:
	pass
