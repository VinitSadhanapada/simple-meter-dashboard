#!/usr/bin/env bash
# tools/pg_dump_full_sql.sh
#
# Create a plain SQL dump of the entire PostgreSQL cluster (all databases)
# Usage:
#   ./pg_dump_full_sql.sh -U <db_user> -h <host> -p <port> -o /path/to/output.sql [--compress]
# Examples:
#   ./pg_dump_full_sql.sh -U postgres -h localhost -p 5432 -o /tmp/mfmdb_all_$(date +%F).sql
#   ./pg_dump_full_sql.sh -U mquser -h db.example.local -p 5432 -o ./mfmdb_all.sql --compress
#
# Notes:
# - This script uses `pg_dumpall` (produces plain SQL suitable for psql restore).
# - For large DBs consider using the custom/directory format with `pg_dump -F c`.
# - To avoid interactive password prompts, configure `~/.pgpass` or export PGPASSWORD
#   (export PGPASSWORD='yourpassword') before running. Using environment variables
#   on the command line may expose passwords in process listings; prefer `.pgpass`.

set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 -U <db_user> -h <host> -p <port> -o <output.sql> [--compress]

Options:
  -U <db_user>    PostgreSQL user to run pg_dumpall as (required)
  -h <host>       PostgreSQL host (default: localhost)
  -p <port>       PostgreSQL port (default: 5432)
  -o <output.sql> Output path for the plain SQL dump (required)
  --compress      gzip the output (.gz appended)
  -n              Dry-run: show the pg_dumpall command that will be run
  -?              Show this help

Examples:
  $0 -U postgres -h localhost -p 5432 -o /tmp/pg_all_2025-12-13.sql
  PGPASSWORD=mysecret $0 -U postgres -h dbhost -o /tmp/dump.sql --compress
EOF
}

DB_USER=""
DB_HOST=localhost
DB_PORT=5432
OUTFILE=""
COMPRESS=0
DRY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -U) DB_USER="$2"; shift 2;;
    -h) DB_HOST="$2"; shift 2;;
    -p) DB_PORT="$2"; shift 2;;
    -o) OUTFILE="$2"; shift 2;;
    --compress) COMPRESS=1; shift;;
    -n) DRY=1; shift;;
    -?) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 2;;
  esac
done

if [[ -z "$DB_USER" || -z "$OUTFILE" ]]; then
  echo "ERROR: -U and -o are required" >&2
  usage
  exit 2
fi

TIMESTAMP=$(date +%F_%H%M%S)
OUTDIR=$(dirname "$OUTFILE")
BASENAME=$(basename "$OUTFILE")

mkdir -p "$OUTDIR"

if [[ $COMPRESS -eq 1 ]]; then
  FINAL_OUT="${OUTFILE}.gz"
else
  FINAL_OUT="$OUTFILE"
fi

CMD=(pg_dumpall -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT")

echo "Prepared to run: ${CMD[*]} > $FINAL_OUT"
if [[ $DRY -eq 1 ]]; then
  exit 0
fi

# Run the dump. If compression requested, pipe through gzip.
if [[ $COMPRESS -eq 1 ]]; then
  # Use stdbuf to avoid buffering issues on some systems, but it's optional.
  stdbuf -oL "${CMD[@]}" | gzip -9 > "$FINAL_OUT"
else
  stdbuf -oL "${CMD[@]}" > "$FINAL_OUT"
fi

echo "Dump completed: $FINAL_OUT"
echo "Suggested verification:"
echo "  head -n 40 $FINAL_OUT"
echo "  gzip -t $FINAL_OUT (if compressed)"
echo "To restore the SQL dump: psql -U <user> -d postgres -f $FINAL_OUT"

exit 0
