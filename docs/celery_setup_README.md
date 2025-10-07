# Celery Setup and Usage for meter_dashboard

## Installation

1. Install Python packages:

```bash
pip install celery redis
```

2. Install system package for Redis:

```bash
sudo apt-get install redis-server
```

3. (Optional) Download packages for offline use:

```bash
pip download celery redis -d /home/isha/deepak/MFM_offline_setup/packages_folder
apt-get download redis-server -o Dir::Cache::archives=/home/isha/deepak/MFM_offline_setup/packages_folder
```

## Django settings.py Configuration

Add the following to your `settings.py`:

```python
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
```

## Project Structure

- `meter_dashboard/meter_dashboard/celery.py`: Celery app configuration
- `meter_dashboard/meter_dashboard/__init__.py`: Import Celery app
- `device_config/tasks.py`: Celery tasks (e.g., OTA deployment)

## Celery App Setup

Create `meter_dashboard/meter_dashboard/celery.py`:

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meter_dashboard.settings')

app = Celery('meter_dashboard')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

Update `meter_dashboard/meter_dashboard/__init__.py`:

```python
from .celery import app as celery_app
__all__ = ['celery_app']
```

## Running Redis

Start Redis server:

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## Running Celery Worker

From your project root (where manage.py is):

```bash
celery -A meter_dashboard worker --loglevel=info
```

## Usage

- Trigger background tasks (e.g., OTA deployment) from Django admin.
- Celery worker will process tasks in the background.
- Status updates are reflected in the Django admin interface.

## Troubleshooting

- If you see connection errors, ensure Redis is running and `CELERY_BROKER_URL` is set correctly.
- Check Celery worker logs for errors.
- For production, use systemd or supervisor to keep Celery running.

## Additional Notes

- Celery tasks can be configured with timeouts (see `device_config/tasks.py`).
- All required packages can be kept in `/home/isha/deepak/MFM_offline_setup/packages_folder` for offline installation.
