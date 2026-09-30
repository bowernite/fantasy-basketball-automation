#!/bin/bash
# Deploys the lineup-runner Worker: tests, refuses within 90 min of a tip (a deploy kills in-flight runs and resets cron), then checks the alarm is armed.
# Usage: scripts/deploy-runner.sh [--force]
# Needs LINEUP_RUNNER_URL and LINEUP_RUNNER_TOKEN (repo .env).
set -euo pipefail
cd "$(dirname "$0")/.."

: "${LINEUP_RUNNER_URL:?missing; see the repo .env}" "${LINEUP_RUNNER_TOKEN:?missing; see the repo .env}"
tip_guard_minutes=90

status() { curl -sf -H "Authorization: Bearer $LINEUP_RUNNER_TOKEN" "$LINEUP_RUNNER_URL/status"; }

CI=1 bunx vitest run --silent=true src/worker

if [ "${1:-}" != "--force" ]; then
  next_tip=$(status | jq -r --argjson minutes "$tip_guard_minutes" \
    '[.upcomingTips[].at | select(sub("\\.[0-9]+Z$"; "Z") | fromdateiso8601 < now + $minutes * 60)] | first // empty')
  if [ -n "$next_tip" ]; then
    echo "Refusing: a tip is at $next_tip (within $tip_guard_minutes min). Deploy after it, or pass --force." >&2
    exit 1
  fi
fi

bunx wrangler deploy

# The previous version can keep serving for ~30 s after a deploy
sleep 40
status | jq -e '.alarm != null' >/dev/null || { echo "No alarm armed after deploy: POST /run starts the schedule" >&2; exit 1; }
status | jq '{alarm, savesEnabled, nextTip: .upcomingTips[0]}'
