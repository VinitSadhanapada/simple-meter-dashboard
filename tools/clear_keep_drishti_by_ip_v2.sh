#!/usr/bin/env bash
set -euo pipefail

# clear_keep_drishti_by_ip_v2.sh
# Keep only readings whose `pi_ip` equals the target IP. Preview, backup and
# optionally delete other readings.

IP="${1:-192.168.112.91}"
EXECUTE=false
BACKUP=false

for arg in "${@:2}"; do
  case "$arg" in
    --execute) EXECUTE=true ;;
    --backup) BACKUP=true ;;
    *) ;;
  esac
done
VACUUM ANALYZE public.meter_readings;
  echo "Deletion finished."
fi
#!/usr/bin/env bash
set -euo pipefail

# clear_keep_drishti_by_ip_v2.sh
# Keep only readings whose `pi_ip` equals the target IP. Preview, backup and
# optionally delete other readings.

IP="${1:-192.168.112.91}"
EXECUTE=false
BACKUP=false

for arg in "${@:2}"; do
  case "$arg" in
    --execute) EXECUTE=true ;;
    --backup) BACKUP=true ;;
    *) ;;
  esac
done

if [ -z "${PG_DSN:-}" ]; then
  echo "ERROR: PG_DSN not set. Export a Postgres DSN like:"
  echo "  export PG_DSN='postgresql://user:password@host:5432/dbname'"
  exit 1
fi

echo "Using PG_DSN=$PG_DSN"
echo "Target IP=$IP"

if [ "$BACKUP" = true ]; then
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  dumpfile="meter_readings_backup_${ts}.dump"
  echo "Creating pg_dump -> $dumpfile"
  pg_dump "$PG_DSN" -t public.meter_readings -Fc -f "$dumpfile"
  echo "Backup saved: $dumpfile"
fi

echo "--- Preview (matching by pi_ip) ---"
psql "$PG_DSN" -c "SELECT count(*) AS total_rows FROM public.meter_readings;"
psql "$PG_DSN" -c "SELECT count(*) AS kept_rows FROM public.meter_readings WHERE pi_ip = '$IP';"
psql "$PG_DSN" -c "SELECT count(*) AS rows_to_delete FROM public.meter_readings WHERE pi_ip IS NULL OR pi_ip <> '$IP';"

psql "$PG_DSN" -c "SELECT DISTINCT meter_name, pi_ip FROM public.meter_readings WHERE pi_ip IS NULL OR pi_ip <> '$IP' ORDER BY 1 LIMIT 200;"
psql "$PG_DSN" -c "SELECT * FROM public.meter_readings WHERE pi_ip IS NULL OR pi_ip <> '$IP' ORDER BY time DESC LIMIT 50;"

if [ "$EXECUTE" = true ]; then
  read -p "Type DELETE to confirm deletion of rows where pi_ip IS NULL or <> $IP: " confirm
  if [ "$confirm" != "DELETE" ]; then
    echo "Aborting deletion."; exit 0
  fi

  psql "$PG_DSN" <<'SQL'
BEGIN;
DELETE FROM public.meter_readings
WHERE pi_ip IS NULL OR pi_ip <> '$IP';
COMMIT;
VACUUM ANALYZE public.meter_readings;
SQL

  echo "Deletion finished."
else
  echo "Re-run with --execute to perform deletion (backup recommended)."
fi

echo "All done."
    *) ;;
  esac
done

if [ -z "${PG_DSN:-}" ]; then
  echo "ERROR: PG_DSN not set. Export a Postgres DSN like:"
  echo "  export PG_DSN='postgresql://user:password@host:5432/dbname'"
  exit 1
fi

echo "Using PG_DSN=$PG_DSN"
echo "Target IP=$IP"

# Find candidate columns in device_config_raspberrypi
cols=$(psql "$PG_DSN" -Atc "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='device_config_raspberrypi';")
if [ -z "$cols" ]; then
  echo "device_config_raspberrypi not found. Aborting."; exit 1
fi

conds=()
for c in $cols; do
  lc=$(echo "$c" | tr '[:upper:]' '[:lower:]')
  if [[ "$lc" == *ip* || "$lc" == *host* || "$lc" == *addr* || "$lc" == *location* ]]; then
    conds+=("$c = '$IP'")
    conds+=("lower($c::text) LIKE '%$IP%'")
    where_clause="${conds[$i]}"
  #!/usr/bin/env bash
  set -euo pipefail

  # clear_keep_drishti_by_ip_v2.sh
  # Matches and keeps readings by the `pi_ip` column on `meter_readings`.
  # Usage:
  #   export PG_DSN="postgresql://user:password@host:5432/dbname"
  #   ./clear_keep_drishti_by_ip_v2.sh 192.168.112.91 [--backup] [--execute]

  IP="${1:-192.168.112.91}"
  EXECUTE=false
  BACKUP=false

  for arg in "${@:2}"; do
    case "$arg" in
      --execute) EXECUTE=true ;;
      --backup) BACKUP=true ;;
      *) ;;
    esac
  done

  if [ -z "${PG_DSN:-}" ]; then
    echo "ERROR: PG_DSN not set. Export a Postgres DSN like:"
    echo "  export PG_DSN='postgresql://user:password@host:5432/dbname'"
    exit 1
  fi

  echo "Using PG_DSN=$PG_DSN"
  echo "Target IP=$IP"

  if [ "$BACKUP" = true ]; then
    ts=$(date -u +%Y%m%dT%H%M%SZ)
    dumpfile="meter_readings_backup_${ts}.dump"
    echo "Creating pg_dump -> $dumpfile"
    pg_dump "$PG_DSN" -t public.meter_readings -Fc -f "$dumpfile"
    echo "Backup saved: $dumpfile"
  fi

  echo "--- Preview (matching by pi_ip) ---"
  echo "Total rows in meter_readings:"
  psql "$PG_DSN" -c "SELECT count(*) FROM public.meter_readings;"

  echo "Rows that WILL BE KEPT (pi_ip = '$IP'):"
  psql "$PG_DSN" -c "SELECT count(*) FROM public.meter_readings WHERE pi_ip = '$IP';"

  echo "Rows that WILL BE DELETED (pi_ip IS NULL OR pi_ip <> '$IP'):"
  psql "$PG_DSN" -c "SELECT count(*) FROM public.meter_readings WHERE pi_ip IS NULL OR pi_ip <> '$IP';"

  echo "Distinct meter_name and pi_ip that WOULD BE DELETED (first 200):"
  psql "$PG_DSN" -c "SELECT DISTINCT meter_name, pi_ip FROM public.meter_readings WHERE pi_ip IS NULL OR pi_ip <> '$IP' ORDER BY 1 LIMIT 200;"

  echo "Sample rows that WOULD BE DELETED (50):"
  psql "$PG_DSN" -c "SELECT * FROM public.meter_readings WHERE pi_ip IS NULL OR pi_ip <> '$IP' ORDER BY time DESC LIMIT 50;"

  if [ "$EXECUTE" = true ]; then
    read -p "Type DELETE to confirm deletion of rows where pi_ip IS NULL or <> $IP: " confirm
    if [ "$confirm" != "DELETE" ]; then echo "Aborting deletion."; exit 0; fi

    psql "$PG_DSN" <<SQL
  BEGIN;
  DELETE FROM public.meter_readings
  WHERE pi_ip IS NULL OR pi_ip <> '$IP';
  COMMIT;
  VACUUM ANALYZE public.meter_readings;
  SQL

    echo "Deletion finished."
  else
    echo "Re-run with --execute to perform deletion (backup recommended)."
  fi

  echo "All done."