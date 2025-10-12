# Meter Dashboard Server Setup Manual

---
## 1. System Preparation
- Use Ubuntu or Debian-based server (recommended).
- Update system:
  ```bash
  sudo apt-get update && sudo apt-get upgrade
  ```

---
## 2. Python & Django Setup
- Install Python 3 and pip:
  ```bash
  sudo apt-get install python3 python3-pip
  ```
- Clone the meter_dashboard repository to `/home/isha/deepak/MFM_offline_setup/`.
- Install Python dependencies:
  ```bash
  pip install -r requirements.txt
  ```

---
## 3. PostgreSQL Database Setup
- Install PostgreSQL:
  ```bash
  sudo apt-get install postgresql postgresql-contrib
  ```
- Create database and user:
  ```bash
  sudo -u postgres psql
  CREATE DATABASE mfmdb;
  CREATE USER mfmuser WITH PASSWORD 'devi';
  GRANT ALL PRIVILEGES ON DATABASE mfmdb TO mfmuser;
  \q
  ```
- Update `settings.py` with DB credentials and bind address (use Pi/server IP or `0.0.0.0` for all interfaces).

---
## 4. MQTT Broker Setup
- Install Mosquitto MQTT broker:
  ```bash
  sudo apt-get install mosquitto mosquitto-clients
  ```
- Configure Mosquitto to listen on all interfaces:
  Edit `/etc/mosquitto/mosquitto.conf`:
  ```
  listener 1883 0.0.0.0
  allow_anonymous true
  ```
- Restart Mosquitto:
  ```bash
  sudo systemctl restart mosquitto
  sudo systemctl enable mosquitto
  ```

---
## 5. Redis & Celery Setup
- Install Redis server:
  ```bash
  sudo apt-get install redis-server
  sudo systemctl start redis-server
  sudo systemctl enable redis-server
  ```
- Install Celery:
  ```bash
  pip install celery redis
  ```
- Configure `settings.py`:
  ```python
  CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
  ```
- Create `celery.py` and update `__init__.py` in main Django project folder.
- Start Celery worker:
  ```bash
  celery -A meter_dashboard worker --loglevel=info
  ```
- (Optional) Use systemd or supervisor to keep Celery running.

---
## 6. Django Project Setup
- Run migrations:
  ```bash
  python manage.py migrate
  ```
- Create superuser:
  ```bash
  python manage.py createsuperuser
  ```
- Start Django server:
  ```bash
  python manage.py runserver 0.0.0.0:8000
  ```
- Access admin at `http://<server_ip>:8000/admin/`

---
## 7. SSH & Rsync Utilities
- Install sshpass and rsync:
  ```bash
  sudo apt-get install sshpass rsync
  ```

---
## 8. Environment & Security
- Store sensitive keys and passwords in `.env` file.
- Set proper permissions for config and data folders.
- Restrict access to admin and database in production.

---
## 9. Replicating Server Setup
- Copy project folder and `/docs` to new server.
- Repeat steps above for Python, DB, MQTT, Redis, Celery, and Django setup.
- Restore database from backup if needed:
  ```bash
  pg_dump mfmdb > backup.sql
  psql mfmdb < backup.sql
  ```
- Update IP addresses and credentials in config files.

---
## 10. Quick Reference
- Django admin: `http://<server_ip>:8000/admin/`
- Celery worker: `celery -A meter_dashboard worker --loglevel=info`
- Redis server: `sudo systemctl start redis-server`
- MQTT broker: `sudo systemctl start mosquitto`
- PostgreSQL: `sudo systemctl start postgresql`

---
## 11. Troubleshooting
- Check logs for Django, Celery, Redis, Mosquitto, and PostgreSQL.
- Ensure all services are running and listening on correct addresses.
- Use `systemctl status <service>` to check service health.

---
