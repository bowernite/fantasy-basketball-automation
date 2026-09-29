#!/bin/bash

set -euo pipefail

# One build at a time; a concurrent run waits for the first to finish
if [ -z "${SAFARI_DEV_LOCKED:-}" ]; then
  mkdir -p ./.safari
  exec env SAFARI_DEV_LOCKED=1 lockf -k ./.safari/dev.lock bash "$0" "$@"
fi

bun run build:only
bun run safari:sync

XCODEPROJ_PATH="$(find "./.safari/xcode" -name "*.xcodeproj" | head -n 1 || true)"
if [ -z "$XCODEPROJ_PATH" ]; then
  bun run safari:init
fi

bun run safari:build

