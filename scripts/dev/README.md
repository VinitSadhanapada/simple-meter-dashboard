# One-command dev launcher

This starts the full stack in a tmux session: Django server, Celery worker, and MQTT ingest (Redis via systemd).

## Requirements

- tmux installed
- Redis server running via systemd
- Repo virtualenv at `venv/`

## Usage

```bash
cd /home/pi/Desktop/simple-meter-dashboard
chmod +x scripts/dev/run_dev.sh
./scripts/dev/run_dev.sh
# Then attach to the tmux session:
tmux attach -t smd-dev
```

Windows in the session:
- server: shows Redis status
- django: runs `python manage.py runserver 0.0.0.0:8000`
- celery: runs the Celery worker
- ingest: runs the MQTT ingestion script

To detach from tmux: Ctrl+b, then d.
To kill the session when done:

```bash
tmux kill-session -t smd-dev
```

## Tweaks
- Edit `scripts/dev/run_dev.sh` to change ALERT_PERSISTENCE_SECONDS or bind host/port.
- If you want auto-restart on crash, consider using `honcho`/`foreman` or systemd service units.
