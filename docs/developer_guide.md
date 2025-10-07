# Meter Dashboard Developer Guide

## Setup
1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install system packages:
   ```bash
   sudo apt-get install sshpass redis-server
   ```
4. Configure `settings.py` (database, CELERY_BROKER_URL, etc.).
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Start Redis and Celery worker:
   ```bash
   sudo systemctl start redis-server
   celery -A meter_dashboard worker --loglevel=info
   ```
7. Start Django server:
   ```bash
   python manage.py runserver
   ```

## Key Files
- `device_config/models.py`: ORM models.
- `device_config/tasks.py`: Celery background tasks.
- `device_config/admin.py`: Django admin actions.
- `meter_dashboard/celery.py`: Celery app config.

## Extending
- Add new models in `device_config/models.py`.
- Add new admin actions in `device_config/admin.py`.
- Add new background tasks in `device_config/tasks.py`.

## Best Practices
- Use Django ORM for all DB operations.
- Use Celery for long-running/background tasks.
- Keep documentation up to date in `/docs`.

---
