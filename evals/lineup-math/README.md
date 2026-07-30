# Lineup math — what a player is worth under a 9-slot daily cap

**Evaluated: 2026-07-29.** Prices a trade in **expected wins** on the real '25-26 NBA
calendar, calibrated against our real weekly scores. Durable rules live in the
`team-eval` Skill. Come here for a number and **re-run rather than quote it.**

```
python3 sim.py gp            # expected GP: what predicts it, and what doesn't
python3 sim.py market        # board rank -> FPts/G, and GP persistence
python3 sim.py calibration   # NBA calendar, sim vs reality, PF -> wins and its band
python3 sim.py scenarios     # the consolidation ladder
python3 sim.py breakevens    # N-for-1 break-evens + backfill bracket (~4 min)
python3 sim.py replacement   # replacement level per position, the formula's shape
python3 sim.py nights formula durability positions extras players
python3 -m unittest test_sim
python3 fetch_data.py [pool]                   # re-scrape; `pool` is ~20 min, resumable
```

The CLI knows only these names and **exits non-zero on anything else.** For a live trade,
import it:

```python
import sim
full = sim.basis()                        # whoever is loaded, padded to 38 bodies
base = sim.run(full)
deal = sim.run(sim.swap(full, ["Jalen Suggs", "Coby White"], [sim.star(48, 70, ("C",))]))
sim.wins(deal, base)                      # +wins over 20 matchups
sim.breakeven(full, ["Jalen Suggs", "Coby White"], gp=70, elig=("C",))
sim.player_wins(full, ["Jalen Suggs"])    # Δw + sd; pass a swap() result for an incoming name
```

## Pricing a counterparty

```
python3 fetch_data.py roster 160941      # -> roster-160941-2025-26.json
python3 sim.py --roster roster-160941-2025-26.json players replacement
python3 fetch_data.py roster 161025      # OURS is the same command, same schema.
                                         # Re-run it after any trade EXECUTES.
```

`--roster` serves **8 of the 12 reports** and **exits non-zero on `calibration` `scenarios`
`breakevens` `durability`, naming the 8 it does serve** — those four are built on our own
player names and our real weekly scores, and under another team's file they used to print a
full table that answered nothing. `sim.our_roster(path)` and `sim.basis(path)` are the
import path. Team ids are in `team-info`. A row is `{n, tm, avg, tot, gp, posLabel, elig}` —
`fetch_data.roster_rows` is the schema, and `avg`/`gp` are last season as it happened, which
`our_roster` then projects forward.

⚠️ **Compare two teams only at a common body count.** `R` rises with the count, and value is
`(rate − R) × GP`, so **a roster measured short has a low `R` and every player on it reads too
valuable.** Measured, **forward group** throughout: ours **13.7 live at 28 → 16.1 padded to
38**; Pharaoh's 26 bodies **9.0 live → 12.5 padded** (per group 8.7/9.0/8.1 → 11.9/12.5/11.8
guard/forward/centre). Those 3.5 rate points are **~0.27 wins on every player he owns** — ten
times the gaps the σ column is there to police. `sim.basis()` pads to 38 for exactly this
reason. **13.7 is the *live file*; §*Valuation formula*'s 28 row is a different 28 and reads
14.3.**
**Acquisition prices on our roster; what they give up prices on theirs.**

⚠️ **`FetchRoster?season=` is a snapshot** as of the season's last lineup period: a body added
after it is absent (The Don, 26 against 28 live — take counts from `FetchLeagueRosters`), and
a player who missed the whole season carries no rate on it. `our_roster` fills that from his
last real pool season; a rookie with no pool history at all prices at **zero** unless given a
`PROJECTED_RATE` entry.

## Method, and where to distrust it

Read this first — it is the most load-bearing section here.

- **Basis: the 20 periods that count toward the standings.** Our real 27,229 = the
  standings PF column. Periods 21–23 are the playoff bracket; a 23-period total is **18.5%**
  larger and not comparable. 34 of the 165 NBA nights — 22% of its games — score nothing.
- **Calibration 1.006** (27,382 sim vs 27,229 real). Absolute PF is good to ~1%; the
  deliverable is the *differences*.
- **Lineups are set optimally every night** (exact max-weight matching), so absolute PF is an
  upper bound — and it flatters breadth specifically: 88% of breadth's payoff sits on ~32
  nights and all of it requires noticing them.
