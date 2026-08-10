# Method, and where to distrust it

Read this before quoting anything in `findings.md`.

- **Basis: the 20 periods that count toward the standings.** Our real 27,229 = the
  standings PF column. Periods 21–23 are post-season on the wire; a 23-period total is
  **18.5%** larger and not comparable. 34 of the 165 NBA nights — 22% of its games — score
  nothing. ⚠️ **That period count is not the bracket's shape** — the real bracket is 4 rounds
  over periods 20–23, and it is R1's *label* Fleaflicker cannot express, so period 20 arrives
  here marked `regular` (`league-info`). Read only "these 20 score, those don't" off this
  line.
- **Calibration 1.052** (28,643 sim vs 27,229 real). ⚠️ **Not a 1% fit, and the
  cause is the roster, not the model:** the numerator is the roster file as it stands and
  27,229 is what the roster *before the last trade* scored — `sim.py calibration` prints that
  caveat under the ratio, because the ratio is read there and nowhere else. Absolute PF is
  good to ~5% here; the deliverable is the *differences*, which common random numbers hold to
  ±0.01–0.05 wins across the scenario ladder.
  **Re-cut the roster and this drifts again** — read it as a sanity bound, never as a scale
  factor to divide by.
- **Lineups are set optimally every night** (exact max-weight matching), so absolute PF is an
  upper bound — and it flatters breadth specifically: nearly all of breadth's payoff sits on
  the ~32 light nights (`findings.md` §*The slot-fill curve* owns the share) and all of it
  requires noticing them.
- **Availability is a per-team-game draw at GP/82** — blind to rest days tracking a team's own
  schedule density, and **~6% too noisy** (sim weekly CV 20.4% vs real 19.2% with *zero*
  per-game scoring noise), so "variance is third-order" survives by an over-statement.
  Absence *blocks* draw a length from `gauss(9, 6)` truncated at 1, so the realised block is
  not 9 — which is why `mean_block` is measured off the same draw rather than quoted.
- **Derive periods from the API, never from arithmetic.** Real periods run 4–7 nights and
  **28–56 games** (CV 16.8%); even buckets erase most of the weekly variance the sim
  exists to explain.
- **`test_sim.py` guards what these claims rest on** — **its docstrings are the specifics;
  this is the outline:**
  - schedule integrity and the single-schedule basis; an NBA abbreviation the schedule
    cannot resolve is **refused** rather than served `SIM_TM`;
  - the nightly lineup being the max-weight one, checked against a second algorithm;
  - common random numbers — both uncertainty intervals and the paired per-block σ;
  - GP-proportionality, the surprise-scratch model, circular absence blocks;
  - the board join and its snapshot;
  - one scoring basis for every PF figure (20 periods, 27,229);
  - the per-slot-group counterfactual behind every `Δw`, in `formula` as well as `players`;
  - the roster schema, duplicate names, a common body count on both sides of the mirror,
    and that a projected rate reaches the win figure without reaching the GP;
  - light-night counts on the **scored** basis, and only the auction's seven bodies
    steerable;
  - the flag vocabulary being `Eval Template.md`'s, and every section these files
    cite existing;
  - the bracket window taken off the period field size rather than the wire's flags, a
    period 20 carrying anything beside R1 refused where it is read, the per-team game counts
    against the NBA schedule, the seed bands against who actually played each round, and
    `ΔP(title)`'s counterfactual and sign — with a one-body joint run agreeing to the digit
    with the per-player row;
  - **the draw**: every game of last season's bracket walked through it in seed terms, the
    half a seed cannot meet before the final being exactly the half it meets in it, the final's
    opponent sitting above the field, and the eight seeds' title probabilities summing to 1;
  - **σ's split**: a named opponent narrower than a drawn one by exactly the field's level
    spread, and the two recombining onto the margins they came from;
  - **the matched basis**: inflating every team's projected rates together moves no band's
    `P(title)`, the field is the top 8 of the projected league, the league is one season's
    roster files rather than two, and no team is inside the opponent level it is measured
    against — including when its file arrives as an argument instead of loaded;
  - the CLI failing loudly on an unknown report, and every `sim.py <report>` a page or a
    skill cites naming a real one;
  - every verdict sentence in `findings.md` §*Light-night coverage*'s report being **derived
    from the numbers printed above it**, and moving when those move;
  - the published constants, so a re-scrape cannot move them silently: `PF_PER_WIN`, the
    fitted `project_gp` coefficients, the slot-fill shares, and how few players clear
    45/50/60 FPts/G.
