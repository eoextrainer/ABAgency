#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"

if ./scripts/healthcheck.sh; then
  echo "App healthy."
  exit 0
fi

echo "Healthcheck failed. Attempting rollback..."
./scripts/rollback.sh
