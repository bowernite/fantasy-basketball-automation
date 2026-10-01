# Priorities

Rough triage as of 9/30. P1 = before opening night (10/20), P2 = opening week through midseason, P3 = later or only if needed. Effort is rough agent working time; "user" means it needs the user. Detail is in the entries below.

| Pri | Item | Effort | When / gate |
| --- | --- | --- | --- |
| P1 | Confirm the GitHub watchdog's scheduled runs fire | ~10 min | Now: the safety net is unproven |
| P1 | healthchecks.io dead-man sign-up | ~15 min (user) | Now: the dead-man check isn't set up yet |
| P1 | See a T-40/T-15 tip run fire live (fake tip via debug route) | ~1–2 h | Before 10/20 |
| P1 | Day-1 lineup is now the runner's: glance at it | ~5 min (user) | Before 10/20 |
| P1 | 10/20 opening night: capture in-game page + API roster, add fixtures | ~2–3 h | 10/20 after the 2:00p CT tip |
| P2 | Respect manual lineup changes (hourly runs overwrite hand-edits) | Decide ~15 min (user); build ~1 day | Before the user relies on manual edits |
| P2 | Smaller runner backlog (NaN score fails the whole day first) | ~0.5 day | Opening week |
| P2 | Game-day digest | ~2–3 h | Opening week |
| P2 | Untagged OUT news: firmer status source | ~0.5 day (ESPN corroboration) to ~2 days (LLM) | After opening week's shadow `wouldBench` data |
| P2 | Late scratches after T-15 | ~1 day | After opening week's injury-lag numbers |
| P2 | Worker ntfy fallback: document it in the skill | ~15 min | Any time |
| P2 | Board-residual test red on main | ~1 h | Any time |
| P2 | Preseason freeze (projections) | ~1–2 h | Once all 12 rosters are re-cut |
| P2 | Stale-projection alerts (needs generator change) | ~0.5 day | Early season |
| P2 | Average projections from more sites (e.g. ESPN) | ~0.5 day | Once those sites publish |
| P3 | AI sanity check (LLM reviewer) | ~1–2 days + API key (user) | Only if opening week shows misses the deterministic checks don't catch |
| P3 | Aging role vets overvalued (progression model) | ~1 day | Before trusting year 2+ bands |
| P3 | Top-5 picks over-projected | ~1 day | When enough post-2016 classes exist |
| P3 | Team sim leftovers (retire `horizon.py`, calibrate) | ~1–2 days | After the model fixes above |
| P3 | Draft-class nudge re-read | ~1 h each | Jan–Mar; freeze each October |
| P3 | Each offseason: refit + backtest | ~0.5 day | After the season |
| P3 | 2027 season finale rollover check | ~1 h | April 2027 |
| P3 | Rookie P(active) swings; G1/G2 gate redesign | ~0.5–1 day | Low value |
| P3 | Years 8–20 extrapolated; "if it ever feeds valuations" | — | Don't invest unless triggered |

# General

- [x] Delta w for just PF / in general, vs for this season simmed — see `Eval Definitions §Δw` vs `§Δw (season)`
- [x] Formula Δw cutoff R stays 15, not ~25 — gap vs sim is our fitted REPL (~25) vs league last-rostered, not a wrong constant (`Eval Definitions §Δw`)
- [ ] At some point Update repo (average projections from a few more sites, once those sites have released. e.g. ESPN)

# Lineup runner

- [ ] Sign-up (healthchecks.io dead-man) and game-day tasks for the cloud lineup runner: `.claude/skills/lineup-runner/open-items.md`
- [ ] **10/20 opening night: capture the in-game page + API roster** from `GET /captures` after the 2:00p CT tip and turn them into fixtures. The locked-row markup is a guess, and if the page vs API cross-check disagrees once starters lock, every later run that day fails (no late-scratch coverage for the 6p/8:30p games). Steps: `open-items.md` §Game-day tasks
  - Before then: no T-40/T-15 tip run has fired live yet (preseason has no tip targets); watch the first ones on 10/20 in `/runs`
