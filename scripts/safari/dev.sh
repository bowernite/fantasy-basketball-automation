#!/bin/bash

set -euo pipefail

bun run build:only
bun run safari:sync

XCODEPROJ_PATH="$(find "./.safari/xcode" -name "*.xcodeproj" | head -n 1 || true)"
if [ -z "$XCODEPROJ_PATH" ]; then
  bun run safari:init
fi

bun run safari:build

