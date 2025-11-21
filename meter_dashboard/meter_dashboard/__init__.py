try:
    from .celery import app as celery_app
    # Provide a conventional name so `celery -A meter_dashboard worker` can find it
    celery = celery_app  # alias for Celery CLI autodiscovery
    __all__ = ['celery_app', 'celery']
except Exception:
    # Celery not critical for base dashboard operation; silently ignore
    __all__ = []

# Ensure device config signals are registered
try:
    import meter_dashboard.signals_30_08  # noqa: F401
except ImportError:
    pass
