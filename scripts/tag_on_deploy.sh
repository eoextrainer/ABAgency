#!/usr/bin/env bash
set -euo pipefail

TAG_PREFIX=${TAG_PREFIX:-deploy}
TAG_NAME="${TAG_PREFIX}-$(date +%Y%m%d-%H%M%S)"

if ! git diff --quiet; then
  echo "Working tree not clean. Commit changes before tagging."
  exit 1
fi

git tag "$TAG_NAME"
git push origin "$TAG_NAME"

echo "Created and pushed tag: $TAG_NAME"