- **Availability is a per-team-game draw at GP/82** — blind to rest days tracking a team's own
  schedule density, and **~7% too noisy** (sim weekly CV 20.6% vs real 19.2% with *zero*
  per-game scoring noise), so "variance is third-order" survives by an over-statement.
- **Derive periods from the API, never from arithmetic.** Real periods run 4–7 nights and
  **28–56 games** (CV 16.8%); even buckets erase most of the weekly variance the sim
  exists to explain. `test_sim.py` (**53 tests**) guards that and the rest of what these
  claims rest on: schedule integrity, common random numbers, GP-proportionality, the
  surprise-scratch model, circular absence blocks, the board join and its snapshot, the
  single-schedule basis, both uncertainty intervals, the roster schema, the common body
  count, and that the CLI fails loudly on an unknown report.
- **GP is fitted** (`sim.py gp`) for every player on every roster — see below. Only four
  **rates** are judgment (`PROJECTED_RATE`), and only where there is **no usable sample**:
  two missed seasons, two changed rookie roles. **Never an age haircut on a rate he actually
  posted** — that is an aging term inside a win delta, which `team-eval` forbids; age is
  priced in BASE. Without an entry a 0-GP row takes his last real pool season, unmarked.
- **No in-season waiver streaming**, understating an open roster spot before expansion closes
  the pool. **Opponent distribution is fixed** at last year's and the league is rising
  (`team-projections.md`), so real win totals run below these.
- **One NBA schedule for every synthetic body** (`SIM_TM`, currently LAC; multi-body rows
  spread over LAC/TOR/MEM). A body's added PF spans **189 PF across the 30 schedules —
  mean 1,516, sd 57, ~3.6 rate points end to end** — so mixing teams down a ladder charges
  a schedule handicap and reads it as body count. **Never mix teams.**
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

**Non-factors:** `team-eval` owns the canonical list — don't restate or re-derive it. What
*this* file measures about them: variance from any normal trade is well under **0.1 wins** in
every scenario tested (a code comment, not a report — re-measure before quoting), and bracket
sensitivity is `P(title) = p^k` with `k` = 2 or 3, so ≤0.1 wins never moves a decision.

## PF → wins: 1 win ≈ 600 PF (±14%)

Our weekly scores over the scored periods: **mean 1,361, sd 261.** A matchup is decided
on the **margin** — our score minus each other team's in the *same* period, pooled:
**mean +34, sd 236** → P(win) 0.557, against our actual 12-8.

⚠️ **Never build the margin sd by adding ours and the opponent's in quadrature.** Weekly
scores are correlated **ρ = 0.67** through the shared NBA calendar (All-Star period 31 NBA
games and a 722-PF league average; a full period 56 and 1,558). Independence gives sd 409,
**1.74× too wide**, and **1,030** PF per win — `sim.py calibration` prints that too.

⚠️ **The corroborations are other estimators on one score matrix, not independent methods**
(and the head-to-head figure is a subset of the pooled one). On a consistent 20-period basis
they span **582–644**: pooled margin 597, our 20 head-to-head margins 633, cross-sectional
fit of win% on PF-per-matchup across 12 teams 582, or 644 dropping the one 0-19 team. A
**bootstrap clustered on period** — the 11 margins in a period share our score, so they are
not 212 independent draws — gives mean 595, **[518, 679]** around the 597 point estimate,
i.e. **±14%**. `sim.py calibration` prints the band; **quote the band, not the point.**

| +PF/season | +250 | +500 | +1,000 | +2,000 | +3,000 |
|---|---:|---:|---:|---:|---:|
| +wins/20 | +0.42 | +0.83 | +1.64 | +3.16 | +4.50 |

Convert ΔPF at this operating point; a normal CDF on the sim's own weekly mean distorts the
*ordering*, not just the scale. A single 1-for-1 tops out near **+3 wins** and only against
the best player available; a *programme* of several reaches **~+4** — treat anything pitched
above that as wrong. **Variance is third-order**: weekly CV moves 19.2% → 19.0–19.6% across
every scenario, and 1 point of weekly mean ≈ 7 units of weekly sd, so **never accept less
production to buy steadiness.**

## Consolidation is not the lever

**Outgoing bodies 2..N are refunded at 6 FPts / 40 GP here** — post-auction open FA, the
stingiest defensible grade. The backfill bracket below moves these by ≤3.6 rate points and
flips only the 5-for-1.

