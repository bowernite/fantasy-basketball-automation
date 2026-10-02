# How the lineup runner works

The goal: the user's lineup is set optimally and reliably for every game, with no dependence on the user's Mac, and anything unexpected reaches the user. The browser extension (`page-load__set-lineup.ts`, `src/lineup/`) stays the manual path; the Worker (`src/worker/`) is the unattended one. Both run the same `src/` scoring and optimizer.

## A tick

- Clocks: the `*/5` cron and the Durable Object alarm both call `tick()` on the one DO (`primary`). Every tick re-arms the alarm at most 5 min out, so either clock alone keeps the schedule alive, and double firing is harmless
- Planning needs no network: `planTick()` (`lineup-schedule.ts`) reads stored tip tables, the per-day run ledger and cached lineup periods
- Targets: T-40 and T-15 before every distinct tip time of the user's players, plus hourly at :05 (today and tomorrow, so an early game is pre-set even if the morning's runs die). A target is done only by an ok run for that day; a failed day retries every tick while a tip is ≤45 min away (until T-3), else every 30 min
- Missed tip: from T-10, a day with no ok run since T-45 sends an emergency alert, once per tip
- Tip times come from the lineup page's `local-time[datetime]`, so any early, international or holiday game gets the same targets with no special case

## A run

1. Log in (cached `cookieId`; fresh login when a page comes back signed out)
2. Per day: GET the lineup page for an explicit `week=N` in the fantasy-stats view, plus the signed-in `FetchRoster` for the same day. Day `N` comes from the API's `eligibleLineupPeriods`, never the default page (the league day ends 6a ET)
3. `decideLineup()`: runs the extension's `setLineup()` on the page, parsed with linkedom plus a small form-control shim, then serializes the whole form and checks invariants. It fails closed on an error banner, no form, page vs API disagreement, an empty or over-filled slot, or a select with no slot chosen
4. When saves are on and something changed: `saveLineup()` POSTs the whole form, then reloads the page and diffs every posted slot. No POST within 3 min of a tip
5. After every day is saved: untagged OUT news alerts (below), then the ESPN injury cross-check (alert only). Disagreements are always recorded but alert only from 3 days before the fantasy season's first day until a day after its last (from the stored `eligibleLineupPeriods`, so each season rolls over unattended; no periods stored → alert). Process failures and run warnings alert year-round. Untagged news needs a tip ≤36 h out, so it can't fire off-season either
6. Record to DO SQLite (`GET /runs`), alert on problems or warnings. A day with problems, or the day's first check with locked rows, also keeps its page and roster (`GET /captures`), since in-game markup is gone by the next day

## Untagged OUT news

News can rule a player out before Fleaflicker tags him (`untagged-news.ts`, `untagged-out-match.ts`). A false positive benches a healthy starter, so matching is strict and only ever lowers a player.

- Candidates: per day page, `findUntaggedNews` returns the tooltip news of every player with no `.injury` tag, with a loose `status` (OUT or D via `parsePlayerNews`, news ≤36 h old) when it has one. All of it goes to the strict matcher
- Recorded in `days[].untaggedOutNews` (`player`, `status`, `postedAt`, `headline`): every match, plus unmatched news with a loose `status`, so misses can be reviewed
- Strict match (`matchOutNews`) against his tip that day (`parseGameTips`; no game that day → no match). News must be posted 0–36 h before tip. The headline, then each body sentence (a truncated last fragment is dropped), is checked; the first that passes wins:
  - Day: every day reference names the tip's ET day (weekday, "Oct. 20" / "10/20", "tonight/today" if posted that ET day from 6a, "tomorrow" if posted the ET day before from 6a), and there is at least one
  - Rejected: hedges (could, might, may, would, likely, questionable, probable, upgraded…) and teammate wording (starts with "With", or has who, absence, in place of, usage, minutes, start…)
  - OUT: "ruled out", "will not / won't play", "out <day>", "out for/against (≤4 words) <day>"; not negated, not an idiom ("sat out", "closed out"…). Otherwise "doubtful" → D
- A match adds `tipAt` and `matched: {status, sentence}`. A matched OUT adds `wouldBench: true`. D never changes the lineup
- Act mode: before `decideLineup()`, his row is rewritten to carry an OUT tag (×0) with no news icon, so the news can't lift the tag. `wouldBench` becomes `benched: true` only if the decision moved him out of the starters; when no one with a game can replace him he still starts and keeps `wouldBench`
- Alerts, after the day loop: one per match, titled "Would bench X (news: out, no Fleaflicker tag)", "Benched X (news: out, no Fleaflicker tag)" or "News says X is doubtful"; body = headline, posted time (CT) and the quoted sentence. Pushover priority 1 if he's still a starter and his tip is ≤3 h away, else a Trello card. Dedupe on player + `postedAt`, repeat after 24 h, per channel (a later ≤3 h push still goes). Sends land in the run's `untaggedNewsAlerts`; a failure becomes a run warning
- Mode: DO storage `untaggedOutNewsAct`, default off (shadow); switch via `PUT /untagged-out-news` (`operations.md` §Untagged OUT news)
- Known risk: the matcher never sees the player's name, so news about a teammate still matches if it avoids the teammate words

