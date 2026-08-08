# Findings — what a player is worth under a 9-slot daily cap

**Measured 2026-08-03**, on our 28 live bodies padded to 38, calibrated against our real
weekly scores. `method.md` owns the basis and the caveats every table below inherits;
`README.md` owns the commands. **Re-run rather than quote.**

# PF → wins: 1 win ≈ 600 PF (±14%)

Our weekly scores over the scored periods: **mean 1,361, sd 261.** A matchup is decided
on the **margin** — our score minus each other team's in the *same* period, pooled:
**mean +34, sd 236** → P(win) 0.557, against our actual 12-8.

⚠️ **Never build the margin sd by adding ours and the opponent's in quadrature.** Weekly
scores are correlated **ρ = 0.64** through the shared NBA calendar (All-Star period 31 NBA
games and a 722-PF league average; a full period 56 and 1,558). Independence gives sd 395,
**1.67× too wide**, and **993** PF per win — `sim.py calibration` prints that too.
⚠️ Both sides of that comparison sit on **the 20 scored periods**, like every other PF figure
here. Pooling the opponents over all 23 while our own sd runs over the 20 compares two
different seasons and publishes it as a fact about independence — **check the basis on any ρ,
ratio or PF-per-win carried in from elsewhere.**

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
*ordering*, not just the scale. A single 1-for-1 tops out near **+3.1 wins** and only against
the best player available; a *programme* of three reaches **+3.2** — treat anything pitched
above that as wrong. **Variance is third-order**: weekly CV moves 19.2% → 19.1–19.5% across
every scenario, and 1 point of weekly mean ≈ 7 units of weekly sd.

# Consolidation is not the lever

**Outgoing bodies 2..N are refunded at 6 FPts / 40 GP here** — post-auction open FA, the
stingiest defensible grade. The backfill bracket (§*Break-evens*) moves these by ≤4.3 rate
points and flips no sign.

⚠️ **Suggs/Coby/Turner/Poeltl/Reid are this study's *filler*, held fixed so body count is the
only variable — not a bucket, not a surplus list, not a recommendation.** Two of the five
price as **Core** against `../teams/my-team/My Team.md`'s own medians, where shipping one is a
walk-away trigger — the count moves with those medians, so read them there. Buckets:
`my-team-situation`.

| Move | ΔPF | **+wins/20** |
|---|---:|---:|
| **Three separate 1-for-1s** (Suggs/Coby/Turner → three 42s @68 GP) | +1,927 | **+3.23** |
| Jokić **1**-for-1 (Suggs) | +1,857 | +3.11 |
| **Two separate 1-for-1s** (→ two 42s @68 GP) | +1,499 | **+2.51** |
| 1-for-1: Suggs → a 50 @68 GP | +1,311 | +2.20 |
| Jokić **2**-for-1 (+ Coby White) | +1,213 | +2.03 |
| 1-for-1: Suggs → a 45 @68 GP | +1,050 | +1.76 |
| **Bottom-up:** Matković + Holmes + Middleton → three 26s @76 GP | +973 | **+1.63** |
| 1-for-1: Suggs → a 40 @78 GP | +971 | +1.63 |
| 3-for-1: Melton + Simons + Ellis (dregs) → a 45 | +749 | +1.25 |
| 2-for-1: Suggs + Coby → a 50 | +650 | +1.09 |
| Jokić **3**-for-1 (+ Turner) | +436 | +0.73 |
| Jokić **4**-for-1 (+ Poeltl) | +63 | **+0.10** |
| 3-for-1: Suggs + Coby + Turner → a 50 | −71 | **−0.12** |
| 3-for-1 → a **fragile** 55 @40 GP | −678 | **−1.14** |
| Jokić **5**-for-1 (+ Poeltl + Naz Reid) | −691 | **−1.16** |

200 trials; `swap()` preserves common random numbers, so per-block sds run ±0.007–0.054 wins.
Jokić is at his real shape (**65.2 FPts/G, 65 GP, C-only**) but on the study's schedule, not
Denver's (`method.md`). 38-man baseline PF **30,236.** ⚠️ **Two adjacent pairs are unordered
on paired per-block differences** and the table's sort does not mean otherwise: bottom-up
against the 40 @78 GP 1-for-1 (**0.4σ**), and the fragile 55 against the 5-for-1 (**0.5σ**).
Every other adjacent pair clears 2σ.

- **Body count is the price.** Same player: +3.11 → +2.03 → +0.73 → +0.10 → **−1.16**
  from 1-for-1 to 5-for-1.
