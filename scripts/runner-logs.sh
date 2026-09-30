#!/bin/bash
# Workers Logs for the lineup-runner Worker, one line per event, newest first.
# Usage: scripts/runner-logs.sh [hours=6] [text to search for]
# Needs CF_ACCOUNT_ID and CF_OBSERVABILITY_TOKEN (repo .env).
set -euo pipefail

hours="${1:-6}"
needle="${2:-}"
: "${CF_ACCOUNT_ID:?missing; see the repo .env}" "${CF_OBSERVABILITY_TOKEN:?missing; see the repo .env}"

now=$(($(date +%s) * 1000))
from=$((now - hours * 3600 * 1000))

body=$(jq -n --argjson from "$from" --argjson to "$now" --arg needle "$needle" '{
  queryId: "runner-logs", view: "events", limit: 1000,
  timeframe: { from: $from, to: $to },
  parameters: ({ filters: [{ key: "$metadata.service", operation: "eq", type: "string", value: "lineup-runner" }] }
    + (if $needle == "" then {} else { needle: { value: $needle, isRegex: false, matchCase: false } } end))
}')

curl -sf -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/workers/observability/telemetry/query" \
  -H "Authorization: Bearer $CF_OBSERVABILITY_TOKEN" -H "Content-Type: application/json" -d "$body" |
  jq -r '.result.events.events[]
    | .["$metadata"] as $m | .["$workers"] as $w
    | [ (.timestamp / 1000 | strflocaltime("%m-%d %H:%M:%S %Z")),
        $m.origin, $m.trigger, $m.level,
        (if $w.outcome then "outcome=\($w.outcome) wall=\($w.wallTimeMs)ms cpu=\($w.cpuTimeMs)ms" else empty end),
        (if (.source | keys) == ["level", "message"] then .source.message else (.source | tojson) end)
      ] | join("  ")'