## The watchdog

A second vendor watches the Worker: `.github/workflows/lineup-watchdog.yml` runs `src/watchdog/lineup-watchdog.ts` at :07/:22/:37/:52 (GitHub starts it 5–20 min late). It reads `/runs`, `/status` and `/alerts` and pushes to Pushover (app "Lineup runner") when:

- no run record in 75 min (hourly runs always write one): "Lineup runner silent"
- the alarm is unset or >15 min overdue: "Lineup runner alarm stuck"
- any route fails or times out: "Lineup runner unreachable"
- a Worker alert ≤6 h old hasn't been forwarded yet and isn't marked `delivered` (same Pushover priority; Trello-only → −1, quiet). Its own three alerts are priority 1

State (forwarded `/alerts` ids, when each own alert last went out) lives in a JSON file carried between runs by `actions/cache` (ids and times only: caches are readable from fork PRs). It repeats its own alerts at most every 3 h; a lost cache re-forwards ≤6 h of alerts. Any push fails the job, so GitHub also emails the user. It covers Cloudflare down, a billing lapse and a broken deploy, which the Worker can't report itself

## Decisions and why

- **Watchdog pulls, from GitHub, and pushes to Pushover**: Pushover limits per account, not per IP (ntfy's per-IP quota is shared by every runner or Worker on that IP), and pulling keeps any GitHub token out of the Worker. GitHub's late schedule is fine for a watchdog, not for the runner itself. An urgent push (priority 1 or 2) that Pushover rejects falls back to ntfy (`NTFY_TOPIC`, ntfy priority 5 / 4): GitHub's IPs rarely hit ntfy's shared quota, and a failed fallback is retried next run. Quiet and normal pushes don't fall back
- **Cloudflare Worker + Durable Object** over GitHub Actions (cron often late or dropped, which is fatal at T-15; logs would be public) and over a hosted LLM agent such as Grokbot (imprecise timing, usage caps, less accurate than the optimizer). Workers Paid is required: a run uses ~20 ms CPU, over Free's 10 ms
- **Reuse the extension's code through linkedom**, one `src/`, rather than porting or splitting it. Shim gaps fail silently (a missing `option.text` once started 0 players with no error), so the invariants in step 3 are mandatory. happy-dom can't run in Workers and misreads `<option selected>`
- **The runner guards legality itself**: Fleaflicker accepts an under-filled lineup. The page vs API cross-check catches markup drift before anything is saved
- **Whole-form POST, not `/api/SetLineup`**: the form is atomic and proven (accepted, rejected and no-op responses all seen); SetLineup is one swap per call, non-atomic, and can't fill an empty slot. It stays a fallback only if the form path proves brittle
- **Verify by reload, never by the save response**: a rejected save re-renders the form with the rejected values
- **ESPN is a cross-check, not a scoring input**: it only has Out / Day-To-Day and is UA-gated. Its value is catching Fleaflicker's stale OUT/OFS tags, which score ×0. Revisit an OUT-only override after opening-week data (`open-items.md`)
- **Questionable players keep the ×0.5 expected-value model** (`src/prioritization/injury-adjustments.ts`). Timing is the fix: T-40/T-15 runs see most Q players resolved
- **Alerts**: urgent → Pushover only (priority 1 for a failure or injury disagreement with a tip ≤3 h away, 2 for a missed tip); the rest → a Trello card in the user's To-Do Inbox (things that may not be working), since cards made with the user's own token never notify him. Before filing, it searches the whole board's open cards for the same title (the user moves cards between lists; archiving closes one). On a match it comments the new body, or skips if the card's latest comment (else its desc) already says it. If the board can't be read, it files the card anyway and records `lookupError`. Titles name one issue each, never the trigger, so the match holds across runs. A failure while no upcoming tip is stored (All-Star break, or tip times stopped parsing) may still cost a game, so it pushes at priority 0 (respects quiet hours) once a day; after the fantasy season's last day it's a daily Trello card instead. ntfy can't be reached from Workers (shared egress IPs hit its per-IP quota; 522s). A healthchecks.io ping each tick is the dead-man for "the Worker stopped". Every alert is also logged on the channels' dedupe schedule, delivered or not, and served on `GET /alerts` with `delivered` (every channel tried accepted it) for the watchdog below
- **Failed logins and failed saves back off 30 min** except within 45 min of a tip, to avoid a captcha or lockout
- **No runtime self-healing**: a failure alerts, and a human merges any fix. Code that rewrites itself while writing the user's lineup is the wrong risk on a public repo
- **Saves are a runtime switch** (`PUT /saves`, DO storage, default off), so turning them off needs no deploy
