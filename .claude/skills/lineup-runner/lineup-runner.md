---
description: Use when debugging or checking the cloud auto-lineup runner (Cloudflare Worker `lineup-runner`): its runs, logs, alerts, cron or deploys
---

The runner is a Cloudflare Worker (`wrangler.jsonc`, `src/worker/`) that logs in to Fleaflicker, decides the lineup with the extension's code and stores a record per run. `$LINEUP_RUNNER_URL` and `$LINEUP_RUNNER_TOKEN` come from the repo's `.env` (gitignored, already exported in agent shells).

## Where to look

Check in this order; stop once the failing run and its cause are found.

1. **Run records** (last 20, newest first): `curl -s -H "Authorization: Bearer $LINEUP_RUNNER_TOKEN" "$LINEUP_RUNNER_URL/runs"`. Each record has the trigger (`cron`, `alarm`, `manual`), login result, lineup-page status, the decision (starters, errors, warnings) and any thrown `error`. A missing record for an expected time means the run never started or died mid-way: go to 2
2. **Workers Logs** (Worker and Durable Object `console.*` output, invocations incl. cron, exceptions; ~7 days): `cloudflare-observability` MCP, `query_worker_observability` on Worker `lineup-runner`. Use `observability_keys` / `observability_values` to find fields to filter on
3. **Live**: `bunx wrangler tail lineup-runner --format json > /tmp/<file>` in the background, then trigger or wait for a run
4. **Deploys**: `bunx wrangler deployments list` (which version was live when a run failed)

`POST $LINEUP_RUNNER_URL/run` (same auth) runs the lineup now: only when the user asks.

## Where output lands

During a run `src/worker/decide-lineup.ts` swaps `console`, so shared code's logs don't all reach Workers Logs. Read its console handling before concluding a log line was never written.

## Setup gaps

- `cloudflare-observability` missing or "needs authentication": the user runs `claude mcp login cloudflare-observability` in a terminal in this repo (OAuth in the browser)
- `$LINEUP_RUNNER_TOKEN` missing: it's the Worker's `RUN_TOKEN` secret, which can't be read back. Generate a new token, set it with `bunx wrangler secret put RUN_TOKEN` (stdin), and save it to `.env`
- The repo is public: keep run records and logs in `/tmp`, never in the repo

## Tests

`bunx vitest run --silent=true src/worker` (workerd pool; `bun test` skips `src/worker/`)