⚠️ **Suggs/Coby/Turner/Poeltl/Reid are this study's *filler*, held fixed so body count is the
only variable — not a bucket, not a surplus list, not a recommendation.** On
`bathroom-club.md`'s **pre-execution** medians (991 / +0.410) **three of the five** price as
**Core**, where shipping one is a walk-away trigger; the count moves with the medians, so recut
it. Buckets: `my-team-situation`.

| Move | ΔPF | **+wins/20** |
|---|---:|---:|
| **Three separate 1-for-1s** (Suggs/Coby/Turner → three 42s @68 GP) | +2,569 | **+4.30** |
| Jokić **1**-for-1 (Suggs) | +1,871 | +3.13 |
| **Two separate 1-for-1s** (→ two 42s @68 GP) | +1,790 | **+3.00** |
| Jokić **2**-for-1 (+ Coby White) | +1,536 | +2.57 |
| 1-for-1: Suggs → a 50 @68 GP | +1,265 | +2.12 |
| **Bottom-up:** Maluach + Holmes + Middleton → three 26s @76 GP | +1,134 | **+1.90** |
| Jokić **3**-for-1 (+ Turner) | +1,063 | +1.78 |
| 1-for-1: Suggs → a 45 @68 GP | +1,004 | +1.68 |
| 2-for-1: Suggs + Coby → a 50 | +928 | +1.55 |
| 1-for-1: Suggs → a 40 @78 GP | +923 | +1.55 |
| 3-for-1: Melton + Simons + Ellis (dregs) → a 45 | +911 | +1.53 |
| Jokić **4**-for-1 (+ Poeltl) | +682 | +1.14 |
| 3-for-1: Suggs + Coby + Turner → a 50 | +469 | +0.79 |
| Jokić **5**-for-1 (+ Poeltl + Naz Reid) | −108 | **−0.18** |
| 3-for-1 → a **fragile** 55 @40 GP | −129 | **−0.22** |

200 trials; `swap()` preserves common random numbers, so per-block sds run ±0.002–0.032 wins.
Jokić is at his real shape (**65.2 FPts/G, 65 GP, C-only**) but on the study's schedule, not
Denver's (§Method). 38-man baseline PF **30,664.**

- **Body count is the price.** Same player: +3.13 → +2.57 → +1.78 → +1.14 → **−0.18**
  from 1-for-1 to 5-for-1. Winning "best player in the deal" is not sufficient.
- **Splitting a consolidation into separate 1-for-1s is worth 1.2× at N=2 and 2.4× at
  N=3** — the penalty compounds with body count rather than scaling.
- **Cheapest wins are at the bottom.** Bottom-up **+1.90** *beats* a 1-for-1 for a 45 (+1.68),
  and the numerator counts the **incoming** side, same as the denominator: three real 23–26
  FPts/G bodies price at **592** (O'Neale 176 + Achiuwa 108 + Mamukelashvili 308, `base.py` at
  `D` = 456; `trade-targets.md` Tier 1) against **3,000–5,000** for the 45 — **5–8× cheaper.**
  ⚠️ **Name the side before quoting the multiple:** the *outgoing* trio (Maluach 559 + Holmes
  166 + Middleton 119) is **844**, i.e. only 3.6–5.9×.
- **GP is as important as rate.** A 55 @40 GP acquired 3-for-1 is *negative*; a 40 @78 GP
  bought 1-for-1 (+1.55) beats a 50 bought 3-for-1 (+0.79).

### Price a body by backfill at the moment it must be *fielded*

Not the moment the trade is made. **There is no backfill before the September auction at
all** — the pool is locked and we are 28/28, so "deal before the auction while the backfill
is still a rotation player" is backwards. The body price is **structural** (a 9-slot cap and
light-night breadth); backfill is a modifier worth **+0.10 / +0.20 / +0.25 / +0.32 wins** at
2/3/4/5-for-1 across the bracket below, so it is smallest where you should be trading.

| refund grade | 2-for-1 | 3-for-1 | 4-for-1 | 5-for-1 |
|---|---:|---:|---:|---:|
| 6/40 (post-auction open FA) | 32.2 | 41.0 | 48.8 | 63.3 |
| 10/48 | 31.8 | 39.9 | 47.8 | 62.0 |
| 14/55 (generous) | 31.1 | 38.7 | 45.9 | 59.7 |

