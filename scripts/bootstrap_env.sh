#!/usr/bin/env bash
set -euo pipefail

# Initialize .env from template and ensure FIELD_ENCRYPTION_KEY is set

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    echo "Created .env from .env.example"
  else
    echo "No .env or .env.example found; creating minimal .env" >&2
    touch .env
  fi
fi

# Read existing value if present
KEY_LINE=$(grep -E '^FIELD_ENCRYPTION_KEY=' .env || true)
if [[ -z "$KEY_LINE" || "$KEY_LINE" == "FIELD_ENCRYPTION_KEY="* ]]; then
  echo "Generating FIELD_ENCRYPTION_KEY..."
  PYTHON=$(command -v python3 || command -v python)
  if [[ -z "$PYTHON" ]]; then
    echo "Python is required to generate the key. Install python3." >&2
    exit 1
  fi
  KEY=$($PYTHON - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
)
  if grep -qE '^FIELD_ENCRYPTION_KEY=' .env; then
    sed -i "s/^FIELD_ENCRYPTION_KEY=.*/FIELD_ENCRYPTION_KEY=${KEY}/" .env
  else
    echo "FIELD_ENCRYPTION_KEY=${KEY}" >> .env
  fi
  echo "FIELD_ENCRYPTION_KEY set in .env"
else
  echo "FIELD_ENCRYPTION_KEY already present in .env"
fi

echo "Done."
