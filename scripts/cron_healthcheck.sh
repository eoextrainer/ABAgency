#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
LOG_FILE="${LOG_FILE:-/tmp/abagency_healthcheck.log}"

if ./scripts/healthcheck.sh; then
  echo "$(date -Iseconds) OK" >> "$LOG_FILE"
else
  echo "$(date -Iseconds) FAIL" >> "$LOG_FILE"
  ./scripts/self_heal.sh >> "$LOG_FILE" 2>&1 || true
fi
