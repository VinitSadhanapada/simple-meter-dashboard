# USB Deployment Guide

This guide explains how to take the copied `simple-meter-dashboard` folder from a USB drive and run it on a new Ubuntu machine.

## 1. Prerequisites

Ubuntu 22.04+ recommended. Ensure you have sudo access.

## 2. Copy Project From USB

```bash
sudo mkdir -p /opt/simple-meter-dashboard
sudo cp -r /media/$USER/USB_DRIVE_NAME/simple-meter-dashboard/* /opt/simple-meter-dashboard/
sudo chown -R $USER:$USER /opt/simple-meter-dashboard
cd /opt/simple-meter-dashboard
```

Adjust `USB_DRIVE_NAME` to match your mounted USB volume (check with `ls /media/$USER/`).

## 3. Install Docker (Engine + Compose)

Run the helper script included:

```bash
sudo bash scripts/install_docker.sh
```

Log out and back in (or reboot) to ensure your user can run Docker without sudo (optional). You can proceed with sudo if preferred.

## 4. Environment File

Create a `.env` file (copy from `.env.example` if present). Ensure you set a valid Fernet key:

```bash
cp .env.example .env
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # generate key
```

Then edit `.env` and set:

```
FIELD_ENCRYPTION_KEY=<generated-key>
```

Leave other defaults (DB vars) unless you need custom values.

## 5. Start the Stack

```bash
docker compose up -d --build
```

Services:
- App → port 18000 mapped to container port 8000
- Postgres → internal only (not exposed to host)
- Redis → internal only

## 6. Verify

```bash
curl -I http://localhost:18000/
curl -I http://localhost:18000/api/
curl -s http://localhost:18000/meter_readings/api/meter/
```

Expect 200 responses; if the `meter_readings` raw table is not present yet you will get empty data arrays (safe fallback).

## 7. (Optional) Restore Database Dump

If you copied the PostgreSQL dump file (`postgresql_schema_dump/mfmdb.dump`), you can restore initial data:

```bash
docker compose cp postgresql_schema_dump/mfmdb.dump db:/tmp/mfmdb.dump
docker compose exec db bash -lc "pg_restore -U $DB_USER -d $DB_NAME /tmp/mfmdb.dump"
```

You can then check tables:

```bash
docker compose exec db psql -U $DB_USER -d $DB_NAME -c '\dt'
```

## 8. Regenerating Static Files (if needed)

Static assets are collected during build; to re-collect manually:

```bash
docker compose exec app python meter_dashboard/manage.py collectstatic --noinput
```

## 9. Changing Host IP / Accessing Remotely

No IP configuration changes are required. The container runs `runserver 0.0.0.0:8000` and the compose file maps host port `18000`. Access from another machine on the LAN using:

```
http://<ubuntu_host_ip>:18000/
```

If you need a different external port, edit `docker-compose.yml`:

```yaml
    ports:
      - "8080:8000"  # example
```

## 10. Production Hardening (Next Step)

For a more production-like setup consider:
- Gunicorn instead of Django dev server
- Caddy or Nginx reverse proxy for TLS
- Volume for persistent media/static if needed

## 11. Stopping / Updating

```bash
docker compose pull   # if using images from registry
docker compose up -d --build  # rebuild after code changes
docker compose logs -f app
docker compose down   # stop all services
```

## 12. Troubleshooting

| Symptom | Fix |
|---------|-----|
| 500 on alerts endpoints | Ensure Redis container running; endpoints fall back gracefully in current build. |
| Fernet key error | Regenerate key and update `.env`. Restart app. |
| Permission denied on docker | Log out/in after install or use `sudo`. |
| Empty meter readings | Ingest data or restore dump; fallback is expected. |

---
Deployment via USB complete. Reach out for Gunicorn/HTTPS config when ready.
