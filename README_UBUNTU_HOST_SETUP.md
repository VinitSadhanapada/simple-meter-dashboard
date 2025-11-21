# Ubuntu Host Setup: MQTT to PostgreSQL Ingestion

This guide sets up and runs the ingestion script on an Ubuntu machine using the host's Mosquitto broker and PostgreSQL 14. No Redis/Celery required.

Scope
- MQTT broker: host Mosquitto on port 1883
- Database: host PostgreSQL 14 on port 5432
- Ingestion: runs locally in a Python virtualenv

Optional: restore DB schema/data from `postgresql_schema_dump/mfmdb.dump`.

## TL;DR

```bash
# Prereqs (if needed)
sudo apt update
sudo apt install -y postgresql-14 postgresql-client-14 postgresql-contrib python3-venv python3-pip mosquitto-clients

# DB init (run as sudoer)
sudo -u postgres psql -c "CREATE DATABASE mfmdb;"
sudo -u postgres psql -c "CREATE USER mfmuser WITH ENCRYPTED PASSWORD 'devi';"
sudo -u postgres psql -d mfmdb -c "GRANT ALL PRIVILEGES ON DATABASE mfmdb TO mfmuser;"

# (Optional) Restore schema
cd ~/simple-meter-dashboard
sudo -u postgres pg_restore -d mfmdb postgresql_schema_dump/mfmdb.dump

# Python env + deps
cd ~/simple-meter-dashboard
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run ingestion (no Redis/Celery)
export DISABLE_ALERT_DISPATCH=1
export METER_CONFIG_DIR="$PWD/iot_scripts"
export DB_HOST=localhost
export DB_PORT=5432
python iot_scripts/mqtt_to_db_ingest.py
```

From another terminal:

```bash
cd ~/simple-meter-dashboard
. .venv/bin/activate
python iot_scripts/tests/publish_sample.py
```

Verify:

```bash
# Python helper
python iot_scripts/tests/verify_db.py

# Or psql directly
psql "postgresql://mfmuser:devi@localhost:5432/mfmdb" \
  -c "SELECT id, device_id, meter_name, to_char(time,'YYYY-MM-DD HH24:MI:SS'), watts_total FROM meter_readings ORDER BY id DESC LIMIT 5;"
```

---

## 1) Prerequisites

```bash
sudo apt update
sudo apt install -y postgresql-14 postgresql-client-14 postgresql-contrib \
                    python3-venv python3-pip
# Optional but handy
sudo apt install -y mosquitto-clients git
```

- Mosquitto broker: assumed already installed and running on this host (port 1883).
- PostgreSQL 14: service should be running on port 5432.

Check:
```bash
systemctl status postgresql --no-pager
# Optional: test broker
mosquitto_sub -t 'meter/readings' -v -C 1 & sleep 1; mosquitto_pub -t 'meter/readings' -m 'hello'; wait
```

## 2) PostgreSQL setup

Defaults expected by scripts:
- DB: `mfmdb`
- User: `mfmuser`
- Password: `devi`

Create DB and user:
```bash
sudo -u postgres psql -c "CREATE DATABASE mfmdb;"
sudo -u postgres psql -c "CREATE USER mfmuser WITH ENCRYPTED PASSWORD 'devi';"
sudo -u postgres psql -d mfmdb -c "GRANT ALL PRIVILEGES ON DATABASE mfmdb TO mfmuser;"
# Optional: ensure schema ownership
sudo -u postgres psql -d mfmdb -c "ALTER SCHEMA public OWNER TO mfmuser;"
```

If local TCP auth fails, confirm `/etc/postgresql/14/main/pg_hba.conf` has:
```
host    all             all             127.0.0.1/32            md5
```
Then reload Postgres:
```bash
sudo systemctl reload postgresql
```

## 3) Restore schema/data (optional)

If the database is empty, restore from dump:
```bash
cd ~/simple-meter-dashboard
sudo -u postgres pg_restore -d mfmdb postgresql_schema_dump/mfmdb.dump
```
If you get duplicate/exists errors, you may add `--clean` to drop before restore:
```bash
sudo -u postgres pg_restore --clean -d mfmdb postgresql_schema_dump/mfmdb.dump
```

Quick check:
```bash
psql "postgresql://mfmuser:devi@localhost:5432/mfmdb" -c "\dt"
```

## 4) Get the code on Ubuntu

