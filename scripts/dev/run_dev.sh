#!/usr/bin/env bash
set -euo pipefail

# Simple dev launcher for Raspberry Pi
# Starts: Redis (system), Django server, Celery worker, and MQTT ingest
# Requires: tmux

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV_DIR="$REPO_ROOT/venv"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux not found. Install it: sudo apt-get update && sudo apt-get install -y tmux" >&2
  exit 1
fi

SESSION_NAME="smd-dev"

# Create session if not exists
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  tmux new-session -d -s "$SESSION_NAME" -n server
fi

# Pane 0: Redis status + logs
# (Redis is started by systemd; we just show status once.)
tmux send-keys -t "$SESSION_NAME":server.0 "sudo systemctl status --no-pager redis-server || true" C-m

# Create window for Django
if ! tmux list-windows -t "$SESSION_NAME" | grep -q django; then
  tmux new-window -t "$SESSION_NAME" -n django
fi
# Start Django dev server
DJANGO_CMD="cd '$REPO_ROOT/meter_dashboard' && source '$VENV_DIR/bin/activate' && python manage.py runserver 0.0.0.0:8000"
tmux send-keys -t "$SESSION_NAME":django.0 "$DJANGO_CMD" C-m

# Create window for Celery worker
if ! tmux list-windows -t "$SESSION_NAME" | grep -q celery; then
  tmux new-window -t "$SESSION_NAME" -n celery
fi
CELERY_CMD="cd '$REPO_ROOT' && source '$VENV_DIR/bin/activate' && export ALERT_PERSISTENCE_SECONDS=10 && celery -A meter_dashboard worker -l info"
tmux send-keys -t "$SESSION_NAME":celery.0 "$CELERY_CMD" C-m

# Create window for Ingest
if ! tmux list-windows -t "$SESSION_NAME" | grep -q ingest; then
  tmux new-window -t "$SESSION_NAME" -n ingest
fi
INGEST_CMD="cd '$REPO_ROOT/iot_scripts' && source '$VENV_DIR/bin/activate' && python3 mqtt_to_db_ingest.py"
tmux send-keys -t "$SESSION_NAME":ingest.0 "$INGEST_CMD" C-m

# Select the django window by default
tmux select-window -t "$SESSION_NAME":django

echo "Started tmux session: $SESSION_NAME"
echo "Attach with: tmux attach -t $SESSION_NAME"