- **Splitting a consolidation into separate 1-for-1s is worth 1.2× at N=2 and more than 4× at
  N=3** — the penalty compounds with body count rather than scaling.
- **Cheapest wins are at the bottom.** Bottom-up **+1.63** roughly *matches* a 1-for-1 for a
  45 (+1.76) at a small fraction of the price,
  and the numerator counts the **incoming** side, same as the denominator: three real 23–26
  FPts/G bodies price at **592** (O'Neale 176 + Achiuwa 108 + Mamukelashvili 308,
  `eval-player`'s `base.py` at `D` = 456) against **3,000–5,000** for the 45 — **5–8×
  cheaper.** ⚠️ **Name the side before quoting the multiple**, and re-cut the BASE figures:
  they were taken before the 2026-07-31 trade. The outgoing trio here (Matković + Holmes +
  Middleton) is a *study* of what bottom-up buys, not a live shape — the whole remaining
  sub-replacement group tops out around **500 BASE for any three**, so the multiple is
  *larger* and the deal *harder to make*: less to give, same to get.
- **GP is as important as rate.** A 55 @40 GP acquired 3-for-1 is *negative* (−1.14); a 40 @78
  GP bought 1-for-1 (+1.63) beats a 50 bought 3-for-1, which is itself negative (−0.12).
- ⚠️ **The 5-for-1 is a clear loss even with the best player in the league coming back**, at
  **−1.16**, while the same BASE spent on separate 1-for-1s buys **+3.23**. The **4**-for-1 is
  the row to read carefully instead: **+0.10**, the best player in the league bought for four
  bodies, at the ~0.1-win floor (`method.md`).

## Price a body by backfill at the moment it must be *fielded*

Not the moment the trade is made. **There is no backfill before the September auction at
all** — the pool is locked and we are 28/28, so "deal before the auction while the backfill
is still a rotation player" is backwards. The body price is **structural** (a 9-slot cap and
light-night breadth); backfill is a modifier worth **1.4 / 2.5 / 3.2 / 4.3 rate points** at
2/3/4/5-for-1 across the refund bracket (§*Break-evens*), so it is smallest where you should
be trading.

# Break-evens

Incoming rate needed for an N-for-1 to be PF-neutral. **GP and position are part of the
answer** — read the row matching his shape. Outgoing, in order: Suggs 28.9, Coby White
33.4, Turner 31.5, Poeltl 28.1, Naz Reid 26.8 — the same **filler** as above, listed for its
rates, and **not a send list**.

| roster · incoming shape | 2-for-1 | 3-for-1 | 4-for-1 | 5-for-1 |
|---|---:|---:|---:|---:|
| **38** · 68 GP forward | 37.6 | 51.4 | 59.6 | 73.3 |
| **38** · 65 GP centre | 41.0 | 56.4 | **64.0** | 79.0 |
| **38** · 78 GP forward | 35.0 | 46.9 | 54.0 | 65.3 |
| **28** · 68 GP forward | 37.6 | 53.4 | 63.0 | 79.3 |
| **28** · 65 GP centre | 41.8 | 59.4 | 68.2 | 86.2 |
| **28** · 78 GP forward | 34.4 | 48.2 | 56.6 | 70.2 |

Both sides of a break-even regress together, so the *GP basis* barely moves these cells;
the **schedule** moves them more (`method.md`), so never read a break-even off an undeclared
team. Only the two roster sizes that exist: **28 today, 38 from Sept '26.**

**Roster size barely matters at 2-for-1 and then compounds.** 38 → 28 leaves the 2-for-1
break-even flat (37.6 → 37.6), then +2.0 / +3.4 / +6.0 at 3/4/5-for-1 — large only where the
deal is unbuyable anyway. Don't lean on it.

**Which row you pick decides the sign.** Jokić (65.2, 65 GP, C) reads against the **65 GP
centre** row: at 4-for-1, **64.0** against his 65.2 is the +0.10 the ladder prints, while the
68-GP-forward row (59.6) makes the same deal look like a win by 5.6 rate points. At 5-for-1 he
is short on either row (79.0, or 65.3 as a 78-GP forward), and the generous refund below still
asks 69.0.

Cap at 3-for-1, and only for genuine dregs — Melton 12.9 + Simons 29.2 + Ellis 18.2 break
even at **30.6**.

## The refund bracket

How much the grade of the backfill body moves those cells. The top row is the 6/40 refund the
tables above and the ladder both run on — i.e. the **38 · 68 GP forward** row, repeated here
as the bracket's base:

