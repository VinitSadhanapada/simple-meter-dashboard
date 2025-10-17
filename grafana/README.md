# Grafana Dashboard Setup for Meter Data

This folder provides a ready-to-import dashboard JSON plus optional provisioning files to avoid UID issues.

## Option A — Manual Setup (simplest)
1. In Grafana, create a PostgreSQL data source:
   - Name: Postgres-MeterDB (or any name)
   - Host: localhost:5432
   - Database: mfmdb
   - User: mfmuser
   - Password: devi
   - SSL Mode: disable
2. Import the dashboard JSON:
   - Go to Dashboards → Import
   - Upload `grafana/dashboards/meter_readings_dashboard.json`
   - When prompted for data sources, select your Postgres data source for the placeholder.
   - Note: The JSON uses an input `${DS_POSTGRES}` so there’s no hard-coded UID.

## Option B — Provisioning (auto-load)
1. Copy provisioning files into Grafana paths (adjust for your system):
   - Datasource: `grafana/provisioning/datasources/postgres.yaml` → `/etc/grafana/provisioning/datasources/postgres.yaml`
   - Dashboards: `grafana/provisioning/dashboards/dashboards.yaml` → `/etc/grafana/provisioning/dashboards/dashboards.yaml`
2. Place dashboards in the directory specified by `dashboards.yaml`:
   - Copy `grafana/dashboards/meter_readings_dashboard.json` → `/var/lib/grafana/dashboards/meter_readings_dashboard.json`
3. Restart Grafana:
   - `sudo systemctl restart grafana-server`

## Notes about UIDs
- Grafana assigns a UID to each data source and dashboard. The provided dashboard JSON uses an input placeholder for the data source, so you won’t hit a UID mismatch.
- If you prefer to bake in a specific UID, set your Postgres data source’s UID in Grafana, then search/replace `${DS_POSTGRES}` in the JSON with that UID.

## SQL behind the panels
- Recent table:
  ```sql
  SELECT * FROM meter_readings ORDER BY time DESC LIMIT 20;
  ```
- Voltages timeseries:
  ```sql
  SELECT time AS "time", meter_name, v_r_ph, v_y_ph, v_b_ph
  FROM meter_readings
  WHERE $__timeFilter(time)
  ORDER BY time ASC
  LIMIT 10000;
  ```
- Currents timeseries:
  ```sql
  SELECT time AS "time", meter_name, a_r_ph, a_y_ph, a_b_ph
  FROM meter_readings
  WHERE $__timeFilter(time)
  ORDER BY time ASC
  LIMIT 10000;
  ```
- Latest frequency:
  ```sql
  SELECT frequency FROM meter_readings ORDER BY time DESC LIMIT 1;
  ```
- Latest PF:
  ```sql
  SELECT pf_ave FROM meter_readings ORDER BY time DESC LIMIT 1;
  ```
- Meter list:
  ```sql
  SELECT DISTINCT meter_name FROM meter_readings ORDER BY meter_name;
  ```
- Variable example (`$meter_name`):
  ```sql
  SELECT time AS "time", v_r_ph
  FROM meter_readings
  WHERE meter_name = '$meter_name' AND $__timeFilter(time)
  ORDER BY time ASC
  LIMIT 10000;
  ```

## Troubleshooting
- If panels show “no data”, verify Postgres connectivity and that the `time` column is timestamp with data in range.
- If provisioning doesn’t load, check Grafana logs: `journalctl -u grafana-server -f` and ensure paths in YAML match your system.
- For large datasets, consider adding indexes on `meter_readings(time)` and `meter_readings(meter_name, time)` for better performance.
