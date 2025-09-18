# Ensure device config signals are registered
try:
	import meter_dashboard.signals_30_08
except ImportError:
	pass
