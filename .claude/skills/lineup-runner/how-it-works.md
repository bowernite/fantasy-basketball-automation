# How the lineup runner works

The goal: the user's lineup is set optimally and reliably for every game, with no dependence on the user's Mac, and anything unexpected reaches the user. The browser extension (`page-load__set-lineup.ts`, `src/lineup/`) stays the manual path; the Worker (`src/worker/`) is the unattended one. Both run the same `src/` scoring and optimizer.

## A tick

- Clocks: the `*/5` cron and the Durable Object alarm both call `tick()` on the one DO (`primary`). Every tick re-arms the alarm at most 5 min out, so either clock alone keeps the schedule alive, and double firing is harmless
- Planning needs no network: `planTick()` (`lineup-schedule.ts`) reads stored tip tables, the per-day run ledger and cached lineup periods
- Targets: T-40 and T-15 before every distinct tip time of the user's players, plus hourly at :05 (today and tomorrow, so an early game is pre-set even if the morning's runs die). A target is done only by an ok run for that day; failures retry every tick until T-3
- Missed tip: from T-10, a day with no ok run since T-45 sends an emergency alert, once per tip
- Tip times come from the lineup page's `local-time[datetime]`, so any early, international or holiday game gets the same targets with no special case

## A run

1. Log in (cached `cookieId`; fresh login when a page comes back signed out)
2. Per day: GET the lineup page for an explicit `week=N` in the fantasy-stats view, plus the signed-in `FetchRoster` for the same day. Day `N` comes from the API's `eligibleLineupPeriods`, never the default page (the league day ends 6a ET)
3. `decideLineup()`: runs the extension's `setLineup()` on the page, parsed with linkedom plus a small form-control shim, then serializes the whole form and checks invariants. It fails closed on an error banner, no form, page vs API disagreement, an empty or over-filled slot, or a select with no slot chosen
4. When saves are on and something changed: `saveLineup()` POSTs the whole form, then reloads the page and diffs every posted slot. No POST within 3 min of a tip
5. After every day is saved: the ESPN injury cross-check (alert only)
6. Record to DO SQLite (`GET /runs`), alert on problems or warnings. A day with problems, or the day's first check with locked rows, also keeps its page and roster (`GET /captures`), since in-game markup is gone by the next day

## The watchdog

A second vendor watches the Worker: `.github/workflows/lineup-watchdog.yml` runs `src/watchdog/lineup-watchdog.ts` at :07/:22/:37/:52 (GitHub starts it 5–20 min late). It reads `/runs`, `/status` and `/alerts` and pushes to the user's ntfy topic when:

- no run record in 75 min (hourly runs always write one): "Lineup runner silent"
- the alarm is unset or >15 min overdue: "Lineup runner alarm stuck"
- any route fails or times out: "Lineup runner unreachable"
- a Worker alert ≤6 h old hasn't been forwarded yet (priority 2 → ntfy 5, 1 → 4, 0 → 3, Trello-only → 2, silent)

It keeps no state: it reads the topic's last 12 h from ntfy and skips an alert whose title was pushed after the alert's `at`, and repeats its own three alerts at most every 3 h. Any push fails the job, so GitHub also emails the user. It covers Cloudflare down, a billing lapse and a broken deploy, which the Worker can't report itself

## Decisions and why

- **Watchdog pulls, from GitHub**: ntfy is reachable from GitHub runners, and pulling keeps any GitHub token out of the Worker. GitHub's late schedule is fine for a watchdog, not for the runner itself
- **Cloudflare Worker + Durable Object** over GitHub Actions (cron often late or dropped, which is fatal at T-15; logs would be public) and over a hosted LLM agent such as Grokbot (imprecise timing, usage caps, less accurate than the optimizer). Workers Paid is required: a run uses ~20 ms CPU, over Free's 10 ms
- **Reuse the extension's code through linkedom**, one `src/`, rather than porting or splitting it. Shim gaps fail silently (a missing `option.text` once started 0 players with no error), so the invariants in step 3 are mandatory. happy-dom can't run in Workers and misreads `<option selected>`
- **The runner guards legality itself**: Fleaflicker accepts an under-filled lineup. The page vs API cross-check catches markup drift before anything is saved
- **Whole-form POST, not `/api/SetLineup`**: the form is atomic and proven (accepted, rejected and no-op responses all seen); SetLineup is one swap per call, non-atomic, and can't fill an empty slot. It stays a fallback only if the form path proves brittle
- **Verify by reload, never by the save response**: a rejected save re-renders the form with the rejected values
- **ESPN is a cross-check, not a scoring input**: it only has Out / Day-To-Day and is UA-gated. Its value is catching Fleaflicker's stale OUT/OFS tags, which score ×0. Revisit an OUT-only override after opening-week data (`open-items.md`)
- **Questionable players keep the ×0.5 expected-value model** (`src/prioritization/injury-adjustments.ts`). Timing is the fix: T-40/T-15 runs see most Q players resolved
- **Alerts**: urgent → Pushover (priority 1 when a tip is ≤3 h away, 2 for a missed tip) and Trello; general → a Trello card in the user's To-Do Inbox, comment on the open card on repeats. ntfy can't be reached from Workers (shared egress IPs hit its per-IP quota; 522s). Trello cards made with the user's own token never notify him, so Trello is never the only urgent channel. A healthchecks.io ping each tick is the dead-man for "the Worker stopped". Every alert is also logged on the channels' dedupe schedule, delivered or not, and served on `GET /alerts` for the watchdog below
- **Failed logins and failed saves back off 30 min** except within 45 min of a tip, to avoid a captcha or lockout
- **No runtime self-healing**: a failure alerts, and a human merges any fix. Code that rewrites itself while writing the user's lineup is the wrong risk on a public repo
- **Saves are a runtime switch** (`PUT /saves`, DO storage, default off), so turning them off needs no deploy
