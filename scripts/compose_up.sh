#!/usr/bin/env bash
set -euo pipefail

# Build and start the stack, then run migrations and collectstatic

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

echo "Starting containers (build if needed)..."
docker compose up -d --build

echo "Waiting for app to be ready..."
sleep 5

echo "Applying migrations..."
docker compose exec -T app python meter_dashboard/manage.py migrate --noinput

echo "Collecting static files..."
docker compose exec -T app python meter_dashboard/manage.py collectstatic --noinput

echo "App should be available at http://localhost:18000/"