- **Padding to 38 hands every team the same ten bodies** (`EXPANSION`: 3 rookie grades + 7
  auction grades), **hand-typed and regardless of the picks that team actually holds.**
  Nothing here measures how much that assumption is worth, so a cross-team `R` gap of a
  rate point or two is **not resolved** by these files, and changing a grade re-measures
  every table in `findings.md`.
- **GP is fitted** (`sim.py gp`) for every player on every roster. **Rates are projected**
  (`projections`), never posted and never hand-set, and never haircut on top
  (`Eval Definitions §Δw`).
- **No in-season waiver streaming**, understating an open roster spot before expansion closes
  the pool. **Opponent distribution is fixed** at last year's and the league is rising
  (`../Team Projections.md`), so real win totals run below these.
- **One NBA schedule for every synthetic body** (`SIM_TM`, currently LAC; multi-body rows
  spread over `SIM_TMS`, LAC/TOR/MEM). Which of the 30 schedules a body sits on is worth
  **~4 rate points end to end** — `simlib/schedule.py` owns the measured spread — so mixing
  teams down a ladder charges a schedule handicap and reads it as body count.
  **Never mix teams.** ⚠️ **That binds *comparisons* — every row of one table on one
  schedule — not acquisitions.** Which real NBA schedule a body brings is a live choice, and
  that same spread is what an acquisition tiebreak harvests (`findings.md` §*Light-night
  coverage*). An unsigned player runs on `SIM_TM` too (`README.md` §*Pricing a
  counterparty*). ⚠️ **`SIM_TM` is unresolved:** LAC sits roughly half a schedule-sd below
  the 30-team mean, with DEN nearest its center — so every break-even and scenario row
  carries a mild unfavourable handicap. Re-pointing it re-measures all of them;
  `simlib/schedule.py` carries the flag.
- **Year-specific:** which NBA teams play 10 vs 12 games in a window, playoff-week dates,
  the opponent distribution, the calibration constant, **and the positional premium** —
  that last one is a fact about our roster, not about the format.
- **Data**, all built by `fetch_data.py` and named for the season — `SEASON` there is the one
  constant to bump, and a roll writes new files instead of overwriting last year's.
  `nba-schedule-*`: ESPN scoreboard, 165 nights, **1,231 games**, 7.46/night, postponed
  dropped, NBA Cup final kept as a real 83rd game for NY/SA; '26-27 was unreleased.
  `league-*`: periods from `eligibleSchedulePeriods` plus every team's PF in every period, so
  every win figure is auditable. `players-*`: FPts/G and GP for **'21–'25** plus a
  **birthday** for **684 players**, re-scored under current rules. Which endpoint and field
  is safe to read — and the traps in each — is `get-league-info`'s; check it there before
  changing a fetch.
- **The board is discovered, not named.** `newest_board()` takes the newest
  `<month>-<year>-dynasty-ranks-points.csv` snapshot and raises if there is none, because
  `dizzle-dynasty` re-snapshots under a new month and leaves the old file in place.
- **An unusable projection snapshot stops the run.** Missing, unparseable, or joining to
  nobody, `our_roster` raises naming the file — because "no index" is row-for-row identical
  to "the feed carries nobody": every rate reverts to last season's average, and only
  `players` prints the `noproj` column that would say so. A row the feed genuinely does not
  carry is still just that row (`findings.md` §*GP is the dominant input*).

# The 0.1-win floor

Non-factors are `Eval Definitions §Non-factors`' closed list. What *these* files measure about
them: variance from any normal trade is well under **0.1 wins** in every scenario tested — **no
report publishes that figure, so re-measure before quoting it** — hence **≤0.1 regular-season
wins never moves a decision.**