| refund grade | 2-for-1 | 3-for-1 | 4-for-1 | 5-for-1 |
|---|---:|---:|---:|---:|
| 6/40 (post-auction open FA) | 37.6 | 51.4 | 59.6 | 73.3 |
| 10/48 | 37.2 | 50.7 | 58.6 | 71.7 |
| 14/55 (generous) | 36.2 | 48.9 | 56.4 | 69.0 |

6/40 → 14/55 is the honest bracket: a body must be **fielded** at 456 owned, our worst kept
bodies are 13.9–14.7, and everything past the fixed 10 auction/rookie slots comes from
post-auction open FA below 8. **Cap-at-3-for-1 survives every grade** — 1.4/2.5/3.2/4.3 rate
points across it, and no cell changes a sign.

# Is the incoming rate even purchasable?

`sim.py market` joins the points dynasty board to '25-26 FPts/G (359 players, GP ≥ 30) and
**prints which snapshot it read** — currently `july-2026-dynasty-ranks-points.csv`. This is
the bridge from what a trade **costs** (rank) to what it **pays** (rate); everything above
assumes it and nothing else here measures it.

| board rank | 1-12 | 13-24 | 25-36 | 37-60 | 61-96 | 97-150 | 151-250 | 251-456 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| median FPts/G | 47.8 | 39.0 | 38.1 | 35.7 | 30.7 | 27.5 | 22.8 | 15.7 |

**Only 8 players cleared 45 FPts/G at 30+ GP** last season — **3 cleared 50, one cleared
60.** So the 4-for-1 break-even (59.6) and 5-for-1 (73.3) are not merely expensive, they
are **structurally unavailable at any price**, and even the 3-for-1's **51.4** asks for one of
the three who cleared 50. That, independently of the win table, is the case for the 3-for-1
cap — **and it is why the cap is *dregs only***: the same 3-for-1 out of Melton/Simons/Ellis
breaks even at **30.6**, a rate the 61–96 band supplies, while one out of the filler five is
not purchasable at any price. The report prints the **deepest** board rank
that has ever supplied each rate alongside the best — how far down you might have to look,
which is the bound that matters.

Note the divergence: LeBron ranks 152 at 39.9 FPts/G, Westbrook 336 at 33.0 — the board
discounts age and the format pays rate. **Nothing here measures an age curve, so these files
quote no aging term and no horizon at which a board is "fair"** (`sim.py gp` shows age does
not even predict GP). The gap is an observation about the board, not free value.

# Valuation formula

**`(rate − R) × GP ÷ K` = wins per 20 matchups**, for a **1-for-1**. `R` is the
x-intercept of value in rate, a property of the pool rather than of who left, so the
*share* of a player's rate you lose rises as the roster shrinks:

| bodies | 38 = `basis()` | 28 = `thin(basis(), 28)` |
|---|---:|---:|
| replacement R | **17.1** | **15.1** |

⚠️ **Two different 28s.** This row thins the *padded* 38 to its best 28 — our 28 real bodies
minus the weakest, plus the strongest `sim.EXPANSION` slot — so it is **not** the live file's
**14.6** (`README.md` §*Pricing a counterparty*). Both are forward-elig fits; the roster
differs, not the group. `sim.py replacement` prints the same two rows, and `thin()` ranks on
the roster's **own fitted `R`**.

**R is position-dependent, and that is a third of the error** — measured on our roster
(padded 38):

| | guard | forward | centre |
|---|---:|---:|---:|
| R | 18.8 | **17.1** | 19.9 |
| K | 781 | 779 | 780 |

**Centre carries the highest `R` here.** Crowding on the **padded 38 those fits are measured
on** — bodies pure to a group over slots it can fill — is centre 9/3, guard 15/5, forward 9/5:
centre and guard are **equally crowded at 3.0 bodies per slot** and centre `R` is still 1.1
points higher, so ⚠️ **crowding does not order the three, and "crowding lifts a group's `R`"
is not an explanation this table supports.** Read the `R` column itself. (Counted on the live
28 it is centre 6/3, guard 11/5 — a different roster from the one `R` was fitted on, so never
read a crowding count off it against this table.)

A single R is **2.9 rate points** wrong end to end (guard +1.7, centre +2.9 against
forwards), and **the highest-R group is whichever the table says** — here it is centre, not
guards, so a fixed "our guard glut lifts guard R" reading is now backwards.

