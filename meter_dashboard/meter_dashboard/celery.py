import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')

app = Celery('meter_dashboard')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Explicitly import tasks from non-app modules so the worker registers them
try:
	# Ensure the repository root is on sys.path so 'iot_scripts' is importable
	import sys as _sys, os as _os
	_repo_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
	if _repo_root not in _sys.path:
		_sys.path.append(_repo_root)
	import iot_scripts.alerting.celery_alert_tasks  # noqa: F401
except Exception as e:
	# If this import fails, the /api/alerts feed may still work if tasks are otherwise imported
	print(f"[Celery init] Warning: could not import iot_scripts alert tasks: {e}")
