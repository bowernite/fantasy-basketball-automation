#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

SAFARI_DIR="${SAFARI_DIR:-$ROOT_DIR/.safari}"
SAFARI_XCODE_DIR="${SAFARI_XCODE_DIR:-$SAFARI_DIR/xcode}"
SAFARI_WEB_EXTENSION_DIR="${SAFARI_WEB_EXTENSION_DIR:-$SAFARI_DIR/web-extension}"

SAFARI_APP_NAME="${SAFARI_APP_NAME:-Fantasy Basketball Automation}"
SAFARI_BUNDLE_ID_PREFIX="${SAFARI_BUNDLE_ID_PREFIX:-com.local}"
SAFARI_CONVERTER_BUNDLE_ID="${SAFARI_CONVERTER_BUNDLE_ID:-$SAFARI_BUNDLE_ID_PREFIX.placeholder}"

if [ ! -d "$SAFARI_WEB_EXTENSION_DIR" ]; then
  echo "❌ Missing Safari web extension source dir: $SAFARI_WEB_EXTENSION_DIR"
  echo "Run: bun run safari:sync"
  exit 1
fi

mkdir -p "$SAFARI_XCODE_DIR"

xcrun safari-web-extension-converter "$SAFARI_WEB_EXTENSION_DIR" \
  --project-location "$SAFARI_XCODE_DIR" \
  --app-name "$SAFARI_APP_NAME" \
  --bundle-identifier "$SAFARI_CONVERTER_BUNDLE_ID" \
  --macos-only \
  --no-open \
  --no-prompt \
  --force

bash "$ROOT_DIR/scripts/safari/fix-bundle-ids.sh"

echo "✅ Safari Xcode project generated in: $SAFARI_XCODE_DIR"

