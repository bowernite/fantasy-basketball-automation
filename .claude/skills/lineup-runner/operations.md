# Operating the lineup runner

Auth on every route: `-H "Authorization: Bearer $LINEUP_RUNNER_TOKEN"` against `$LINEUP_RUNNER_URL`.

## Saves

- Automated saves are **on** (user approved 2026-09-30; first save by the 00:10Z cron run, 4 moves, Worker's reload verify passed, independent reload matched; the next run had no changes)
- `PUT /saves` with `{"enabled": true}` or `{"enabled": false}` switches automated saving at runtime; `GET /status` shows `savesEnabled`. It's the kill switch: no deploy needed. While off, every run still decides and records the lineup, and a Trello warning goes out when a tip is within 24 h
- A one-off live save test is allowed with the lead's or the user's OK: record the day's original form body first, `PUT /saves true` → `POST /run` → `PUT /saves false`, confirm the saved lineup with an independent reload, then POST the original body back and confirm the reload matches it. Run it away from tips and deploys (a deploy mid-test runs the old version for ~30 s)
- With saves on, the runs overwrite manual lineup edits within ~1 h; only `PUT /saves false` keeps a manual edit

## Deploys

- `scripts/deploy-runner.sh` deploys the working tree. When other sessions have uncommitted `src/` edits, deploy from a clean worktree of the commit you mean to ship
- Cron schedule changes need `bunx wrangler triggers deploy`; a new cron can take ~30 min to start firing
- Forced-failure alert test: `bunx wrangler versions upload --var LINEUP_URL:<a nonexistent team URL>`, then `bunx wrangler versions deploy <id>@100% -y` (keeps cron). `POST /run` then fails before any day (no capture); the next scheduled run fails per day and stores captures. Redeploy the previous version the same way. Its failure alerts go to Pushover too, so warn the user first. After: delete the Trello cards it made, and drop its `/alerts` entries with `DELETE /alerts/<id>` (same auth) before the watchdog's next run

## Secrets

Set from stdin, never in the repo or command args. Cron-safe: `bunx wrangler versions secret put <NAME>` per secret, then `bunx wrangler versions deploy <last version>@100% -y` (plain `secret put` re-sets the cron trigger and pauses it ~30–45 min; deploy outside a save test). Values can't be read back.

| Secret | Source |
|---|---|
| `FF_EMAIL`, `FF_PASSWORD` | repo `.env` |
| `RUN_TOKEN` | generated; copy to `.env` as `LINEUP_RUNNER_TOKEN` |
| `TRELLO_API_KEY`, `TRELLO_TOKEN` | `~/src/personal/assistant/.env` (the user's own token) |
| `TRELLO_LIST` | the user's To-Do board Inbox list id (a secret to keep it out of the repo) |
| `PUSHOVER_TOKEN`, `PUSHOVER_USER` | pushover.net: the dashboard's User Key, and an application "Lineup runner" at `pushover.net/apps/build` |
| `HEALTHCHECK_URL` | a healthchecks.io check: period 5 min, grace 15 min, notifying the user by its own Pushover or email integration |

`PUSHOVER_*` are set (app "Lineup runner"). `HEALTHCHECK_URL` is unset until the user makes the check (`open-items.md`); until then a channel with no secret records `{error: "… not set"}` and Trello still goes out. After setting either, send one test alert and have the user confirm it arrived. `NTFY_TOPIC` is unused: `bunx wrangler secret delete NTFY_TOPIC`.

## Watchdog

- The workflow's logs are public: the script prints counts only, and the Worker URL and token and the Pushover creds are GitHub secrets `LINEUP_RUNNER_URL`, `LINEUP_RUNNER_TOKEN`, `PUSHOVER_TOKEN`, `PUSHOVER_USER` (`gh secret set <NAME>` from stdin, no trailing newline). Rotating `RUN_TOKEN` means updating `LINEUP_RUNNER_TOKEN` too, or the watchdog alerts "unreachable"
- Runs: `gh run list --workflow lineup-watchdog.yml`. A failed run means it pushed something (or couldn't): check the phone or `/alerts`, not the log
- Test push: `gh workflow run lineup-watchdog.yml -f test=true` sends one "TEST: Lineup watchdog (GitHub Actions)"
- Forced-failure tests and other deliberate failures land in `/alerts`, so the watchdog forwards them to the user's phone within ~30 min. Warn the user first, or `DELETE /alerts/<id>` the test entries before the next watchdog run
- Local run (pushes to the real phone): `LINEUP_RUNNER_URL=… LINEUP_RUNNER_TOKEN=… PUSHOVER_TOKEN=… PUSHOVER_USER=… WATCHDOG_STATE_FILE=/tmp/wd.json bun src/watchdog/lineup-watchdog.ts`

## Tests

- Watchdog: `CI=1 bun test src/watchdog`
- `CI=1 bunx vitest run --silent=true src/worker` (`CI=1` stops empty inline snapshots from self-writing; bare `--silent` eats the next argument). Put the file path before `-u`, or `-u` applies to every file
- `bun test` over the whole repo can hang: pass it directories (`src/page src/prioritization src/lineup src/utils src/optimizer`)
- Fixtures: `src/lineup/fixtures/teampage-logged-in-fantasy-stats.html` (opening night, day 1) and `fetch-roster-week1-signed-in.json`; `src/worker/fixtures/` for ESPN. Scan any new capture for emails, cookies and tokens before adding it
- Durable Object timers: advance fake timers from inside the DO, `runInDurableObject(runner, () => vi.advanceTimersByTimeAsync(…))`; from the test context it hangs
- Module-level state in shared `src/` survives between runs in a warm isolate (the tooltip cache did); check for it before trusting per-run behavior
- workerd's `console` has no own enumerable methods: never copy it with `{...console}`