```bash
cd ~
# Clone (or copy your project folder here)
git clone https://github.com/VinitSadhanapada/simple-meter-dashboard.git
cd simple-meter-dashboard
# Optional: checkout a branch
# git checkout 10SepMerge
```

## 5) Create Python venv and install dependencies

```bash
cd ~/simple-meter-dashboard
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 6) Run the ingestion script (host Mosquitto + host PostgreSQL)

Use the repo’s config at `iot_scripts/config.json` and disable alerts to avoid Redis/Celery.

```bash
cd ~/simple-meter-dashboard
. .venv/bin/activate

export DISABLE_ALERT_DISPATCH=1
export METER_CONFIG_DIR="$PWD/iot_scripts"
export DB_HOST=localhost
export DB_PORT=5432

python iot_scripts/mqtt_to_db_ingest.py
```

Expected output includes:
- `[DEBUG] Loaded config: .../iot_scripts/config.json`
- `Listening for meter readings...`
- `[DEBUG] MQTT on_connect rc=0`
- `[DEBUG] Subscribed to meter/readings`

## 7) Publish a test payload

In a second terminal:
```bash
cd ~/simple-meter-dashboard
. .venv/bin/activate
python iot_scripts/tests/publish_sample.py
```
This publishes a retained test message to `meter/readings` on port 1883.

## 8) Verify in PostgreSQL

Using the helper script:
```bash
cd ~/simple-meter-dashboard
. .venv/bin/activate
python iot_scripts/tests/verify_db.py
```
Or directly via psql:
```bash
psql "postgresql://mfmuser:devi@localhost:5432/mfmdb" \
  -c "SELECT id, device_id, meter_name, to_char(time,'YYYY-MM-DD HH24:MI:SS'), watts_total FROM meter_readings ORDER BY id DESC LIMIT 5;"
```
You should see the `Test-Meter` row from the publisher.

## 9) Optional: run ingestion as a systemd service

Keep the ingestion running on boot.

```bash
# Place code under /opt for a stable path
sudo mkdir -p /opt/simple-meter-dashboard
sudo rsync -a ~/simple-meter-dashboard/ /opt/simple-meter-dashboard/
sudo chown -R $USER:$USER /opt/simple-meter-dashboard

cd /opt/simple-meter-dashboard
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create service
sudo tee /etc/systemd/system/iot-ingest.service >/dev/null <<'EOF'
[Unit]
Description=IoT MQTT to PostgreSQL Ingestion
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=%i
WorkingDirectory=/opt/simple-meter-dashboard
Environment=DISABLE_ALERT_DISPATCH=1
Environment=METER_CONFIG_DIR=/opt/simple-meter-dashboard/iot_scripts
Environment=DB_HOST=localhost
Environment=DB_PORT=5432
ExecStart=/opt/simple-meter-dashboard/.venv/bin/python /opt/simple-meter-dashboard/iot_scripts/mqtt_to_db_ingest.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Replace %i with your actual username
sudo sed -i "s/User=%i/User=$USER/" /etc/systemd/system/iot-ingest.service

sudo systemctl daemon-reload
sudo systemctl enable --now iot-ingest.service

# Check status and logs
systemctl status iot-ingest.service --no-pager
journalctl -u iot-ingest.service -f
```

To deploy code updates to /opt later:
```bash
sudo rsync -a ~/simple-meter-dashboard/ /opt/simple-meter-dashboard/
sudo systemctl restart iot-ingest.service
```

## Troubleshooting

- MQTT not received:
  - Verify broker: `mosquitto_sub -t 'meter/readings' -v -C 1`
  - Confirm ingestion shows `[DEBUG] Subscribed to meter/readings`.

- DB auth or connection errors:
  - Check Postgres is running: `systemctl status postgresql`
  - Validate creds: `psql "postgresql://mfmuser:devi@localhost:5432/mfmdb" -c '\\dt'`
  - Ensure pg_hba.conf has `host all all 127.0.0.1/32 md5` and reload Postgres.

- Config conflicts:
  - The script prefers `/home/<user>/meter_config/config.json` if it exists. Override with `METER_CONFIG_DIR` to point to the repo’s `iot_scripts`.

## Notes

- Docker is not required for this host-based setup. If you later run the Django app in Docker and still want to use host PostgreSQL, set `DB_HOST=host.docker.internal` in the container and add `extra_hosts: ["host.docker.internal:host-gateway"]` to the service.
- Alerts are stubbed via `DISABLE_ALERT_DISPATCH=1`. Remove that environment variable when you’re ready to enable Redis/Celery.
