- [x] Delta w for just PF / in general, vs for this season simmed — see `Eval Definitions §Δw` vs `§Δw (season)`
- [x] Formula Δw cutoff R stays 15, not ~25 — gap vs sim is our fitted REPL (~25) vs league last-rostered, not a wrong constant (`Eval Definitions §Δw`)
- [ ] At some point Update repo (average projections from a few more sites, once those sites have released. e.g. ESPN)

# Lineup runner

- [ ] Sign-ups, saves approval and game-day tasks (10/20 opening-night capture) for the cloud lineup runner: `.claude/skills/lineup-runner/open-items.md`

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
