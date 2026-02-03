#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
COOKIE_JAR=$(mktemp)

cleanup() {
  rm -f "$COOKIE_JAR"
}
trap cleanup EXIT

curl -fsS "$BASE_URL/" > /dev/null
curl -fsS "$BASE_URL/assets" > /dev/null

curl -fsS -c "$COOKIE_JAR" -d "email=artist@abagency.com&password=User123!" "$BASE_URL/login" > /dev/null
curl -fsS -b "$COOKIE_JAR" "$BASE_URL/workspace" > /dev/null

curl -fsS -b "$COOKIE_JAR" -H "Content-Type: application/json" \
  -d '{"title":"Test Event","event_date":"2030-01-01","location":"Test"}' \
  "$BASE_URL/api/events" > /dev/null

curl -fsS -b "$COOKIE_JAR" -H "Content-Type: application/json" \
  -d '{"title":"Test Performance","performance_date":"2030-01-02","fee":100}' \
  "$BASE_URL/api/performances" > /dev/null

curl -fsS -b "$COOKIE_JAR" -H "Content-Type: application/json" \
  -d '{"body":"Hello moderator","to_moderator":true}' \
  "$BASE_URL/api/messages" > /dev/null

echo "All checks passed."
