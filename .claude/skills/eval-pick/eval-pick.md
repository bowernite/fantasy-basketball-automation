---
name: eval-pick
description: Procedure for pricing rookie draft picks — slot resolution, chart lookup, future picks, and what a pick is worth in year 1.
---

Load: `league-info` (draft rules) · `get-league-info` (fetching, and the draft-label
trap) · `strategy/Definitions/Eval Definitions.md` §BASE (the curve — picks and players must land on the
same one) · `eval-player` (boards) · `strategy/teams/my-team/Ours.team.md`.

_Source set and blend below verified 2026-07 — re-check each board's own skill for
staleness, and re-read `league-info` for the roster size in effect._

# Procedure

## 1. Resolve which draft

A season's finish sets the **following** offseason's draft. "A 2029 2nd" is ambiguous —
resolve it by naming the season whose finish sets the slot (`get-league-info`), and say
which in the output.

## 2. Resolve the slot

- **Next draft, once its order is set:** read it. `FetchLeagueDraftBoard` gives real slots and marks acquired
  picks.
- **The draft the current season sets:** project the **originating** team's record rank (never the current
  holder) from `strategy/Team Projections.md`, with a range, then apply `league-info`'s
  draft-order rule. The order rule **splits by record band, not by round** — every round shares one
  order, so a projected top-4 finish resolves to an exact slot in every round, and a
  projected bottom-8 finish is a **prior only** in every round. Publish a range for the
  latter; never derive it.
- **Every later draft:** `future-picks.md` step 1.
- **Never read a displayed future slot** — Fleaflicker shows placeholders copied from
  the last finish.

## 3. Ordinal, not label

Charts price the NBA's 60 slots; ours is 12 × 4 taking any player in any order. Our
`R.S` = overall ordinal **`(R−1)×12 + S`**, and that ordinal is the lookup. Reading the
label under-prices every pick after round 1. Our whole draft (ordinals 1–48) fits inside
their round 1 plus the first 18 of round 2.

**Then convert the ordinal to a label in the chart's 30-wide rounds, never ours** — row
`⌈ord/30⌉`, slot `ord − 30×(⌈ord/30⌉−1)`. Our 2.01 (ord 13) is chart `1.13`; our 3.09
(ord 33) is chart **`2.03`**, not `2.09`. Carrying our round structure back out is the
same error as reading the label in, one step later in the chain, and it costs most on
picks that cross into the chart's round 2.

## 4. BASE

Picks have their own source set: only two boards price a current-class slot at all, so the
blend is 50/50 between them, not `Eval Definitions §BASE`'s player weights.

- **Dizzle — read the slot prefix off the *dynasty* Points board.** It carries the
  incoming class inline against players, each such row prefixed with its slot
  (`1.09 / Brayden Burries`). Match the chart label for the ordinal (§3) against that
  prefix, take that row's **board rank**, run it through the curve. Chain:
  `ordinal → chart label → prefixed row → board rank → value`.
- **Hashtag crowd:** the `/keeper` pick row whose band contains the same ordinal → that
  row's crowd rank → curve.

`VALUE` = mean of the two. **Use Dizzle alone whenever the crowd board carries a
vote-convergence notice** — its pick rows are unreliable until that clears. Once the NBA
draft passes, the crowd's pick rows price the next class (`future-picks.md`); the current
class's crowd half is then the crowd rank of the slot's player (§5).

That notice tracks vote settling on a newly-loaded class. **Not a class-strength signal,
and never about a future class** — that is §*Future picks*.

**4th round (ordinals 37–48): never use a crowd pick band** — its bands lump late 3rds and every 4th onto one rank (§7 ceiling). Where the crowd half would be a band, `VALUE` = Dizzle alone; prefix, else chart, labelled.

**No pick prices above an earlier ordinal of the same draft** — cap it at that pick's value and say so.

**The slot→value lookup, and every section that prices a slot uses this one:** prefer the
prefix over the pick chart for every slot that has one. It is an exact per-slot rank on the
same board the players are priced on, so no name join and no band-midpoint step; and it
separates slots the chart flattens (§7). Use the chart only as the cross-check below, or as
the fallback where a slot has no prefixed row: band `Top lo–hi` → rank
`floor((lo+hi)/2)` → curve, labelled as the coarser figure. **The two disagree materially
across our whole range** — never treat them as interchangeable, and say which you used.

Cross-check the two and publish **both values side by side** whenever they diverge
materially — a large gap either way means that board's class is still normalising (§7).
Compare them in absolute terms, never as a ratio (`Eval Definitions §BASE`).

## 5. Cross-check against the players actually available at that slot

Two separate lookups — don't conflate them:

