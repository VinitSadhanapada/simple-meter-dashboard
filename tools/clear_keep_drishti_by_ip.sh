#!/usr/bin/env bash
set -euo pipefail

# Lightweight, robust script to keep only meter_readings for a Raspberry Pi
# identified by IP. It previews rows to be deleted, can create a pg_dump
# backup and can execute the DELETE inside a transaction (interactive).

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

echo "Using PG_DSN=${PG_DSN}"
echo "Target IP=${IP}"

# Find candidate columns in device_config_raspberrypi to match the IP
cols=$(psql "$PG_DSN" -Atc "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='device_config_raspberrypi';")
if [ -z "$cols" ]; then
  echo "Table device_config_raspberrypi not found in public schema."
  exit 1
fi

conds=()
for c in $cols; do
  lc=$(echo "$c" | tr '[:upper:]' '[:lower:]')
  if [[ "$lc" == *ip* || "$lc" == *host* || "$lc" == *addr* || "$lc" == *location* ]]; then
    conds+=("$c = '$IP'")
    conds+=("lower($c::text) LIKE '%$IP%'")
  fi
done

if [ ${#conds[@]} -eq 0 ]; then
  echo "No IP-like columns found; showing first 200 rows for manual inspection."
  psql "$PG_DSN" -c "SELECT * FROM public.device_config_raspberrypi LIMIT 200;"
  exit 1
fi

where_clause=""
for i in "${!conds[@]}"; do
  if [ $i -eq 0 ]; then
    where_clause="${conds[$i]}"
  else
    where_clause+=" OR ${conds[$i]}"
  fi
done

sql="SELECT id, pi_name, location FROM public.device_config_raspberrypi WHERE ${where_clause};"
echo "Running: $sql"
rows=$(psql "$PG_DSN" -Atc "$sql")
if [ -z "$rows" ]; then
  echo "No matching Raspberry Pi rows found."; exit 1
fi

echo "Found Raspberry Pi rows (id|pi_name|location):"
echo "$rows"

ids=()
while IFS='|' read -r id rest; do
  ids+=("$id")
done <<< "$rows"

# Detect likely FK column in device_config_meterdevice that references the RPI
md_rpi_col=""
md_cols=$(psql "$PG_DSN" -Atc "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='device_config_meterdevice';")
if [ -n "$md_cols" ]; then
  for prefer in raspberry_pi raspberry_pi_id raspberrypi_id rpi rpi_id; do
    if echo "$md_cols" | grep -xq "$prefer"; then
      md_rpi_col="$prefer"; break
    fi
  done
  if [ -z "$md_rpi_col" ]; then
    md_rpi_col=$(echo "$md_cols" | tr '\n' ' ' | tr ' ' '\n' | grep -Ei 'rasp|rpi|raspberry|pi' | head -n1 || true)
  fi
  if [ -z "$md_rpi_col" ]; then
    md_rpi_col=$(echo "$md_cols" | tr '\n' ' ' | tr ' ' '\n' | grep -E '_id$' | head -n1 || true)
  fi
fi

if [ -z "$md_rpi_col" ]; then
  echo "Could not detect meterdevice FK column. Enter it manually (e.g. raspberry_pi_id):"
  read -p "Column name: " md_rpi_col
fi

echo "Using device_config_meterdevice.$md_rpi_col as the RPI FK column"

if [ "$BACKUP" = true ]; then
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  dumpfile="meter_readings_backup_${ts}.dump"
  echo "Creating pg_dump of public.meter_readings -> $dumpfile"
  pg_dump "$PG_DSN" -t public.meter_readings -Fc -f "$dumpfile"
  echo "Backup complete: $dumpfile"
fi

for id in "${ids[@]}"; do
  echo
  echo "=== PREVIEW for Raspberry Pi id = $id ==="
  echo "Distinct meter_name that WOULD BE DELETED:"
  psql "$PG_DSN" -c "SELECT DISTINCT mr.meter_name FROM public.meter_readings mr WHERE mr.meter_name NOT IN (SELECT md.meter_name FROM device_config_meterdevice md WHERE md.\"$md_rpi_col\" = $id) ORDER BY 1 LIMIT 200;"

  echo "Count of rows that WOULD BE DELETED:"
  psql "$PG_DSN" -c "SELECT count(*) FROM public.meter_readings mr WHERE mr.meter_name NOT IN (SELECT md.meter_name FROM device_config_meterdevice md WHERE md.\"$md_rpi_col\" = $id);"

  echo "Sample rows that WOULD BE DELETED (50):"
  psql "$PG_DSN" -c "SELECT * FROM public.meter_readings mr WHERE mr.meter_name NOT IN (SELECT md.meter_name FROM device_config_meterdevice md WHERE md.\"$md_rpi_col\" = $id) ORDER BY mr.time DESC LIMIT 50;"

  if [ "$EXECUTE" = true ]; then
    echo "About to DELETE non-Drishti readings for RPI id $id (transactional)."
    read -p "Type DELETE to proceed: " confirm
    if [ "$confirm" != "DELETE" ]; then
      echo "Confirmation failed; skipping deletion for id $id."; continue
    fi

    psql "$PG_DSN" <<SQL
BEGIN;
DELETE FROM public.meter_readings
WHERE meter_name NOT IN (
  SELECT md.meter_name FROM device_config_meterdevice md WHERE md."$md_rpi_col" = $id
);
COMMIT;
VACUUM ANALYZE public.meter_readings;
SQL

    echo "Deletion completed for id $id"
  else
    echo "Run again with --execute to perform deletion for id $id (backup recommended)."
  fi
done

echo "Done."
#!/usr/bin/env bash
set -euo pipefail

# Safe helper to find Raspberry Pi entries by IP and preview/delete meter_readings
# Usage:
#   export PG_DSN="postgresql://user:password@host:5432/dbname"
#   ./clear_keep_drishti_by_ip.sh [IP] [--execute] [--backup]
# Example:
#   export PG_DSN="postgresql://postgres:secret@localhost:5432/smpdb"
#   ./clear_keep_drishti_by_ip.sh 192.168.112.91 --backup

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
  echo "ERROR: PG_DSN not set. Set it to a Postgres DSN, e.g."
  echo "  export PG_DSN='postgresql://user:password@host:5432/dbname'"
  exit 1
fi

echo "Using PG_DSN=${PG_DSN}"
echo "Target IP = ${IP}"

# Inspect columns in device_config_raspberrypi to identify candidate columns
cols=$(psql "$PG_DSN" -Atc "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='device_config_raspberrypi';")
if [ -z "$cols" ]; then
  echo "Could not find table 'device_config_raspberrypi' in public schema. Aborting."
  exit 1
fi

# Build WHERE conditions on likely column names
conds=()
for c in $cols; do
  lc=$(echo "$c" | tr '[:upper:]' '[:lower:]')
  if [[ "$lc" == *ip* || "$lc" == *host* || "$lc" == *addr* || "$lc" == *address* || "$lc" == *location* ]]; then
    conds+=("$c = '$IP'")
    conds+=("lower($c::text) LIKE '%$IP%'")
  fi
done

if [ ${#conds[@]} -eq 0 ]; then
  echo "No candidate columns found for IP match. Will print all rows and grep (fallback)."
  echo "Listing first 200 rows of device_config_raspberrypi (you can inspect for the IP):"
  psql "$PG_DSN" -c "SELECT * FROM public.device_config_raspberrypi LIMIT 200;"
  echo "If you see the row, re-run the script with the matching RPI id instead."
  exit 1
fi

# Compose WHERE clause
where_clause=""
for i in "${!conds[@]}"; do
  if [ $i -eq 0 ]; then
    where_clause="${conds[$i]}"
  else
    where_clause+=" OR ${conds[$i]}"
  fi
done

sql="SELECT id, pi_name, location FROM public.device_config_raspberrypi WHERE ${where_clause};"
echo "Searching for Raspberry Pi rows matching IP using the following SQL:"
echo "$sql"

# Execute and capture ids
rows=$(psql "$PG_DSN" -Atc "$sql")
if [ -z "$rows" ]; then
  echo "No rows found matching IP. Exiting."; exit 1
fi

echo "Found rows (id|pi_name|location):"
echo "$rows"

ids=()
while IFS='|' read -r id rest; do
  ids+=("$id")
done <<< "$rows"

# Detect the column in device_config_meterdevice that references the raspberry pi
md_rpi_col=""
md_cols=$(psql "$PG_DSN" -Atc "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='device_config_meterdevice';")
if [ -n "$md_cols" ]; then
  # Prefer common names first
  for prefer in raspberry_pi raspberry_pi_id raspberrypi_id rpi rpi_id raspberry pi raspberry_id; do
    if echo "$md_cols" | grep -xq "$prefer"; then
      md_rpi_col="$prefer"
      break
    fi
  done
  # Fallback: any column containing 'rasp' or 'rpi' or 'raspberry' or 'pi'
  if [ -z "$md_rpi_col" ]; then
    md_rpi_col=$(echo "$md_cols" | tr '\n' ' ' | tr ' ' '\n' | grep -Ei 'rasp|rpi|raspberry|pi' | head -n1 || true)
  fi
  # Final fallback: any *_id column
  if [ -z "$md_rpi_col" ]; then
    md_rpi_col=$(echo "$md_cols" | tr '\n' ' ' | tr ' ' '\n' | grep -E '_id$' | head -n1 || true)
  fi
fi

if [ -z "$md_rpi_col" ]; then
  echo "WARNING: Could not auto-detect raspberry-pi FK column in device_config_meterdevice."
  echo "Please specify the column name to use (example: raspberry_pi_id)."
  read -p "Column name: " md_rpi_col
fi

echo "Using meterdevice.rpi column: $md_rpi_col"

# If backup requested, run pg_dump for meter_readings
if [ "$BACKUP" = true ]; then
  timestamp=$(date -u +%Y%m%dT%H%M%SZ)
  dumpfile="meter_readings_backup_${timestamp}.dump"
  echo "Creating pg_dump for public.meter_readings -> $dumpfile"
  pg_dump "$PG_DSN" -t public.meter_readings -Fc -f "$dumpfile"
  echo "Backup written to $dumpfile"
fi

for id in "${ids[@]}"; do
  echo
  echo "=== PREVIEW for Raspberry Pi id = $id ==="
  echo "Meters that WOULD BE DELETED (distinct meter_name):"
  psql "$PG_DSN" -c "SELECT DISTINCT mr.meter_name FROM public.meter_readings mr WHERE mr.meter_name NOT IN (SELECT md.meter_name FROM device_config_meterdevice md WHERE md.\"$md_rpi_col\" = $id) ORDER BY 1 LIMIT 200;"

  echo "Count of rows that WOULD BE DELETED:"
  psql "$PG_DSN" -c "SELECT count(*) FROM public.meter_readings mr WHERE mr.meter_name NOT IN (SELECT md.meter_name FROM device_config_meterdevice md WHERE md.\"$md_rpi_col\" = $id);"

  echo "Preview of rows to be deleted (sample 50):"
  psql "$PG_DSN" -c "SELECT * FROM public.meter_readings mr WHERE mr.meter_name NOT IN (SELECT md.meter_name FROM device_config_meterdevice md WHERE md.\"$md_rpi_col\" = $id) ORDER BY mr.time DESC LIMIT 50;"

  if [ "$EXECUTE" = true ]; then
    echo "About to DELETE non-Drishti readings for RPI id $id. This will run inside a transaction."
    read -p "Type DELETE to proceed: " confirm
    if [ "$confirm" != "DELETE" ]; then
      echo "Confirmation failed; skipping deletion for id $id."; continue
    fi

    echo "Running DELETE inside transaction..."
    psql "$PG_DSN" <<SQL
BEGIN;
DELETE FROM public.meter_readings
WHERE meter_name NOT IN (
  SELECT md.meter_name FROM device_config_meterdevice md WHERE md."$md_rpi_col" = $id
);
COMMIT;
VACUUM ANALYZE public.meter_readings;
SQL
    echo "DELETE completed for id $id"
  else
    echo "To perform deletion for id $id, re-run with --execute. Recommended: create a backup first with --backup."
  fi
done

echo "Script finished. If you need a one-shot non-interactive run, I can prepare that too."
#!/usr/bin/env bash
set -euo pipefail

# Safe helper to find Raspberry Pi entries by IP and preview/delete meter_readings
# Usage:
#   export PG_DSN="postgresql://user:password@host:5432/dbname"
#   ./clear_keep_drishti_by_ip.sh [IP] [--execute] [--backup]
# Example:
#   export PG_DSN="postgresql://postgres:secret@localhost:5432/smpdb"
#   ./clear_keep_drishti_by_ip.sh 192.168.112.91 --backup

IP="${1:-192.168.112.91}"
EXECUTE=false
BACKUP=false
#!/usr/bin/env bash
set -euo pipefail

# Safe helper to find Raspberry Pi entries by IP and preview/delete meter_readings
# Usage:
#   export PG_DSN="postgresql://user:password@host:5432/dbname"
#   ./clear_keep_drishti_by_ip.sh [IP] [--execute] [--backup]
# Example:
#   export PG_DSN="postgresql://postgres:secret@localhost:5432/smpdb"
#   ./clear_keep_drishti_by_ip.sh 192.168.112.91 --backup

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
  echo "ERROR: PG_DSN not set. Set it to a Postgres DSN, e.g."
  echo "  export PG_DSN='postgresql://user:password@host:5432/dbname'"
  exit 1
fi

echo "Using PG_DSN=${PG_DSN}"
echo "Target IP = ${IP}"

# Inspect columns in device_config_raspberrypi to identify candidate columns
cols=$(psql "$PG_DSN" -Atc "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='device_config_raspberrypi';")
if [ -z "$cols" ]; then
  echo "Could not find table 'device_config_raspberrypi' in public schema. Aborting."
  exit 1
fi

# Build WHERE conditions on likely column names
conds=()
for c in $cols; do
  lc=$(echo "$c" | tr '[:upper:]' '[:lower:]')
  if [[ "$lc" == *ip* || "$lc" == *host* || "$lc" == *addr* || "$lc" == *address* || "$lc" == *location* ]]; then
    conds+=("$c = '$IP'")
    conds+=("lower($c::text) LIKE '%$IP%'")
  fi
done

if [ ${#conds[@]} -eq 0 ]; then
  echo "No candidate columns found for IP match. Will print all rows and grep (fallback)."
  echo "Listing first 200 rows of device_config_raspberrypi (you can inspect for the IP):"
  psql "$PG_DSN" -c "SELECT * FROM public.device_config_raspberrypi LIMIT 200;"
  echo "If you see the row, re-run the script with the matching RPI id instead."
  exit 1
fi

# Compose WHERE clause
where_clause=""
for i in "${!conds[@]}"; do
  if [ $i -eq 0 ]; then
    where_clause="${conds[$i]}"
  else
    where_clause+=" OR ${conds[$i]}"
  fi
done

sql="SELECT id, pi_name, location FROM public.device_config_raspberrypi WHERE ${where_clause};"
echo "Searching for Raspberry Pi rows matching IP using the following SQL:"
echo "$sql"

# Execute and capture ids
rows=$(psql "$PG_DSN" -Atc "$sql")
if [ -z "$rows" ]; then
  echo "No rows found matching IP. Exiting."; exit 1
fi

echo "Found rows (id|pi_name|location):"
echo "$rows"

ids=()
while IFS='|' read -r id rest; do
  ids+=("$id")
done <<< "$rows"

# Detect the column in device_config_meterdevice that references the raspberry pi
md_rpi_col=""
md_cols=$(psql "$PG_DSN" -Atc "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='device_config_meterdevice';")
if [ -n "$md_cols" ]; then
  # Prefer common names first
  for prefer in raspberry_pi raspberry_pi_id raspberrypi_id rpi rpi_id raspberry pi raspberry_id; do
    if echo "$md_cols" | grep -xq "$prefer"; then
      md_rpi_col="$prefer"
      break
    fi
  done
  # Fallback: any column containing 'rasp' or 'rpi' or 'raspberry' or 'pi'
  if [ -z "$md_rpi_col" ]; then
    md_rpi_col=$(echo "$md_cols" | tr '\n' ' ' | tr ' ' '\n' | grep -Ei 'rasp|rpi|raspberry|pi' | head -n1 || true)
  fi
  # Final fallback: any *_id column
  if [ -z "$md_rpi_col" ]; then
    md_rpi_col=$(echo "$md_cols" | tr '\n' ' ' | tr ' ' '\n' | grep -E '_id$' | head -n1 || true)
  fi
fi

if [ -z "$md_rpi_col" ]; then
  echo "WARNING: Could not auto-detect raspberry-pi FK column in device_config_meterdevice."
  echo "Please specify the column name to use (example: raspberry_pi_id)."
  read -p "Column name: " md_rpi_col
fi

echo "Using meterdevice.rpi column: $md_rpi_col"

# If backup requested, run pg_dump for meter_readings
if [ "$BACKUP" = true ]; then
  timestamp=$(date -u +%Y%m%dT%H%M%SZ)
  dumpfile="meter_readings_backup_${timestamp}.dump"
  echo "Creating pg_dump for public.meter_readings -> $dumpfile"
  pg_dump "$PG_DSN" -t public.meter_readings -Fc -f "$dumpfile"
  echo "Backup written to $dumpfile"
fi

for id in "${ids[@]}"; do
  echo
  echo "=== PREVIEW for Raspberry Pi id = $id ==="
  echo "Meters that WOULD BE DELETED (distinct meter_name):"
  psql "$PG_DSN" -c "SELECT DISTINCT mr.meter_name FROM public.meter_readings mr WHERE mr.meter_name NOT IN (SELECT md.meter_name FROM device_config_meterdevice md WHERE md.\"$md_rpi_col\" = $id) ORDER BY 1 LIMIT 200;"

  echo "Count of rows that WOULD BE DELETED:"
  psql "$PG_DSN" -c "SELECT count(*) FROM public.meter_readings mr WHERE mr.meter_name NOT IN (SELECT md.meter_name FROM device_config_meterdevice md WHERE md.\"$md_rpi_col\" = $id);"

  echo "Preview of rows to be deleted (sample 50):"
  psql "$PG_DSN" -c "SELECT * FROM public.meter_readings mr WHERE mr.meter_name NOT IN (SELECT md.meter_name FROM device_config_meterdevice md WHERE md.\"$md_rpi_col\" = $id) ORDER BY mr.time DESC LIMIT 50;"

  if [ "$EXECUTE" = true ]; then
    echo "About to DELETE non-Drishti readings for RPI id $id. This will run inside a transaction."
    read -p "Type DELETE to proceed: " confirm
    if [ "$confirm" != "DELETE" ]; then
      echo "Confirmation failed; skipping deletion for id $id."; continue
    fi

    echo "Running DELETE inside transaction..."
    psql "$PG_DSN" <<SQL
BEGIN;
DELETE FROM public.meter_readings
WHERE meter_name NOT IN (
  SELECT md.meter_name FROM device_config_meterdevice md WHERE md."$md_rpi_col" = $id
);
COMMIT;
VACUUM ANALYZE public.meter_readings;
SQL
    echo "DELETE completed for id $id"
  else
    echo "To perform deletion for id $id, re-run with --execute. Recommended: create a backup first with --backup."
  fi
done

echo "Script finished. If you need a one-shot non-interactive run, I can prepare that too."
