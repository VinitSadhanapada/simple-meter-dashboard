#!/usr/bin/env bash
set -euo pipefail

# Restore PostgreSQL dump into the compose-managed database

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

DUMP_PATH="postgresql_schema_dump/mfmdb.dump"

if [[ ! -f "$DUMP_PATH" ]]; then
  echo "Dump file not found at $DUMP_PATH" >&2
  exit 1
fi

echo "Copying dump into DB container..."
docker compose cp "$DUMP_PATH" db:/tmp/mfmdb.dump

echo "Running pg_restore (may take a while)..."
docker compose exec -T db bash -lc 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" /tmp/mfmdb.dump'

echo "Restore complete. Listing tables:"
docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c '\dt'

echo "Done."
