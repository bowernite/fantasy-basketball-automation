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

DEVELOPMENT_TEAM_FILE="$SAFARI_DIR/development-team.txt"
DEVELOPMENT_TEAM_ID=""
if [ -f "$DEVELOPMENT_TEAM_FILE" ]; then
  DEVELOPMENT_TEAM_ID="$(tr -d '[:space:]' < "$DEVELOPMENT_TEAM_FILE" || true)"
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

perl -pi -e 's/^\s*"CODE_SIGN_IDENTITY\[sdk=macosx\*\]" = "-";\n//mg' "$PBXPROJ_PATH"

if [ -n "$DEVELOPMENT_TEAM_ID" ]; then
  perl -pi -e 's/^\s*DEVELOPMENT_TEAM = [A-Z0-9]+;\n//mg' "$PBXPROJ_PATH"
  perl -pi -e "s/(CODE_SIGN_STYLE = Automatic;\\n)/\$1\\t\\t\\t\\tDEVELOPMENT_TEAM = $DEVELOPMENT_TEAM_ID;\\n/g" "$PBXPROJ_PATH"
  echo "✅ Development team applied: $DEVELOPMENT_TEAM_ID"
else
  echo "ℹ️ No $DEVELOPMENT_TEAM_FILE found; leaving DEVELOPMENT_TEAM as-is"
fi

echo "✅ Bundle identifiers aligned:"
echo "   App:       $APP_BUNDLE_ID"
echo "   Extension: $EXTENSION_BUNDLE_ID"

