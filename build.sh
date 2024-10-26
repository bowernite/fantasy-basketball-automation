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

log_step "📁 Creating temporary directory"
# Create a temporary directory
TEMP_DIR=$(mktemp -d)
TEMP_JS_FILE="$TEMP_DIR/temp.js"

log_step "🔎 Determining TypeScript file to transpile"
# Check for main.ts, then package.json entrypoint, then index.ts
if [ -f "./main.ts" ]; then
  TS_FILE="./main.ts"
elif [ -f "./package.json" ]; then
  ENTRYPOINT=$(node -p "require('./package.json').main")
  if [ -n "$ENTRYPOINT" ] && [ -f "$ENTRYPOINT" ]; then
    TS_FILE="$ENTRYPOINT"
  fi
fi

if [ -z "$TS_FILE" ] && [ -f "./index.ts" ]; then
  TS_FILE="./index.ts"
fi

if [ -z "$TS_FILE" ]; then
  echo "❌ No TypeScript file found. Please ensure main.ts, a valid entrypoint in package.json, or index.ts exists."
  rm -rf "$TEMP_DIR"
  exit 1
fi

log_step "🔄 Transpiling TypeScript to JavaScript"
# Transpile TypeScript to JavaScript
if [ "$TRANSPILE_CMD" = "bun build" ]; then
  $TRANSPILE_CMD "$TS_FILE" --outfile="$TEMP_JS_FILE"
else
  $TRANSPILE_CMD --outFile "$TEMP_JS_FILE" "$TS_FILE"
fi

# Check if transpilation was successful
if [ $? -ne 0 ]; then
  echo "❌ Transpilation failed. Please check your TypeScript code."
  rm -rf "$TEMP_DIR"
  exit 1
fi

log_step "📋 Copying transpiled JavaScript to clipboard"
# Copy the transpiled JavaScript to clipboard
cat "$TEMP_JS_FILE" | $CLIPBOARD_CMD

echo "✅ Transpiled JavaScript has been copied to clipboard."

log_step "🧹 Cleaning up temporary files"
# Clean up temporary files
rm -rf "$TEMP_DIR"
