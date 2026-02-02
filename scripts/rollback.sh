#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-${LAST_GOOD_TAG:-}}"

if [[ -z "$TAG" ]]; then
  echo "No tag provided. Set LAST_GOOD_TAG or pass a tag as the first argument."
  exit 1
fi

git fetch --tags

echo "Rolling back to tag: $TAG"
git checkout "$TAG"

if [[ -f docker-compose.yml ]] || [[ -f docker-compose.yaml ]]; then
  if command -v docker >/dev/null 2>&1; then
    docker compose up -d --build
  fi
fi

echo "Rollback completed."