⚠️ **That floor is denominated in regular-season wins over the 20-matchup basis, and does not
carry into a bracket week.** Every `Δw` here is built on the 20 periods Fleaflicker scores as
regular, so periods 21–23 sit outside all of them — and **period 20 is bracket R1**
(`league-info`), priced here as a regular-season period. Pricing a bracket-week game in these
units and reading it against the floor is a currency error, not a conservative approximation.
`Eval Definitions §ΔP(title)` owns what the bracket currency is and what it may decide;
**`sim.py playoffs` is the only source of the number** and re-runs it per roster.

**The multiplier.** `findings.md` §*Bracket weeks* carries the measured tables, per band and
per roster. **Take the window and the round count from the period data — never hardcode
either here** (`league-info`).

**One basis, both sides.** μ_us and μ_opp are the same measurement of different rosters — all
12 roster files, projected rates, padded to 38, one engine — so the body count, the projections
and the sim's own optimism cancel out of the margin instead of booking as an edge. `test_sim.py`
pins it: inflate every team's rates 10% together and no band's `P(title)` moves more than
**0.008**. ⚠️ **Not exactly zero, and the residual is ours** — `pad`'s ten bodies carry fixed
grades no rate feed reaches, so the team holding the most real bodies (us, 28) rescales hardest.

⚠️ **A level error that hits one roster and not the field does not cancel**, and nothing here
is a paired difference against a fixed opponent: `P(title)`, the multiplier and `ΔP(title)` all
scale with the loaded roster's own level. Read them per roster — the same run over a rebuilding
one prices a bracket game at a twentieth of ours or less (`findings.md` §*Bracket weeks*).

Its error bars, in the order they bite:
- **A band is a seed range, and `P(title)` is the mean over it.** The opponent is the round's
  survivor, enumerated over the whole draw, but which seed inside the band is not resolved —
  and the draw splits them (`findings.md` §*Bracket weeks* carries the spread). A decision that
  turns on that spread needs the seed, not the band.
- **σ is a decomposition, and it closes.** The eight seeds over the 19 regular periods split
  into a within-team weekly CV *w* = **0.1005** and a between-team level CV *b* = **0.0448**;
  a bracket margin names both teams and takes √2·*w*, a regular matchup draws its opponent and
  takes √(2*w*²+*b*²) — with *b* the **whole league's 0.0909**, since the seeds are the top of
  it by construction and a regular opponent is drawn from all 11. Recombined with both level
  terms that reads **0.1556** against the **0.1557** the same margins pool to directly.
  ⚠️ **Both steps that isolate *w* also shrink it** — the period mean is the same 8 teams', and
  each team's deviations are taken from its own measured level — so *w* carries an explicit
  finite-sample correction; without it the split lands 9% short and every σ below with it.
- **σ is fitted, not observed** — from within-period scores of last season's eight seeds
  (`findings.md` §*Bracket weeks*). The 7 title-ladder games actually played give a narrower
  read, printed by the report as a bound and not used as the basis.
- **The field is projected, not known.** Which 8 seed is a season away; the rule is the
  league's own (PF), run forward on this basis. The 8th/9th cut is ~1,500 PF wide, so it is not
  on a knife edge — but the **7th/8th is ~70 PF, 0.3% of a season**, and two teams swapping
  there re-point a whole slot of the draw.
- **Three sigmas of the same name are not the same quantity.** Pooling periods 21–23 without
  excluding the consolation half inflates σ by mixing two brackets scoring in one period.
- **One season of margins**, like every other figure here — and nothing re-measures the CV.
- **Monte Carlo — the smallest bar here, and the only one the report prints.** `P(title)`,
  `by seed` and the multiplier are single **unpaired** draws: `ΔP(title)` differences two runs
  across the seed blocks they share and the draw cancels out of it, while these difference
  against nothing, so one whole sim of 12 rosters rides in each. `sim.py playoffs` carries the
  sd across re-draws of the entire basis beside every one (`findings.md` §*Bracket weeks*).
  ⚠️ **Both sides re-draw together** — our weeks re-seeded against a pinned field measure a
  mismatch on top of the sampling noise and read wider than the truth.
