#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

SAFARI_DIR="${SAFARI_DIR:-$ROOT_DIR/.safari}"
SAFARI_XCODE_DIR="${SAFARI_XCODE_DIR:-$SAFARI_DIR/xcode}"
SAFARI_DERIVED_DATA_DIR="${SAFARI_DERIVED_DATA_DIR:-$SAFARI_DIR/DerivedData}"

SAFARI_APP_NAME="${SAFARI_APP_NAME:-Fantasy Basketball Automation}"
SAFARI_SCHEME="${SAFARI_SCHEME:-$SAFARI_APP_NAME}"

XCODEPROJ_PATH="$(find "$SAFARI_XCODE_DIR" -name "*.xcodeproj" | head -n 1 || true)"
if [ -z "$XCODEPROJ_PATH" ]; then
  echo "❌ No .xcodeproj found under: $SAFARI_XCODE_DIR"
  echo "Run: bun run safari:init"
  exit 1
fi

rm -rf "$SAFARI_DERIVED_DATA_DIR"
mkdir -p "$SAFARI_DERIVED_DATA_DIR"

xcodebuild \
  -project "$XCODEPROJ_PATH" \
  -scheme "$SAFARI_SCHEME" \
  -configuration Debug \
  -derivedDataPath "$SAFARI_DERIVED_DATA_DIR" \
  build

APP_PATH="$(find "$SAFARI_DERIVED_DATA_DIR" -type d -name "*.app" -path "*/Build/Products/Debug/*" | head -n 1 || true)"
if [ -z "$APP_PATH" ]; then
  echo "✅ Build complete, but could not find a .app under: $SAFARI_DERIVED_DATA_DIR"
  exit 0
fi

echo "✅ Build complete: $APP_PATH"
echo "Next: open \"$APP_PATH\""