- **Class order** comes off a rookie tab / `DDTYPE=ROOKIE`. A rookie tab's `#` is a
  **within-class ordinal**, never a board rank. Running it through the curve prices a
  mid-first as if it were a top-10 asset — off by ~4×.
- **Board ranks for those players** come off all three blended boards: Dizzle's dynasty
  Points board (**the §4 prefix already is this**, so don't count it twice — for Dizzle
  the remaining cross-check is the chart), plus **Hashtag crowd (`/keeper`)** and
  **Hashtag expert `DDTYPE=POINT`**, which carry the class inline on their own ranks.

Take the class ordinal for the slot, then read those boards' ranks over a **window around
it** (a few names either side) and use the **min and max** as the range. **Do not assume
the ranks rise with class order** — they routinely don't, by 100+ places. Where a board's
class order inverts, say so; it is a live class-normalising signal.

Joining a class name to a board row hits the normalisation rules in `eval-player` —
apply them, and never read a failed join as a value of 0.

Where the players and the chart disagree materially, prefer the players, publish both, and
say why. Neither is a bracket for the other — one is sourced, one derived (`Eval
Definitions §Sourced vs modelled`).

## 6. Cap the near-term half

Never cap BASE. Cap what the pick is worth *to this roster*, in the `Δw (season)` layer (`trades` Skill):
a pick can't beat the cheapest alternative way to fill the same slot. That alternative is
set by backfill availability (`Eval Definitions §Where our format pulls off consensus`) —
a known veteran off the wire or an auction
while the pool is live, nothing at all once every NBA player is owned. So the near-term
half of a late pick is worth ~0 while backfill exists, and rises when it doesn't.

**No external chart models this** — every chart over-prices our late picks, and so will a
counterparty reading one. Check the regime before pricing.

## 7. Sanity checks

- **A pick band and the players it would take are far apart in either direction** → that
  board's class is still normalising. Distrust the row. Early bands typically price
  *above* the player; wide later bands can price well *below* two of the players inside
  them. Both are the same symptom.
- **A band's last slot prices identically to its first.** At the wide end of a wide band
  the number is a ceiling, not an estimate. Consecutive slots priced identically are an
  artefact of band width, not a judgment that they are worth the same — the §4 prefix
  resolves them, so flag it only when falling back to the chart.

# A chart prices ONE class

Slot→value off a chart is a claim about that draft only.

**A slot run through the current class's lookup (§4) is never a future pick's price** —
both halves are one-class: the chart carries a cliff wherever *that* class thins, the
prefix is a rank inside it, and another class thins elsewhere or not at all. Price it off
its own year's market (below).

To locate the current chart's cliff: walk consecutive rows, convert each band to its
midpoint rank then to a value, take the largest step down. Two expectations, both forced by
`V()`'s convexity (`Eval Definitions §BASE`):

- At the *first* slot of a newly-wider band, not on the plateau before it.
- **Near the top of the chart**, where a band first widens. A small rank step high up
  dwarfs a large one deep down — a 30-rank step at rank 30 beats a 60-rank step at rank
  215 by ~8×. So the chart's own round-1/round-2 boundary is **not** the largest step and
  is not where to look; nor is any round boundary, which is a label, not a thinning.

**Cite location and class, never a remembered magnitude.**

Pricing a future class — off that year's market, identically on both sides of a deal — is `future-picks.md` (this directory).

# A pick has no production dimension in year 1

Rookie year-1 rates are typically at or below replacement, so in its first season a pick
contributes as a body, not a producer. State this whenever a pick trades against a
player:

- A veteran pays now; a pick pays in two years. One BASE number hides the difference.
- **For a contender, trading a mid or late pick for a durable mid-tier producer wins on
  this axis alone.** Say it. Reverse it only when deliberately selling the window.
- A draft haul is an asset for the season after next.
- A late pick's value is entirely its multi-year tail — price it as a lottery ticket on
  that tail (`Eval Definitions §SIT`, prospect tail) and nothing else.
- **Never discount a pick's VALUE for window, roster fit or pick surplus**, ours or theirs.
  Win-now preference lives in the win columns and `ΔP(title)`; between deals inside
  `Score`'s tie band, prefer the one that turns picks into producers.

Board details and staleness rules: `eval-player`. Pick-specific: `dizzle-dynasty`
for the dynasty board's slot-prefixed rows (start here) and its `Top N–M` chart ·
`hashtag-basketball` for the crowd pick bands **and** for both boards' ranks on the class
itself (§5) · `dynatyze` for the future-pick board (`future-picks.md`). Worked example with the numbers of
the day: `strategy/board-snapshots/Boards 2026-07-29.md`.
