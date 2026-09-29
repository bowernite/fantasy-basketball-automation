#!/bin/bash

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function for pretty logging with emojis
log_step() {
  echo -e "\n🚀 \033[1;34m==>\033[0m \033[1m$1\033[0m"
}

# Check if we should skip version bump and signing (for dev builds)
SKIP_VERSION_AND_SIGN=false
if [ "$1" = "--skip-version-sign" ]; then
  SKIP_VERSION_AND_SIGN=true
fi

if [ "$SKIP_VERSION_AND_SIGN" = false ]; then
  log_step "📝 Bumping version"
  # Read manifest.json, bump patch version, and write back
  MANIFEST_PATH="./extension/manifest.json"
  CURRENT_VERSION=$(node -pe "JSON.parse(require('fs').readFileSync('$MANIFEST_PATH', 'utf-8')).version")
  IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
  NEW_VERSION="${VERSION_PARTS[0]}.${VERSION_PARTS[1]}.$((VERSION_PARTS[2] + 1))"
  
  # Update manifest.json with new version
  node -e "
    const fs = require('fs');
    const manifest = JSON.parse(fs.readFileSync('$MANIFEST_PATH', 'utf-8'));
    manifest.version = '$NEW_VERSION';
    fs.writeFileSync('$MANIFEST_PATH', JSON.stringify(manifest, null, 2) + '\n');
  "
  
  echo "✅ Version bumped from $CURRENT_VERSION to $NEW_VERSION"
fi

log_step "🔍 Checking for TypeScript compiler"
# Check for TypeScript compiler
if command_exists bun; then
  TRANSPILE_CMD="bun build"
elif command_exists npm; then
  TRANSPILE_CMD="npx tsc"
elif command_exists yarn; then
  TRANSPILE_CMD="yarn tsc"
elif [ -f "./node_modules/.bin/tsc" ]; then
  TRANSPILE_CMD="./node_modules/.bin/tsc"
else
  echo "❌ No TypeScript compiler found. Please install Bun, npm, or Yarn, or ensure tsc is in node_modules."
  exit 1
fi

log_step "📋 Checking for clipboard command"
# Check if pbcopy (macOS) is available
if command_exists pbcopy; then
  CLIPBOARD_CMD="pbcopy"
else
  echo "❌ pbcopy not found. Please ensure you're running this on macOS."
  exit 1
fi

log_step "📊 Regenerating player projections from the projections snapshot"
if ! python3 ./.claude/skills/projections/extension_data.py; then
  echo "❌ Could not regenerate src/data/player-data.ts"
  exit 1
fi

log_step "📁 Creating dist directory"
# Create dist directory if it doesn't exist
mkdir -p ./extension/dist

log_step "🔄 Transpiling TypeScript to JavaScript"
# Transpile TypeScript to JavaScript
if [ "$TRANSPILE_CMD" = "bun build" ]; then
  $TRANSPILE_CMD "./main.ts" --outfile="./extension/dist/main.js" &&
    $TRANSPILE_CMD "./page-load__set-lineup.ts" --outfile="./extension/dist/page-load__set-lineup.js"
else
  $TRANSPILE_CMD "./main.ts" --outFile "./extension/dist/main.js" &&
    $TRANSPILE_CMD "./page-load__set-lineup.ts" --outFile "./extension/dist/page-load__set-lineup.js"
fi

# Check if transpilation was successful
if [ $? -ne 0 ]; then
  echo "❌ Transpilation failed. Please check your TypeScript code."
  exit 1
fi

if [ -z "${SKIP_CLIPBOARD:-}" ]; then
  log_step "📋 Copying transpiled JavaScript to clipboard"
  cat "./extension/dist/main.js" | $CLIPBOARD_CMD
  echo "✅ Successfully built JavaScript to ./extension/dist/main.js and copied to clipboard"
fi

log_step "🔄 Copying extension background file"
cp ./extension/background.js ./extension/dist/background.js

echo "✅ Build complete!"

if [ "$SKIP_VERSION_AND_SIGN" = false ]; then
  log_step "🔐 Signing extension"
  
  # Check if .env file exists
  if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from env.signing.example"
    exit 1
  fi
  
  # Load environment variables and run web-ext sign
  if command_exists bun; then
    bun run sign
  elif command_exists npm; then
    npm run sign
  else
    echo "❌ Neither bun nor npx found. Cannot run signing command."
    exit 1
  fi
  
  if [ $? -ne 0 ]; then
    echo "❌ Signing failed. Please check your credentials in .env"
    exit 1
  fi
  
  echo ""
  echo "✅ Extension signed! Install the .xpi file from ./extension/signed directory"
  
  open -a "Zen" "about:addons"
fi
