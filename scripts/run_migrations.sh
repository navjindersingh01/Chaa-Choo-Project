#!/usr/bin/env bash
set -euo pipefail

# run_migrations.sh
# Helper to run DB migrations for Chaa Choo project in the recommended order,
# create a SQL dump backup, and optionally check the debug diagnostics endpoint.

# Usage: ./scripts/run_migrations.sh [--no-backup] [--check-endpoint]

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PY="$ROOT_DIR/venv/bin/python"
MYSQLDUMP=$(command -v mysqldump || true)
CURL=$(command -v curl || true)

# Defaults
DO_BACKUP=1
CHECK_ENDPOINT=0
PORT=${PORT:-8080}
HOST=${DB_HOST:-127.0.0.1}
DB_NAME=${DB_NAME:-cafe_ca3}
DB_USER=${DB_USER:-root}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-backup) DO_BACKUP=0; shift ;;
    --check-endpoint) CHECK_ENDPOINT=1; shift ;;
    --port) PORT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ ! -x "$VENV_PY" ]]; then
  echo "ERROR: Python virtualenv not found at $VENV_PY"
  echo "Create venv and install requirements first. Example: python3 -m venv venv && ./venv/bin/python -m pip install -r requirements.txt"
  exit 2
fi

cd "$ROOT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$ROOT_DIR/backups/${DB_NAME}_backup_${TIMESTAMP}.sql"

mkdir -p "$ROOT_DIR/backups"

if [[ $DO_BACKUP -eq 1 ]]; then
  if [[ -z "$MYSQLDUMP" ]]; then
    echo "mysqldump not found; skipping SQL backup. Install mysql client tools to enable backups."
  else
    echo "Creating DB backup to: $BACKUP_FILE"
    # Prompt for password if DB_PASSWORD not exported
    if [[ -z "${DB_PASSWORD:-}" ]]; then
      # run with prompt - user will be asked for password
      mysqldump -u "$DB_USER" -h "$DB_HOST" "$DB_NAME" > "$BACKUP_FILE"
    else
      mysqldump -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" "$DB_NAME" > "$BACKUP_FILE"
    fi
    echo "Backup complete"
  fi
fi

# Run migrations in order (idempotent scripts included in migrations/)
MIGRATIONS=("migrations/add_customer_fields.py" "migrations/upgrade_schema.py" "migrations/fix_order_items_price.py" "migrations/fix_order_status.py")

for m in "${MIGRATIONS[@]}"; do
  if [[ -f "$ROOT_DIR/$m" ]]; then
    echo "\n---- Running: $m ----"
    "$VENV_PY" "$ROOT_DIR/$m" || { echo "Migration $m failed"; exit 3; }
  else
    echo "Migration script not found: $m (skipping)"
  fi
done

echo "\nAll migrations executed.\n"

# Optionally start or restart the Flask app (user may prefer to manage this themselves)
cat <<'EOF'
Next steps you can run manually:

# 1) Stop any process using port 8081 (if you use 8081 as in RUN.md):
#    lsof -ti tcp:8081 | xargs -r kill -9

# 2) Start the Flask app (background):
#    PORT=8081 nohup ./venv/bin/python app.py > /tmp/flask_run.log 2>&1 &

# 3) Tail logs:
#    tail -f /tmp/flask_run.log

# 4) Test a public order (curl example):
#    curl -X POST http://localhost:8081/api/public/orders \
#      -H "Content-Type: application/json" \
#      -d '{"customer_name":"Test User","type":"takeaway","items":[{"item_id":1,"qty":2}],"total_amount":100.00}'
EOF

if [[ $CHECK_ENDPOINT -eq 1 ]]; then
  if [[ -z "$CURL" ]]; then
    echo "curl not found; skipping endpoint check"
    exit 0
  fi

  DIAG_URL="http://127.0.0.1:${PORT}/admin/check_migrations"
  echo "Checking diagnostics endpoint: $DIAG_URL"
  set +e
  resp=$(curl -s -S "$DIAG_URL")
  rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    echo "Failed to reach diagnostics endpoint (is the Flask app running on port ${PORT}?)."
    exit 4
  fi
  echo "Diagnostics response:\n$resp"
fi

echo "Done."