6/40 → 14/55 is the honest bracket: a body must be **fielded** at 456 owned, our worst kept
bodies are 13.9–14.7, and everything past the fixed 10 auction/rookie slots comes from
post-auction open FA below 8. **Cap-at-3-for-1 survives every grade** — 1.1/2.3/2.9/3.6 rate
points across it.

⚠️ **The 5-for-1 flips sign at the top of the bracket** — Jokić 5-for-1 is **−0.23 / −0.09 /
+0.09** wins at 6/40 / 10/48 / 14/55. Not a licence: +0.09 is inside the noise, it needs the
most generous defensible refund, and the same BASE on separate 1-for-1s beats it several times
over. "5-for-1 stops being self-harm under a rich refund", not "5-for-1 works".

## Break-evens

Incoming rate needed for an N-for-1 to be PF-neutral. **GP and position are part of the
answer** — read the row matching his shape. Outgoing, in order: Suggs 30.5, Coby White
25.8, Turner 24.7, Poeltl 25.8, Naz Reid 27.4 — the same **filler** as above, listed for its
rates, and **not a send list** (§*Consolidation is not the lever*).

| roster · incoming shape | 2-for-1 | 3-for-1 | 4-for-1 | 5-for-1 |
|---|---:|---:|---:|---:|
| **38** · 68 GP forward | 32.2 | 41.0 | 48.8 | 63.3 |
| **38** · 65 GP centre | 34.6 | 44.0 | 51.5 | **67.4** |
| **38** · 78 GP forward | 30.0 | 37.6 | 44.5 | 57.0 |
| **28** · 68 GP forward | 31.8 | 42.6 | 52.1 | 69.7 |
| **28** · 65 GP centre | 34.6 | 46.2 | 55.5 | 74.5 |
| **28** · 78 GP forward | 29.4 | 38.5 | 47.1 | 62.3 |

Both sides of a break-even regress together, so the *GP basis* barely moves these cells;
the **schedule** moves them more (§Method), so never read a break-even off an undeclared
team. Only the two roster sizes that exist: **28 today, 38 from Sept '26.**

Jokić (65.2, 65 GP, C) reads against the **65 GP centre** row: his 5-for-1 break-even is
**67.4** and he supplies 65.2, which is why that scenario is negative (−0.18). Reading him
against the 68-GP-forward row (63.3) inverts the sign.

**Roster size barely matters, and not monotonically.** 38 → 28 moves the 2-for-1 break-even
the *wrong way* (32.2 → 31.8), then +1.6 / +3.3 / +6.4 at 3/4/5-for-1 — large only where the
deal is unbuyable anyway. Don't lean on it.

Cap at 3-for-1, and only for genuine dregs — Melton 22.7 + Simons 21.4 + Ellis 14.7 break
even at **27.5**.

## Is the incoming rate even purchasable?

`sim.py market` joins the points dynasty board to '25-26 FPts/G (359 players, GP ≥ 30) and
**prints which snapshot it read** — currently `july-2026-dynasty-ranks-points.csv`. This is
the bridge from what a trade **costs** (rank) to what it **pays** (rate); everything above
assumes it and nothing else here measures it.

| board rank | 1-12 | 13-24 | 25-36 | 37-60 | 61-96 | 97-150 | 151-250 | 251-456 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| median FPts/G | 47.8 | 39.0 | 38.1 | 35.7 | 30.7 | 27.5 | 22.8 | 15.7 |

**Only 8 players cleared 45 FPts/G at 30+ GP** last season — **3 cleared 50, one cleared
60.** So the 4-for-1 break-even (48.8) and 5-for-1 (63.3) are not merely expensive, they
are **structurally unavailable at any price.** That, independently of the win table, is the
case for the 3-for-1 cap.

Note the divergence: LeBron ranks 152 at 39.9 FPts/G, Westbrook 336 at 33.0 — the board
discounts age and the format pays rate. **Nothing here measures an age curve, so this file
quotes no aging term and no horizon at which a board is "fair"** (`sim.py gp` shows age does
not even predict GP). `team-eval` owns how age is handled; the gap above is an observation
about the board, not free value.

## Valuation formula

**`(rate − R) × GP ÷ K` = wins per 20 matchups**, for a **1-for-1**. `R` is the
x-intercept of value in rate, a property of the pool rather than of who left, so the
*share* of a player's rate you lose rises as the roster shrinks:

| bodies | 38 = `basis()` | 28 = `thin(basis(), 28)` |
|---|---:|---:|
| replacement R | 16.1 | 14.3 |

