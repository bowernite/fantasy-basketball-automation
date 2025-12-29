#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

SAFARI_DIR="${SAFARI_DIR:-$ROOT_DIR/.safari}"
SAFARI_XCODE_DIR="${SAFARI_XCODE_DIR:-$SAFARI_DIR/xcode}"

PBXPROJ_PATH="$(find "$SAFARI_XCODE_DIR" -name "project.pbxproj" | head -n 1 || true)"
if [ -z "$PBXPROJ_PATH" ]; then
  echo "❌ No project.pbxproj found under: $SAFARI_XCODE_DIR"
  exit 1
fi

APP_BUNDLE_ID="$(
  grep -E 'PRODUCT_BUNDLE_IDENTIFIER = ".*";' "$PBXPROJ_PATH" \
    | grep -v '\.Extension"' \
    | head -n 1 \
    | sed -E 's/.*"([^"]+)".*/\1/'
)"
if [ -z "$APP_BUNDLE_ID" ]; then
  echo "❌ Could not determine app bundle identifier from: $PBXPROJ_PATH"
  exit 1
fi

EXTENSION_BUNDLE_ID="${APP_BUNDLE_ID}.Extension"

perl -pi -e "s/PRODUCT_BUNDLE_IDENTIFIER = ([^;]*\\.Extension|\\\"[^\\\"]*\\.Extension\\\");/PRODUCT_BUNDLE_IDENTIFIER = \\\"$EXTENSION_BUNDLE_ID\\\";/g" "$PBXPROJ_PATH"

echo "✅ Bundle identifiers aligned:"
echo "   App:       $APP_BUNDLE_ID"
echo "   Extension: $EXTENSION_BUNDLE_ID"

