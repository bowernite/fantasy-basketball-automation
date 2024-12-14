#!/bin/bash

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function for pretty logging with emojis
log_step() {
  echo -e "\n🚀 \033[1;34m==>\033[0m \033[1m$1\033[0m"
}

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

log_step "📁 Creating dist directory"
# Create dist directory if it doesn't exist
mkdir -p ./chrome-extension/dist

log_step "🔄 Transpiling TypeScript to JavaScript"
# Transpile TypeScript to JavaScript
if [ "$TRANSPILE_CMD" = "bun build" ]; then
  $TRANSPILE_CMD "./main.ts" --outfile="./chrome-extension/dist/main.js"
  $TRANSPILE_CMD "./page-load__set-lineup.ts" --outfile="./chrome-extension/dist/page-load__set-lineup.js"
else
  $TRANSPILE_CMD "./main.ts" --outFile "./chrome-extension/dist/main.js"
  $TRANSPILE_CMD "./page-load__set-lineup.ts" --outFile "./chrome-extension/dist/page-load__set-lineup.js"
fi

# Check if transpilation was successful
if [ $? -ne 0 ]; then
  echo "❌ Transpilation failed. Please check your TypeScript code."
  exit 1
fi

log_step "📋 Copying transpiled JavaScript to clipboard"
# Copy the transpiled JavaScript to clipboard
cat "./chrome-extension/dist/main.js" | $CLIPBOARD_CMD

echo "✅ Successfully built JavaScript to ./chrome-extension/dist/main.js and copied to clipboard"

log_step "🔄 Copying Chrome Extension background file"
cp ./chrome-extension/background.js ./chrome-extension/dist/background.js

log_step "🔄 Opening Chrome Extension"
open -a "Google Chrome"

# if [[ "$*" == *"--run"* ]]; then
# TODO: Click chrome extension icon
# fi