⚠️ **Two different 28s.** This row thins the *padded* 38 to its best 28 — 27 of ours plus
`RK0`, with Sion James dropped — so it is **not** the live file's **13.7** (§*Pricing a
counterparty*). Both are forward-elig fits; the roster differs, not the group. `sim.py
replacement` prints the same two rows.

**R is position-dependent, and that is a third of the error** — measured on our roster:

| | guard | forward | centre |
|---|---:|---:|---:|
| R | 18.0 | **16.1** | 17.8 |
| K | 782 | 779 | 781 |

A single R is ~1.9 rate points wrong between groups; guards and centres sit above forwards
because our 12 pure PG/SG glut the guard-eligible slots. **R moves with the GP basis and the
body count alike — re-measure it, never carry one over.**

⚠️ **Not a 1% formula.** Against sim 1-for-1s on our actual roster: **median error +33%,
worst +91%, always over-predicting.** Switching to a per-position R takes that to
**median +22%, worst +65%** — Bane from +62% to +43%. A third of the error is a fixable
constant, not irreducible roster shape. The worst row is **Suggs (+91% / +65%)**: the
formula is least trustworthy on low-rate/low-GP players.

**Per-position R fixes magnitude, and here it also fixes the top-5 order** — `formula+posR`
matches the sim's top 5 where the single-R formula does not. `sim.py formula` derives that
comparison rather than asserting it, because the two can diverge on any refit. Sort with the
formula, decide with `sim.py players`.

⚠️ **`sim.py players` prints the σ to the next row — read the order off it, and state no
order below ~2σ.** It averages **3 independent 200-trial seed blocks** and prints the
per-block sd; the mean's se is `sd/√3`, and hand-computing that is how this table twice
published an order it had not measured. Currently **Kawhi +2.10 ±0.011 (17.1σ) · Cade +1.93
±0.012 (3.2σ) · Amen +1.91 ±0.002 · Giddey +1.49 ±0.015 (6.4σ) · Duren +1.42.** Unordered
pairs do occur — Naz Reid/Garland 1.1σ, Edey/VanVleet 0.8σ.

⚠️ **Monte-Carlo resolution is not decision resolution.** Cade over Amen is 3.2σ and 0.02
wins — ~2% of a win, an order of magnitude inside every other error term here (formula
22–33%, PF→wins ±14%). **A resolvable gap in this block is still not a tradeable one.**

**Value in rate is linear above ~30, not convex.** A marginal added 68-GP forward gains a
flat **52.2 PF per rate point** from 30 up (increments 245/260/261/261/261/261/261/261 — flat
from 35). Its x-intercept is 16.1; that is a *different* fit from `R` (30/40/50/65 vs
30–65 in fives) and the two only coincide by luck — quote the grid you fitted. The genuine
convexity is confined to rate < 30, which is exactly what makes the linear formula unusable down
there — and an apparent elasticity fitted through it is mechanically `rate/(rate−R)`, not a
measured exponent. `rate × GP` is worse: charging nothing for the replacement body is too
harsh on high-rate/low-GP players.

## GP is the dominant input — and one season of it is enough

`sim.py gp`. Five seasons of pool history ('21–'25), 684 players with birthdays, ranked by
**5-fold CV grouped by player**, errors averaged over 8 fold shuffles, then a **2,000-sample
bootstrap clustered on player** for the interval. Population: rate ≥ 20 the prior season —
the players we actually trade.

⚠️ **Judge every gap against its CI**, and the CI has to be resampled over **players** —
the sd across fold shuffles is reproducibility of the split, ~0.01 against a real ~0.15, and
a gap of 0.15 read against it becomes a finding.

