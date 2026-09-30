---
description: Use when debugging, checking or changing the cloud auto-lineup runner (Cloudflare Worker `lineup-runner`): its runs, logs, alerts, cron, deploys or saves, or Fleaflicker login and lineup-save mechanics
---

The runner is a Cloudflare Worker (`wrangler.jsonc`, `src/worker/`) that logs in to Fleaflicker, decides the lineup with the extension's code and stores a record per run. `$LINEUP_RUNNER_*` and `$CF_*` below come from the repo's `.env` (gitignored, already exported in agent shells).

## Where to look

Check in this order; stop once the failing run and its cause are found.

1. **Run records** (last 20, newest first): `curl -s -H "Authorization: Bearer $LINEUP_RUNNER_TOKEN" "$LINEUP_RUNNER_URL/runs"`. Each record has the trigger (`cron`, `alarm`, `manual`), login result, lineup-page status, the decision (starters, errors, warnings) and any thrown `error`. A missing record for an expected time means the run never started or died mid-way: go to 2
2. **Workers Logs** (Worker and Durable Object `console.*` output, invocations incl. cron with outcome and CPU, exceptions; ~7 days): `scripts/runner-logs.sh [hours=6] [search text]`, one line per event, newest first. For counts/trends over time, the `cloudflare-observability` MCP's `query_worker_observability` `calculations` view works; its `events` view fails on this Worker's Durable Object events, so read log lines with the script
3. **Live**: `bunx wrangler tail lineup-runner --format json > /tmp/<file>` in the background, then trigger or wait for a run
4. **Deploys**: `bunx wrangler deployments list` (which version was live when a run failed)

`GET $LINEUP_RUNNER_URL/status` (same auth) shows the next alarm and upcoming tips. Ticks with nothing due write no run record; the alarm re-arms at least every 5 min.

`GET /captures` (same auth) has the lineup page HTML and `FetchRoster` JSON behind each day check with problems, plus each day's first check with locked rows (newest 10, ~300 KB each): write it to `/tmp` and debug parsing from the real page. `GET /alerts` lists every alert sent (last 50), including missed-tip alerts, which never appear in run records.

Deploy only with `scripts/deploy-runner.sh`: it refuses within 90 min of a tip and keeps the cron trigger (plain `wrangler deploy` pauses cron ~30–45 min).

`POST $LINEUP_RUNNER_URL/run` (same auth) runs the lineup now: only when the user asks.

A bad save in progress: `PUT $LINEUP_RUNNER_URL/saves` with `{"enabled": false}` stops saving at once, no deploy.

## Where output lands

During a run `src/worker/decide-lineup.ts` swaps `console`, so shared code's logs don't all reach Workers Logs. Read its console handling before concluding a log line was never written.

## Setup gaps

- `cloudflare-observability` missing or "needs authentication": the user runs `claude mcp login cloudflare-observability` in a terminal in this repo (OAuth in the browser)
- `$CF_OBSERVABILITY_TOKEN` missing or rejected: create a user API token at dash.cloudflare.com/profile/api-tokens with only Account › Workers Observability › Read, and save it to `.env` with `CF_ACCOUNT_ID` (`bunx wrangler whoami`)
- `$LINEUP_RUNNER_TOKEN` missing: it's the Worker's `RUN_TOKEN` secret, which can't be read back. Generate a new token, set it with `bunx wrangler secret put RUN_TOKEN` (stdin), and save it to `.env`
- The repo is public: keep run records and logs in `/tmp`, never in the repo

## Tests

`CI=1 bunx vitest run --silent=true src/worker` (workerd pool; `bun test` skips `src/worker/`)

# Additional resources

- [How it works](./how-it-works.md): tick and run flow, design decisions and why. Read before changing the runner
- [Fleaflicker facts](./fleaflicker.md): login, lineup page and form, save responses, signed-in API, `/api/SetLineup`, injury feeds
- [Operations](./operations.md): the saves switch, live save tests, deploys, secrets and alert setup, test gotchas
- [Open items](./open-items.md): what needs the user, game-day tasks (e.g. the opening-night capture), backlog