⚠️ **That gap is not a formula footnote — it is the counterfactual.** `sim.py players`
prices every player against a replacement body **of his own slot group**; against one
forward for everybody a centre reads **0.06–0.09 wins** too high (Poeltl 22% high) and a
guard **0.08–0.15** (Garland the widest), while a forward row does not move at all. A
`Δw` and its counterfactual are one statement (`Eval Definitions §Δw`).

⚠️ **Not a 1% formula.** Against sim 1-for-1s on our actual roster, each priced against a
replacement body **of his own slot group** — the counterfactual `players` publishes, so both
reports grade the same swap: **median error +51%, worst +178%, always over-predicting.**
Switching to a per-position R takes that to **median +38%, worst +138%** — Bane from +84% to
+63%. A third of the error is a fixable constant, not irreducible roster shape. The worst row
is **Suggs (+178% / +138%)**: the formula is least trustworthy on low-rate/low-GP players.

⚠️ **Both error figures are against a sim column that swaps in a body of the player's own
slot group.** An error figure carried in from anywhere else is on a different
counterfactual — guard and centre rows move most, forward rows not at all — so **re-cut it
off `sim.py formula`, never reconcile it.**

⚠️ **The error is an offset, not a scale — so no multiplier converts formula to sim, and
these files publish no fitted conversion.** What holds across re-fits is the *direction*: the
sim is always the smaller number, the ratio drifts with the row (widest at the bottom of a
roster, tightest on a star), and a negative intercept is why the sim turns negative several
rows earlier. **Quote the direction, never a multiple.**

**Per-position R fixes magnitude; it does not currently fix the top-5 order** — on this
roster `formula+posR` reorders the single-R top 5 and still differs from the sim's (sim:
Amen, Kawhi, Giddey, Cade, Butler; posR: Amen, Kawhi, Cade, Giddey, Butler). `sim.py formula`
derives that comparison rather than asserting it, because the two diverge on any refit. The
formula is a diagnostic on the sim, not a valuation layer — decide with `sim.py players`
(`Eval Definitions §Δw`).

**`sim.py players` prints the σ to the next row** (`Eval Definitions §σ` for how to read it).
It averages **3 independent 200-trial seed blocks**, and σ is computed from the **paired
per-block differences**, because every row is measured on the *same* blocks: two rows move
together, so combining their sds as if independent measured something else and was up to 3×
out in both directions. Currently **Amen +2.02 ±0.001 (88.2σ) · Kawhi +1.62 ±0.009 (35.0σ) ·
Giddey +1.36 ±0.009 (3.1σ) · Cade +1.34 ±0.002 (44.4σ) · Butler +1.02 ±0.013 (4.8σ)** — the ±
is the sd across blocks, the σ the paired gap to the row below. Unordered pairs do occur —
Mark Williams/Suggs 0.1σ, Jay Huff/Bona 0.2σ, Kyrie/Jarace Walker 0.4σ, Naz Reid/Garland 0.5σ,
Poeltl/Kyrie 1.0σ, Melton/Holmes 1.1σ, Bona/Chaney Johnson 1.9σ.

⚠️ **3 blocks is 2 degrees of freedom, so σ itself is coarse** — a pair whose blocks happen
to move in lockstep prints a σ in the hundreds.

