from .celery import app as celery_app

__all__ = ['celery_app']

# Ensure device config signals are registered
try:
    import meter_dashboard.signals_30_08
except ImportError:
    pass
