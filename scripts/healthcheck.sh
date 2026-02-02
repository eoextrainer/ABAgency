#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"

curl -fsS "$BASE_URL/" > /dev/null
curl -fsS "$BASE_URL/assets" > /dev/null

echo "Healthcheck OK: $BASE_URL"