⚠️ **Monte-Carlo resolution is not decision resolution.** Amen over Kawhi is huge in σ and
0.40 wins; Giddey over Cade clears 2σ at 3.1σ and is 0.02 wins. Every gap here sits inside the
other error terms (formula's own median 38–51%, PF→wins ±14%).

**Value in rate is linear above ~30, not convex.** A marginal added 68-GP forward gains a
flat **52.2 PF per rate point** from 30 up (increments 258/261/261/261/261/261/261 — flat
from 40). Its x-intercept is 17.1; that is a *different* fit from `R` (30/40/50/65 vs
30–65 in fives) and they coincide here **by luck, not by construction** — quote the grid you
fitted, because the next re-measure will separate them again. The genuine
convexity is confined to rate < 30, which is exactly what makes the linear formula unusable
down there — and an apparent elasticity fitted through it is mechanically `rate/(rate−R)`, not
a measured exponent. `rate × GP` is worse: charging nothing for the replacement body is too
harsh on high-rate/low-GP players.

# GP is the dominant input — and one season of it is enough

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

⚠️ **Over-shrunk.** Predictions run **sd 9.8 against a true 20.5** — nothing below 30 GP or
above 70, on a population whose real seasons run 2 to 82. The level is right (bias +1.1) and
the ordering is not (Spearman 0.35), so the error is concentrated in the tails: an iron-man
reads too low and a genuinely fragile starter too high.

⚠️ **External GP feeds do not fix it.** Backtested out of sample against '25-26 actuals,
they tie or lose overall and **lose clearly on rate ≥ 25** — the rows every table here is
built on — carrying **+5 to +15 games of optimism** and an sd that collapses to ~9 against a
true 18.8. A 50/50 blend does win, by **0.88 MAE [0.30, 1.47]** — below this section's own
"never argue a trade on a few games" threshold, and not worth a second data dependency.

⚠️ **The `rate` is projected, the `GP` is fitted, and the flags are about the GP.** A rate
posted over 15 games is replaced by the projection, but that same 15-game season is still
the GP fit's main input (`README.md` §Flags).

⚠️ **Weakest on a fragment season.** Edey's 11-game '25-26 projects 43 GP, Chaney's 17-game
41, Holmes's 25-game 38: a fragment is the only evidence the model has. Read those rows off
`sim.py gp`, which prints the **pool** GP the projection actually used — the roster file
rounds some seasons a game differently. Flag those rows; don't patch them.

Same finding sideways (`sim.py market`): persistence `b` is 0.45 pool-wide and
**0.17–0.28** among rotation players — everyone converges to **~59–62 GP whatever he did.**

What that dominance looks like — a 48.9-rate forward acquired 1-for-1 for Suggs:

| his GP | 36 | 45 | 55 | 65 |
|---|---:|---:|---:|---:|
| +wins/20 | +0.77 | +1.13 | +1.57 | +1.97 |

**Both sides of a trade are regressed identically by construction** — `our_roster` projects
GP for every player and fills a missed season's rate from the pool, on whichever file is
loaded, so a counterparty's injured star cannot be priced at his worst season while ours ride
forward.

# Durability: no format-derived injury adjustment

`Eval Definitions §Durability` owns the rules. What this file measures:

**With foreknowledge of who plays, the format is exactly proportional** — GP-elasticity 1, as
on any `rate × GP` board. Residual **≤0.8% at every rate we trade at** (45 and 60), worst 2.7%
at rate 26 / 70 GP where it does not matter.

**The lock-in is not an exception.** Lineups lock before tip, so an unannounced scratch
forfeits the slot — but you can only be *surprised* on a block's **first night**; after that he
is on the public injury report. `sim.py durability` **measures how absences arrive on the
roster in hand** — at 38 men, **930 nights in 117 blocks of 7.94** — so sampling every absence
night instead multiplies the penalty by that 7.94.

| whole 38-man roster | 10% of blocks | 25% | 40% |
|---|---:|---:|---:|
| onset-corrected | **−0.12 w** | −0.30 w | −0.48 w |

Per player: **≤2% of his value at any plausible input, and flat in GP** (1/1/0% at 41/55/70
GP). The costliest shape is a high-GP veteran resting scattered single games, where every
absence *is* its own onset. Three unmodelled things push the figure down further: today's 4 IR
slots, waiver streaming, and setting lineups late. The slate-wide-lock premise is unverified,
which can only shrink it.

⚠️ Still **assumed** for GP: that boards price roughly expected games. Nothing here measures a
board's GP haircut — that is a claim about the market; don't launder it as format math.

**Burstiness is EV-neutral for season points** (+0.00%, provably: equal day-level marginals,
independent players, and lineup value depends only on that night's availability set). It does
not extend to a short window, the split `LATE` draws; `eval-team` does not size that, so
neither does this file.

**No IR + empty pool after expansion:** a season-long absence also burns a slot. Marginal
38th body 60–73 PF = **0.100–0.122 wins**, an upper bound.

# The slot-fill curve

Slot template: `league-info §Lineups`, verified here against `FetchLeagueRules.rosterPositions`.
At 38 players the last slot is the hard one: a 7-game night still fills only **8.88** of 9, and
9.00 does not arrive until **11 games**:

| games that night | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| nights (of 131 scored) | 2 | 6 | 6 | 8 | 10 | 20 | 14 | 16 | 19 | 30 |
| players available | 1.7 | 3.1 | 5.2 | 7.8 | 8.7 | 11.1 | 12.7 | 14.0 | 15.6 | 17.5+ |
| slots filled /9 | 1.7 | 3.1 | 5.2 | 7.6 | 7.9 | 8.6 | 8.9 | 8.9 | 9.0 | **9.0** |
| cumulative share of lost slots | 14% | 47% | 68% | 79% | 89% | 96% | 98% | 99% | 100% | 100% |

The constraint is concentrated, not broad: **14 nights (11%) carry 68% of the loss, 32 nights
(24%) carry 89%**, and from 7 games up 4% remains. **107 unfilled slot-nights of 1,179
(9.0%).**

⚠️ **Deliberately no "season loss = N PF" headline** — that is an assumed price for an empty
slot times a slot count, and no price is defensible: the same slots come to roughly 1,500 PF
at `R`, 900 at a price of 10 and 1,800 at 20 (the illustration lives in `report_nights`'
docstring and is not re-derived on every run — re-measure before quoting a figure from it).
**The share columns are price-invariant** — quote those.

⚠️ **Every cell above is a 200-trial Monte-Carlo mean at `sim.py`'s fixed seed**, so
`sim.py nights` reproduces it exactly but a lower-trial cut does not — `test_sim.py` runs 40
and carries a ±0.03 tolerance on the shares for that reason. **A share that disagrees with
this table by a point is a different trial count, not a finding** — re-run the report.

- **Heavy night** (15–25 bodies for 9 slots): only *rate* matters, the 10th-best scores
  nothing. **Light night** — `sim.LIGHT_GAMES`, ≤5 NBA games, **32** of them, biting hardest
  on the 14 at ≤3: nearly everyone available starts, so a 26-FPts body and an 8-FPts body
  differ by the full 18 — *presence, not rate.* Surplus is therefore **the middle**, not the
  top and not the tail.
- **Positions rarely bind:** 1.8% of slot-nights lost to no legal slot against 7.3% to no body
  at all. Both take `min(9, ·)` of a *bucket mean*, so by Jensen the positional figure is an
  **upper bound** — it runs with the conclusion, so say so.

# Positional premium — a fact about *our* roster, not the format

Added body of identical rate, versus that rate as a guard:

| rate | 25 | 35 | 45 |
|---|---:|---:|---:|
| forward vs guard | **+12%** | +11% | +7% |
| centre vs guard | **−16%** | −7% | −5% |

At rate 25 that +12% is **~+0.08 wins** — worth pricing on a marginal body, not worth building
around, and the premium shrinks as rate rises: a high-rate player starts on heavy nights
regardless of slot. **Centre is a discount, not a wash** — the same roster shape that
pushed centre `R` to 19.9 (§*Valuation formula*) is what makes another centre worth less than
a guard here.

⚠️ **Purely a function of our current positional distribution** — on the **padded 38 the
bodies are added to**, 15 pure PG/SG chasing at most 5 guard-eligible slots and 9 pure centres
chasing 3 (11 and 6 on the live 28, which is a different roster from the one measured here).
**Not structural**, and it disappears when the roster's shape changes.

# Light-night coverage — what steering the auction buys

§*The slot-fill curve* is the mechanism; this is the size of it, and
`Eval Definitions §Where our format pulls off consensus` 5 is the rule that spends it.
**`python3 sim.py schedules` emits every table below** (~4 min); `--roster` gives another
team's answer, which is a different one.

**Steering the seven September auction bodies on schedule is worth +0.095 ± 0.015 wins** —
the best 7 of a random 15-team availability set, against not caring. With all 30 teams on
offer it is **+0.212**; the worst available — greedy-minimised, which is all seven stacked on
the emptiest schedule — is **−0.602**, so the whole choice spans ~0.8 wins. ⚠️ **Not caring is
itself a lottery, not a neutral draw:** 20 random 7-body draws land **−0.33 to −0.02 wins**
behind the best-7 (sd **0.098**) — what ignoring schedule actually costs swings by ±0.1 wins
on its own, and one draw in twenty lands on the answer by accident.

⚠️ **+0.095 sits *at* the ~0.1-win floor (`method.md`), not clear of it — so the upside does
not carry this rule.** It survives its own error bar (±0.015 is a standard error; ±14% on
PF→wins moves it to 0.08–0.11, not to zero) and fails the **size** test. Two things carry it
instead. **The downside is the bigger half** — the same seven chosen badly is **−0.602**, six
times the headline, and the uninformed draws' own sd (**0.098**) is as wide as the entire
gain. **And it is nearly free** — it only orders bodies already tied on
`(rate − R) × GP`, and the most it spends is the rate-point band below (~10 PF, **0.018
wins**, on a rate-8 body). It is sized and spent like §*Positional premium* (+0.08 on a
marginal body), not like a `Δw`: **avoiding the stacked shape is the case for it, capturing
the good draw is not, and neither buys a schedule at any price.**

⚠️ **One baseline and one selection rule, and every figure here is meaningless without both.**
Each is quoted against *not caring* — the mean of those 20 random draws — and every pick is
greedy on `coverage`. That is what makes the saturation ladder's last rung the *same number*
as the all-30 best-7 headline. **A steering figure not cut this way is a different quantity,
not an earlier measurement of this one — re-cut it rather than reconcile it.**

**Per body, the schedule is worth far less than the body** — one added 55-GP forward-elig
body, swept across all 30 NBA schedules:

| body's rate | 8 | 12 | 20 | 40 |
|---|---:|---:|---:|---:|
| mean added PF | 40 | 67 | 209 | 981 |
| sd across the 30 schedules, PF | 10.9 | 17.0 | 32.1 | 44.7 |
| that sd in wins | 0.018 | 0.028 | 0.054 | 0.075 |
| that sd in **rate points** | **2.07** | 1.75 | 1.19 | 1.05 |
| end to end, rate points | 9.0 | 7.9 | 4.9 | 4.1 |

**Sub-proportional to value, not constant:** the body grows **24×** from rate 8 to 40 while
the schedule sd under it grows **4×**. **It rises with rate because what changes is not
whether the body plays but what it displaces** — a real producer starts every night either
way, but on a heavy night he pushes a startable teammate out (marginal ≈ his rate *minus
theirs*) and on a light night he fills a slot that would otherwise sit empty (marginal ≈ his
*full* rate). The premium is whatever got displaced: capped by the body's own rate down the
tier, by the displaced body's up it. ⚠️ **Not a reason to price a star's schedule** — you
never choose a real producer's NBA team, and 44.7 PF against a 981-PF body is 1.05 rate
points. Rate points are the PF sd at the *measured* PF-per-rate-point slope of the same
30-schedule mean (central difference, ±2) — a slope that itself runs 2.5 (BKN) to 8.0 (OKC) at
rate 8, which is why it has to be measured on the mean rather than on `SIM_TM`.

**The threshold is ~2.1 rate points at the grade it is actually spent at.** This is an
acquisition tiebreak and the auction fills at **8–14 FPts**, where the exchange rate runs
**2.07 → 1.75** — a ~15% slide, inside these files' own error terms, so **one number serves
the whole auction tier** and there is nothing to interpolate inside it. ⚠️ **It is not flat
above that tier.** 2.07 → 1.05 from rate 8 to 40 is a **2×
slide**, wider than any error term here, so the rule's other cases — an `fa` row, a
`sim.star()` body — read a **smaller** threshold the higher the rate. **Quote the row that
matches the body, and never carry 2.1 onto a real producer.**

⚠️ **And it is not a per-player quantity at all.** The greedy rule takes **LAC twice**: the
same schedule under the same body is worth **+0.016 as the first pick and −0.010 as the
seventh** — opposite signs, because by then the other six already reach every light night
LAC has. Across the ladder the identical decision runs **+0.016 to +0.068** and does not
decline in order. What it buys is a property of what the other six cover, not of the body.

**Saturation** — k of the seven picked on schedule, cumulative, against not caring:

| schedule-aware picks | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---:|---:|---:|---:|---:|---:|---:|
| cumulative +wins | +0.016 | +0.079 | +0.108 | +0.176 | +0.206 | **+0.222** | +0.212 |
| paired ± | 0.012 | 0.017 | 0.020 | 0.019 | 0.020 | 0.022 | 0.022 |
| the steered picks cover | 12 | 23 | 28 | 30 | 31 | **32** | 32 |
| all 7 cover, mean | 27.9 | 29.4 | 30.2 | 30.8 | 31.2 | 32.0 | 32.0 |

Picks: **LAC · OKC · UTAH · SA · MEM · NY · LAC**. **Three picks buy 49% of the peak and four
buy 79%; it peaks at six and the seventh buys nothing** (−0.010 against its own paired
±0.006) — the greedy rule's own seventh pick is a *repeat*, because coverage saturates at
six (32 of 32) and there is no light night left to reach. That is the saturation finding
stated by the rule rather than asserted about it — and the report **derives** that verdict
from the increment and its σ, so a re-cut where the last pick does pay says so instead.
⚠️ **The per-pick increments are not ordered** (they run 0.02–0.07 and do not decline
monotonically); quote the cumulative row and the saturation point, not a single pick's worth.
⚠️ **Four is not where the payoff ends.** Picks 5 and 6 are the other **21%** (+0.046
together) and steering costs nothing, so **steer all six** — four is where the *attention*
pays, not where the ladder stops.
The `±` is *paired* — rung k and rung k−1 share the draw and the seeds — so it is 3–5× tighter
than the ±0.1 lottery the rungs are measured inside.

⚠️ **The quantity bought is distinct light nights *covered*, not summed per-body counts.**
Only **32** of the 131 scored nights carry ≤5 NBA games (**14** at ≤3), so the payoff is
bounded by how many of those 32 the **seven** reach between them — and a second body on a
night one of them already reaches is chasing the slot the first one took.

| seven bodies | body-nights summed | distinct nights covered | +wins |
|---|---:|---:|---:|
| stacked on LAC (tied-deepest light-night schedule, with OKC) | **84** | 12 | **−0.199** |
| the spread best-7 | 74 | **32** | **+0.212** |

**84 is the *ceiling* on that sum** — 7 × the deepest per-team count of 12 — and the shape
that reaches it lands *below not caring*. Over the 43 configurations the report measures
(spanning 3–32 nights covered), PF regresses on **nights covered at 13.1 PF/night, R² 0.71**,
against **1.7 PF/night, R² 0.35** on the summed count: coverage wins that comparison, which is
the whole of the claim. **Diversification is not a separate principle — it is a proxy for
coverage.** ⚠️ **Still only a proxy:** neither quantity explains the
spread *inside* the realistic band (a random 7 already covers 26 of 32), where the 9-slot
mechanics on the nights you do cover carry the rest. **Steer on it; do not model with it.**

Light nights each team plays, **scored periods only** (131 of 165 nights, 959 of 1,231
games; mean **7.60** per team, sd **2.39**):

| light nights | teams |
|---:|---|
| **12** | LAC · OKC |
| **10** | HOU · LAL · SA · UTAH |
| **9** | BOS · IND · MEM · MIN · NY · PHI |
| **8** | DEN · GS · MIA · MIL |
| **7** | CHA · CLE · DAL · SAC · TOR · WSH |
| **6** | ORL · PHX |
| **5** | ATL · DET · NO |
| **3** | BKN · CHI · POR |

**Total scored-period games barely vary (62–66 per team), so the choice buys light nights,
not games** — do not read this table as a strength of schedule. ⚠️ **The scored basis is
load-bearing:** the whole calendar carries 38 light nights, not 32, and re-ranks teams by up
to 5 (DEN 13→8, NY 14→9) — the fantasy season ends before the NBA's, so an April light night
is worth nothing.

⚠️ **Measured on the '25-26 calendar, at 38 bodies, against our current 22-NBA-team spread —
which nights are already covered is what sets both figures, and our other 31 bodies already
reach 31 of the 32.** Re-cut the +0.095 and the saturation point; never carry either forward.

**Projectability: year 1 only, and year 1 needs no projection** — the NBA schedule is
published mid-August. Over 11 seasons, per-team light nights autocorrelate at lag 1 at
**+0.296, p<0.0001** — real, not noise — but the predictable spread at h≥2 is **~0.38 light
nights against a raw spread of 2.44**, about **0.008 wins**, and it is dead by year 3.
⚠️ The 2025-26 media deal (NBC/Peacock Mon+Tue, ESPN Wed, Amazon Thu+Fri) re-dealt every
team's position and collapsed dispersion (**sd 4.0 → 2.44**); it is one season into an
eleven-year deal, so whether the new regime is itself persistent is untestable until
Aug 2026.

⚠️ **This last paragraph is the one claim on this page with no report behind it** — it needs
eleven seasons of NBA schedules and `fetch_data.py` writes one. Treat the autocorrelation and
the 0.008 as unverified here; everything above it re-cuts from `sim.py schedules`.

# Sept '26 expansion

`league-info` owns the format facts (28 → 38, the rookie rounds and the auction). What the sim
measures about them:

- Filling to 38 with auction-grade bodies: **+1,219 PF (+2.04 wins), free** — more than
  most consolidation trades on this page, and the cheapest wins available.
- **Breadth stops being a differentiator — *which* seven does not.** Everyone fills out of
  the same auction, so hoarding 20-FPts filler now buys nothing durable. Steering those seven
  adds a little on top of the +2.04 and sits at the ~0.1-win floor: a free tiebreak, never a
  reason to pay for a schedule (§*Light-night coverage*).
- **A traded-away body cannot be replaced.** 3-for-1 leaves 36 players and 2 dead slots.
