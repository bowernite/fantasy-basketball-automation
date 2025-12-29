#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

SAFARI_DIR="${SAFARI_DIR:-$ROOT_DIR/.safari}"
SAFARI_WEB_EXTENSION_DIR="${SAFARI_WEB_EXTENSION_DIR:-$SAFARI_DIR/web-extension}"
EXTENSION_DIR="${EXTENSION_DIR:-$ROOT_DIR/extension}"

if [ ! -f "$EXTENSION_DIR/manifest.json" ]; then
  echo "❌ Missing: $EXTENSION_DIR/manifest.json"
  exit 1
fi

if [ ! -f "$EXTENSION_DIR/background.js" ]; then
  echo "❌ Missing: $EXTENSION_DIR/background.js"
  exit 1
fi

if [ ! -d "$EXTENSION_DIR/dist" ]; then
  echo "❌ Missing: $EXTENSION_DIR/dist"
  echo "Run: bun run build:only"
  exit 1
fi

if [ ! -d "$EXTENSION_DIR/icons" ]; then
  echo "❌ Missing: $EXTENSION_DIR/icons"
  exit 1
fi

rm -rf "$SAFARI_WEB_EXTENSION_DIR"
mkdir -p "$SAFARI_WEB_EXTENSION_DIR"

cp "$EXTENSION_DIR/manifest.json" "$SAFARI_WEB_EXTENSION_DIR/manifest.json"
cp "$EXTENSION_DIR/background.js" "$SAFARI_WEB_EXTENSION_DIR/background.js"
cp -R "$EXTENSION_DIR/dist" "$SAFARI_WEB_EXTENSION_DIR/dist"
cp -R "$EXTENSION_DIR/icons" "$SAFARI_WEB_EXTENSION_DIR/icons"

echo "✅ Synced Safari web extension source to: $SAFARI_WEB_EXTENSION_DIR"

