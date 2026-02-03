#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/deploy_render_db.sh [--url DATABASE_URL] [--schema schema.sql] [--seed sample_data.sql] [--backup-dir backups] [--restore-latest] [--test]

Options:
  --url            Database connection string (overrides DATABASE_URL env)
  --schema         Path to schema file (default: schema.sql)
  --seed           Path to seed file (default: sample_data.sql)
  --backup-dir     Directory for SQL backups (default: backups)
  --restore-latest Restore the most recent backup and exit
  --test           Run connectivity + savepoint/rollback tests
USAGE
}

DB_URL="${DATABASE_URL:-}"
SCHEMA_FILE="schema.sql"
SEED_FILE="sample_data.sql"
BACKUP_DIR="backups"
RESTORE_LATEST=0
RUN_TESTS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      DB_URL="$2"
      shift 2
      ;;
    --schema)
      SCHEMA_FILE="$2"
      shift 2
      ;;
    --seed)
      SEED_FILE="$2"
      shift 2
      ;;
    --backup-dir)
      BACKUP_DIR="$2"
      shift 2
      ;;
    --restore-latest)
      RESTORE_LATEST=1
      shift
      ;;
    --test)
      RUN_TESTS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
 done

if [[ -z "$DB_URL" ]]; then
  echo "DATABASE_URL is not set. Provide --url or export DATABASE_URL." >&2
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "psql not found in PATH." >&2
  exit 1
fi

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "pg_dump not found in PATH." >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

latest_backup() {
  ls -1t "$BACKUP_DIR"/backup_*.sql 2>/dev/null | head -n 1 || true
}

restore_latest() {
  local backup
  backup="$(latest_backup)"
  if [[ -z "$backup" ]]; then
    echo "No backups found in $BACKUP_DIR" >&2
    exit 1
  fi
  echo "Restoring from $backup"
  psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$backup"
}

if [[ "$RESTORE_LATEST" -eq 1 ]]; then
  restore_latest
  exit 0
fi

backup_file="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

echo "Creating backup: $backup_file"
pg_dump "$DB_URL" --format=plain --no-owner --no-privileges > "$backup_file"

if [[ "$RUN_TESTS" -eq 1 ]]; then
  echo "Running connectivity test"
  psql "$DB_URL" -v ON_ERROR_STOP=1 -c "SELECT 1;"

  echo "Running savepoint/rollback test"
  before_users="$(psql "$DB_URL" -t -A -c "SELECT COUNT(*) FROM users;")"
  psql "$DB_URL" -v ON_ERROR_STOP=1 <<'SQL'
BEGIN;
SAVEPOINT deploy_test;
INSERT INTO users (email, password_hash, name, role)
VALUES ('rollback_test@abagency.com', 'test', 'Rollback Test', 'community');
ROLLBACK TO SAVEPOINT deploy_test;
COMMIT;
SQL
  after_users="$(psql "$DB_URL" -t -A -c "SELECT COUNT(*) FROM users;")"
  if [[ "$before_users" != "$after_users" ]]; then
    echo "Savepoint test failed: user counts changed." >&2
    exit 1
  fi
  echo "Savepoint/rollback test passed"
fi

echo "Applying schema + seed with savepoint"
if ! psql "$DB_URL" -v ON_ERROR_STOP=1 <<SQL
BEGIN;
SAVEPOINT deploy_seed;
\i $SCHEMA_FILE
\i $SEED_FILE
COMMIT;
SQL
then
  echo "Deploy failed. Restoring backup: $backup_file" >&2
  psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$backup_file"
  exit 1
fi

echo "Database deploy completed successfully"