| model | RMSE | vs `gp1` | 95% CI (clustered) | P(beats `gp1`) |
|---|---:|---:|---|---:|
| `gp1 + knot(rate)` — **adopted** | 16.80 | −0.03 | [−0.13, +0.07] | 0.73 |
| `gp1 + rate` | 16.83 | −0.00 | [−0.07, +0.07] | 0.51 |
| `gp1` (last season's GP) | 16.83 | — | — | — |
| `gp5` (5-season mean) | 16.98 | +0.15 | [−0.12, +0.43] | 0.14 |
| **pool mean (a flat ~60 GP)** | **17.54** | **+0.71** | **[+0.30, +1.13]** | **0.00** |
| `age` alone | 17.58 | +0.74 | [+0.34, +1.15] | 0.00 |

What survives:

1. **One season beats a flat prior — the only gap this population resolves.** `gp1` −0.71
   against the pool mean, CI [+0.30, +1.13]. The adopted `gp1 + knot(rate)` **straddles zero
   here** (P 0.73) and is adopted for its *shape*, on whole-pool evidence `sim.py gp` prints.
2. **More history is not worse — just not better.** `gp5` +0.15 straddling zero (P 0.14), and
   +0.42 [−0.28, +1.21] even on the 142 rows with 4+ prior seasons. **One season on Occam.**
3. **Age never helps.** Alone it does not beat the flat prior (17.58 vs 17.54) and is
   measurably worse than one season of GP ([+0.34, +1.15]) — survivorship, most likely.
   **No report here measures an age curve; do not quote one, and keep age out of GP.**
4. **The whole exercise is worth ~4% of the error** — 16.80 against 17.54 on an sd of 17.5. GP
   is a *defensible* input, not a precise one: **never argue a trade on a few games of GP.**

**Adopted, and wired in** (`project_gp`, applied by `our_roster` to ours *and* a
counterparty's file):

```
GP = 25.7 + 0.368 × last season's GP + 0.432 × min(last season's FPts/G, 30)
```

The rate term separates a bench body from a starter — expected GP ~40 at rate < 10 against
~63 at rate 30–40. **The knot is not cosmetic.** Empirical mean next-season GP by last
season's rate is concave and *turns down*: 39.6 (<10) / 53.5 / 58.9 / **62.8 (30–40)** / 61.3
(40–45) / **59.6 (45+)**. So an unknotted term keeps paying for rate that buys no games and
ran **+6.6 GP of bias on the rate ≥ 45 rows — exactly the players every headline table here
is built on**; knotting cuts that to +2.9. Directly against the unknotted form on the same
clustered bootstrap: **−0.062 RMSE [−0.122, −0.007], P(knot better) 0.99**, printed by
`sim.py gp` rather than differenced out of two gaps that share a reference. Knots anywhere in
20–35 sit inside each other's noise; **30** is the whole-pool CV optimum and the peak.

⚠️ **Censored.** A player who misses a *whole* season is absent from the pool rather than a
zero, so every figure here is expected GP **given he plays at all** — an over-estimate for
anyone at real risk of missing a year, and it cannot see that risk.

⚠️ **Weakest on a fragment season.** Edey's 11-game '25-26 projects 43 GP, Chaney's 17-game
40, Holmes's 25-game 41: a fragment is the only evidence the model has. Read those rows off
`sim.py gp`, which prints the **pool** GP the projection actually used — the roster file
rounds some seasons a game differently. Flag those rows; don't patch them.

Same finding sideways (`sim.py market`): persistence `b` is 0.45 pool-wide and
**0.17–0.28** among rotation players — everyone converges to **~59–62 GP whatever he did.**

What that dominance looks like — a 48.9-rate forward acquired 1-for-1 for Suggs:

| his GP | 36 | 45 | 55 | 65 |
|---|---:|---:|---:|---:|
| +wins/20 | +0.67 | +1.03 | +1.49 | +1.89 |

**Both sides of a trade are regressed identically by construction** — `our_roster` projects
GP for every player and fills a missed season's rate from the pool, on whichever file is
loaded, so a counterparty's injured star cannot be priced at his worst season while ours ride
forward. Always state the counterfactual: "if he vanished and the slot went empty" and "if we
swapped X for him" differ by the whole value of X. `sim.py players` prints the second.

## Durability: no format-derived injury adjustment

**With foreknowledge of who plays, the format is exactly proportional** — GP-elasticity 1, as
on any `rate × GP` board. Residual **≤1.2% at every rate we trade at** (45 and 60), worst 2.7%
at rate 26 / 55 GP where it does not matter.

**The lock-in is not an exception.** Lineups lock before tip, so an unannounced scratch
forfeits the slot — but you can only be *surprised* on a block's **first night**; after that he
is on the public injury report. `sim.py durability` **measures how absences arrive on the
roster in hand** — at 38 men, **948 nights in 118 blocks of 8.03** — so sampling every absence
night instead multiplies the penalty by that 8.03.

| whole 38-man roster | 10% of blocks | 25% | 40% |
|---|---:|---:|---:|
| onset-corrected | **−0.11 w** | −0.30 w | −0.48 w |

Per player: **≤2% of his value at any plausible input, and flat in GP** (1/1/0% at 41/55/70
GP). The costliest shape is a high-GP veteran resting scattered single games, where every
absence *is* its own onset.

→ **Do not apply a fragility discount.** `team-eval` is authoritative on that, and three
unmodelled things push this figure down further: today's 4 IR slots, waiver streaming, and
setting lineups late. The slate-wide-lock premise is unverified, which can only shrink it.

⚠️ Still **assumed** for GP: that boards price roughly expected games. Nothing here measures a
board's GP haircut — that is a claim about the market; don't launder it as format math.

**Burstiness is EV-neutral for season points** (+0.05%, provably: equal day-level marginals,
independent players, and lineup value depends only on that night's availability set) — **pay
for GP quantity, ignore the pattern.** It does not extend to a short window, the split `LATE`
draws; `team-eval` does not size that, so neither does this file.

**No IR + empty pool after expansion:** a season-long absence also burns a slot. Marginal
38th body 58–73 PF = **0.097–0.121 wins**, an upper bound.

## The slot-fill curve

`PG · SG · G(PG|SG) · SF · PF · F(SF|PF) · C · ANY · ANY`, verified against
`FetchLeagueRules.rosterPositions`. At 38 players, 9 slots do not fill until a 7-game
night:

| games that night | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| nights (of 131 scored) | 2 | 6 | 6 | 8 | 10 | 20 | 14 | 16 | 19 | 30 |
| players available | 1.6 | 3.1 | 4.9 | 7.5 | 8.7 | 10.7 | 12.7 | 14.0 | 15.5 | 17.5+ |
| slots filled /9 | 1.6 | 3.1 | 4.9 | 7.3 | 8.1 | 8.5 | 8.9 | 8.9 | 9.0 | **9.0** |
| cumulative share of lost slots | 13% | 45% | 67% | 79% | 88% | 97% | 98% | 99% | 100% | 100% |

The constraint is concentrated, not broad: **14 nights (11%) carry 67% of the loss, 32 nights
(24%) carry 88%**, and from 7 games up 3.2% remains. **111 unfilled slot-nights of 1,179
(9.4%).**

⚠️ **Deliberately no "season loss = N PF" headline** — that is an assumed price for an empty
slot times a slot count, and no price is defensible: the same slots come to ~1,559 PF at `R`,
928 at a price of 10, 1,857 at 20. **The share columns are price-invariant** — quote those.

- **Heavy night** (15–25 bodies for 9 slots): only *rate* matters, the 10th-best scores
  nothing. **Light night**, ~14 of them: nearly everyone available starts, so a 26-FPts body
  and an 8-FPts body differ by the full 18 — *presence, not rate.* Surplus is therefore **the
  middle**, not the top and not the tail.
- **Positions rarely bind:** 1.9% of slot-nights lost to no legal slot against 7.5% to no body
  at all. Both take `min(9, ·)` of a *bucket mean*, so by Jensen the positional figure is an
  **upper bound** — it runs with the conclusion, so say so.

## Positional premium — a fact about *our* roster, not the format

Added body of identical rate, versus that rate as a guard:

| rate | 25 | 35 | 45 |
|---|---:|---:|---:|
| forward vs guard | **+13%** | +12% | +8% |
| centre vs guard | −1% | +1% | +1% |

At rate 25 that +13% is **~+0.09 wins** — worth pricing on a marginal body, not worth building
around. Guards and centres are indistinguishable, and the premium shrinks as rate rises: a
high-rate player starts on heavy nights regardless of slot.

⚠️ **Purely a function of our current positional distribution** — 12 pure PG/SG chasing at most
5 guard-eligible slots. **Not structural**, and it disappears when the roster's shape changes.
`team-eval` files it as a tiebreak against *that* roster's tightest slot group.

## Sept '26 expansion

`league-info` owns the format facts (28 → 38, the rookie rounds and the auction). What this
file measures about them:

- Filling to 38 with auction-grade bodies: **+1,279 PF (+2.14 wins), free** — more than
  most consolidation trades on this page, and the cheapest wins available.
- **Breadth stops being a differentiator** — everyone gets it in the same auction.
  Hoarding 20-FPts filler now buys nothing durable.
- **A traded-away body cannot be replaced.** 3-for-1 leaves 36 players and 2 dead slots.
- **The 4 IR slots disappear** — a small markdown on fragile stars from Sept '26 that does
  not apply today.