- [ ] **Day-1 lineup is now the runner's**: the 9/30 save test and first automatic save replaced the hand-set day-1 lineup with the optimizer's. Glance at it before 10/20
- [ ] **Confirm the GitHub watchdog's scheduled runs fire**: as of 10/1 00:30Z only manual (`workflow_dispatch`) runs exist. Check `gh run list --workflow lineup-watchdog.yml` for `schedule` runs (`operations.md` §Watchdog)
- [ ] **Worker ntfy fallback is untested live**: it only sends when Pushover rejects, which can't be forced without hitting the phone; ntfy reaches it from Cloudflare only ~3/4 of the time. The skill still says ntfy can't be reached from Workers (`how-it-works.md` §Alerts): document the fallback there
- [ ] **Late scratches after T-15**: the last scheduled run is T-15 (T-10/T-5 only retry failures), so a scratch announced in the last ~15 min is missed. Option: poll an injury feed inside ~90 min of tip and trigger a run when a starter's status changes. Decide after opening week's injury-lag numbers (`open-items.md` §Game-day tasks)
- [ ] **Game-day digest**: one push at each day's first T-40 listing starters, benched players with a game, and changes, so a wrong lineup is visible without opening Fleaflicker (`open-items.md` §Backlog)
- [ ] **Stale-projection alerts**: rostered players missing from the bundled `src/data/player-data.ts` (e.g. Okpara) get a 6.0 fallback (a run warning only), and nothing warns when the feed is old. Needs a generator change first (`projections` Skill; `open-items.md` §Backlog)
- [ ] Smaller runner backlog (a NaN score fails the whole day, `.alert-warning` banners, duplicate alerts, `tsc` skips `src/worker/`): `open-items.md` §Backlog
- [ ] **2027 season finale**: check what the API returns at rollover; an empty `eligibleLineupPeriods` makes every tick throw (`open-items.md` §Game-day tasks)
- [ ] Respect manual lineup changes (hourly runs overwrite hand-edits); see `.claude/skills/lineup-runner/open-items.md` §Manual edits vs hourly runs
- [ ] **AI sanity check (tabled 9/30)**: today every Worker check is deterministic. An LLM reviewer would catch soft problems: odd banners, news contradicting a tag (stale out-for-season tags), a starter who looks wrong given news, untagged OUT news (now only measured as `untaggedOutNews`)
  - Shape: reviewer only, never in the save path. Runs after save + reload verify, on T-40/T-15 tip runs and runs that saved changes (~5–10 calls/day in season), not hourly no-ops or 5-min ticks
  - Input: trimmed text of the post-save lineup page, the decision (scores, slots, changes, warnings), ESPN injury rows, `untaggedOutNews`. Text, not screenshots
  - Output: Claude API structured `{level: ok|warn|urgent, issues[]}`. `urgent` → Pushover (≤3 h to tip, same rule as failures); `warn` → Trello via the existing dedupe; LLM error/timeout → Trello, run still ok. Optional: server-side web search for Q/GTD starters on T-15 runs
  - Cost (estimate): ~10–20k input tokens/call → Sonnet-class ~$10–20/mo, Haiku-class ~$3–6/mo
  - Needs: an Anthropic API key as a Worker secret, plus a monthly spend cap
  - Before building: read opening week's `/runs` (`injuries`, `untaggedOutNews`). If ESPN cross-check + an untagged-news alert cover the misses, this may not be needed
