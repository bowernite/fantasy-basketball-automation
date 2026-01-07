#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

SAFARI_DIR="${SAFARI_DIR:-$ROOT_DIR/.safari}"
SAFARI_XCODE_DIR="${SAFARI_XCODE_DIR:-$SAFARI_DIR/xcode}"
SAFARI_DERIVED_DATA_DIR="${SAFARI_DERIVED_DATA_DIR:-$SAFARI_DIR/DerivedData-Archive}"
SAFARI_ARCHIVE_DIR="${SAFARI_ARCHIVE_DIR:-$SAFARI_DIR/archive}"
SAFARI_EXPORT_DIR="${SAFARI_EXPORT_DIR:-$SAFARI_DIR/export}"

SAFARI_APP_NAME="${SAFARI_APP_NAME:-Fantasy Basketball Automation}"
SAFARI_SCHEME="${SAFARI_SCHEME:-$SAFARI_APP_NAME}"

DEVELOPMENT_TEAM_FILE="$SAFARI_DIR/development-team.txt"
DEVELOPMENT_TEAM_ID=""
if [ -f "$DEVELOPMENT_TEAM_FILE" ]; then
  DEVELOPMENT_TEAM_ID="$(tr -d '[:space:]' < "$DEVELOPMENT_TEAM_FILE" || true)"
fi

XCODEPROJ_PATH="$(find "$SAFARI_XCODE_DIR" -name "*.xcodeproj" | head -n 1 || true)"
if [ -z "$XCODEPROJ_PATH" ]; then
  echo "❌ No .xcodeproj found under: $SAFARI_XCODE_DIR"
  echo "Run: bun run safari:init"
  exit 1
fi

mkdir -p "$SAFARI_ARCHIVE_DIR" "$SAFARI_EXPORT_DIR"
rm -rf "$SAFARI_DERIVED_DATA_DIR"
mkdir -p "$SAFARI_DERIVED_DATA_DIR"

ARCHIVE_PATH="$SAFARI_ARCHIVE_DIR/$SAFARI_APP_NAME.xcarchive"
rm -rf "$ARCHIVE_PATH"

EXPORT_OPTIONS_PLIST="$SAFARI_DIR/ExportOptions.plist"
cat > "$EXPORT_OPTIONS_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>method</key>
  <string>development</string>
  <key>signingStyle</key>
  <string>automatic</string>
  <key>teamID</key>
  <string>${DEVELOPMENT_TEAM_ID}</string>
</dict>
</plist>
EOF

xcodebuild \
  -project "$XCODEPROJ_PATH" \
  -scheme "$SAFARI_SCHEME" \
  -configuration Release \
  -derivedDataPath "$SAFARI_DERIVED_DATA_DIR" \
  -destination "generic/platform=macOS" \
  -allowProvisioningUpdates \
  archive \
  -archivePath "$ARCHIVE_PATH" \
  -quiet

rm -rf "$SAFARI_EXPORT_DIR"
mkdir -p "$SAFARI_EXPORT_DIR"

xcodebuild \
  -exportArchive \
  -archivePath "$ARCHIVE_PATH" \
  -exportPath "$SAFARI_EXPORT_DIR" \
  -exportOptionsPlist "$EXPORT_OPTIONS_PLIST" \
  -allowProvisioningUpdates \
  -quiet

EXPORTED_APP_PATH="$(find "$SAFARI_EXPORT_DIR" -maxdepth 2 -type d -name "*.app" | head -n 1 || true)"
if [ -z "$EXPORTED_APP_PATH" ]; then
  echo "✅ Export complete, but could not find a .app under: $SAFARI_EXPORT_DIR"
  exit 0
fi

echo "✅ Exported app: $EXPORTED_APP_PATH"
echo "Next: open \"$EXPORTED_APP_PATH\" once, then enable it in Safari -> Settings -> Extensions"