- [ ] **Untagged OUT news: firmer status source** (pairs with the AI sanity check above). v1 benches a player Fleaflicker hasn't tagged only on strict news wording ("ruled out", "won't play", "out for <game>") that names the game day and is newer than his last game. It's lower-only, `doubtful` only alerts, and it runs shadow-only for opening week (records who it would bench). Details: `lineup-runner` Skill
  - Why it's not fully trusted: `parsePlayerNews` takes the first status keyword anywhere in the news and never checks which game. Probes read "closed out the win", "moved out of the starting lineup but played 28 minutes" and "out of his walking boot" as OUT, and "ruled out of Monday's game" (posted Mon) would still bench him Tue
  - Options: corroborate with a second source before benching (ESPN injuries already fetched per run; NBA official injury report PDF is finer-grained, with Q/Available); or have an LLM read the news + game date and return `{status, forGame, confidence}`, acting only on high-confidence OUT for day N; or both (LLM as tiebreaker when the sources disagree)
  - Before deciding: read opening week's shadow `wouldBench` rows and `injuries` rows in `/runs`. Count true and false benches and how often Fleaflicker tags lag the news. Turn on deterministic benching if it's clean; otherwise add the second source or LLM

# Future-year projections

Per-player progression model: `strategy/lineup-math/simlib/progression.py` (sampler), `fit_progression.py` (fit + backtest, how-to in its docstring), `sim.py progression` (report). Gates G1–G6 are defined in `simlib/progression_eval.py`; latest results in `data/progression-backtest.txt`. Today it's a review-only read for years 2–7; its limits print in the report preamble (`LIMITS`).

- [ ] **Preseason freeze** — pending until all 12 rosters are re-cut after the last preseason move (`projections` Skill). Then measure year-1 error and σ_u off it (σ_u .12 is a prior until then). First real check of year 1; do it before trusting any year-2 band
- [ ] **Aging role vets overvalued** — age 29+ at 20–27 FP/G, 7-yr value pred/real 1.15–1.28 across cutoffs; 27–34 FP/G 1.07–1.19 (1.32 at 2020, CI .85–2.24). G3 fails every cutoff. Opinion: probably the post-2016 era churning role vets faster; try an era term in drift like exit's, else a flat haircut calibrated on G3. Re-read after each refit
- [ ] **Top-5 picks over-projected** — 56–66% land below the model's median (G5). Pre-cutoff fits find ~0 shrink; the miss is a post-cutoff shift compounding over 2–4 steps, and recency/era variants didn't close it. Opinion: `top5` flag + judgment for now; refit growth on post-2016 classes once there are enough
- [ ] **Rookie P(active) swings** ±.04–.07 at career years 3–5 (G5); sophomore spread multiplier sits at its grid top (3.5). Opinion: young players' spread is structurally too narrow; low priority
- [ ] **G1 fails, G2 by a hair** — G1: fringe (<20 FP/G) exits after 2015 at the old cutoffs; at 2020 a perfect model misses 21/38 cells, so the gate can't discriminate. Opinion: redesign to fewer, larger buckets rather than chase it. G2 (rule set 9/29: yr-2 CI < 0, yr 3 ≥ 5%): yr 3 is −4.7% / −4.4% at 2009 / 2013; accepted as noise
- [ ] **Board-residual test red on main** — `test_among_the_best_producers_the_residual_does_not_track_age` reads live boards; corr .20 vs < .15 after the 9/29 Hashtag refresh (passes on the older boards). Opinion: pin it to fixture boards, and check whether the residual's age terms hold up across refreshes
- [ ] **Years 8–20 extrapolated** — anchored to history only at ages 38–40; WRV's 8–20 split is a sensitivity. Opinion: fine under the 5%/yr taper; don't invest
- [ ] **Team sim leftovers** — `sim.py future` is built and feeds `strategy/Team Projections.md`'s '27-28+ table (uncalibrated; biases listed in its Notes). Left: retire `horizon.py` (its '26-27 PF block still feeds the '26-27 table) and calibrate the probabilities it rests on (the items above)
- [ ] **If it ever feeds valuations** — revisit "BASE owns everything multi-year" (`Eval Definitions`, `Delta w.md`, `Delta w (season).md`, `findings.md`)
- [ ] **Each offseason** — refit after the BBRef mirror's end-of-season push, re-run the backtest, re-read G3/G5
- [ ] **Draft-class nudge** (`eval-pick` future-picks step 5) — re-read the 2027 top label Jan–Mar. Each October, also freeze the market's class read (crowd pick rows, Dynatyze dial + stamp); after 2–3 classes, test whether it beats neutral
