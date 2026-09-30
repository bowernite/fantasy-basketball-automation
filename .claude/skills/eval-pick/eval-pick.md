---
description: Use when pricing a rookie draft pick, or weighing a pick against a player
---

Load: `league-info` (draft rules) · `get-league-info` (fetching, and the draft-label trap) · `Eval Definitions §BASE` (the curve; picks and players land on the same one) · `eval-player` (boards) · `strategy/teams/my-team/Ours.team.md`.

_Source set and blend verified 2026-07: re-check each board's skill for staleness, and `league-info` for the roster size in effect._

# Procedure

## 1. Resolve which draft

A season's finish sets the **following** offseason's draft, so "a 2029 2nd" is ambiguous. Done when you've named the season whose finish sets the slot (`get-league-info`), in the output.

## 2. Resolve the slot

- **Next draft, once its order is set:** read it. `FetchLeagueDraftBoard` gives real slots and marks acquired picks.
- **The draft the current season sets:** project the **originating** team's record rank (not the current holder's) from `strategy/Team Projections.md`, with a range, then apply `league-info`'s draft-order rule. The rule **splits by record band, not by round**: every round shares one order, so a projected top-4 finish resolves to an exact slot in every round, and a projected bottom-8 finish is a **prior only** in every round. Publish a range for the latter; never derive it.
- **Every later draft:** `future-picks.md` step 1.
- **Never read a displayed future slot**: Fleaflicker shows placeholders copied from the last finish.

Done when each pick has an exact slot or a published range.

## 3. Ordinal, not label

Charts price the NBA's 60 slots; ours is 12 × 4 taking any player in any order. Our `R.S` = overall ordinal **`(R−1)×12 + S`**, and that ordinal is the lookup. Reading the label under-prices every pick after round 1. Our whole draft (ordinals 1–48) fits inside their round 1 plus the first 18 of round 2.

**Then convert the ordinal to a label in the chart's 30-wide rounds, never ours**: row `⌈ord/30⌉`, slot `ord − 30×(⌈ord/30⌉−1)`. Our 2.01 (ord 13) is chart `1.13`; our 3.09 (ord 33) is chart **`2.03`**, not `2.09`. Carrying our round structure back out is the same error one step later, and costs most on picks that cross into the chart's round 2.

Done when each pick has an ordinal and a chart label.

## 4. BASE

Only two boards price a current-class slot, so the blend is 50/50 between them, not `Eval Definitions §BASE`'s player weights.

- **Dizzle: read the slot prefix off the *dynasty* Points board.** It carries the incoming class inline, each row prefixed with its slot (`1.09 / Brayden Burries`). Match the chart label (§3) against that prefix, take that row's **board rank**, run it through the curve. Chain: `ordinal → chart label → prefixed row → board rank → value`.
- **Hashtag crowd:** the `/keeper` pick row whose band contains the same ordinal → that row's crowd rank → curve.

`VALUE` = mean of the two.

- **Crowd board carries a vote-convergence notice → Dizzle alone**; its pick rows are unreliable until that clears. The notice tracks vote settling on a newly-loaded class: **not a class-strength signal, and never about a future class** (`future-picks.md`).
- **Once the NBA draft passes**, the crowd's pick rows price the next class (`future-picks.md`); the current class's crowd half is then the crowd rank of the slot's player (§5).
- **4th round (ordinals 37–48): never use a crowd pick band**; its bands lump late 3rds and every 4th onto one rank (§7 ceiling). Where the crowd half would be a band, `VALUE` = Dizzle alone; prefix, else chart, labelled.
- **No pick prices above an earlier ordinal of the same draft**: cap it at that pick's value and say so.

**The slot→value lookup (every section that prices a slot uses this one):** prefer the prefix over the pick chart for every slot that has one. It is an exact per-slot rank on the board players are priced on (no name join, no band midpoint), and it separates slots the chart flattens (§7). Use the chart only as the cross-check below, or as the fallback where a slot has no prefixed row: band `Top lo–hi` → rank `floor((lo+hi)/2)` → curve, labelled as the coarser figure. **The two disagree materially across our whole range**: say which you used.

Where prefix and chart diverge materially, publish **both values side by side**; a large gap either way means that board's class is still normalising (§7). Compare in absolute terms, never as a ratio (`Eval Definitions §BASE`).

Done when each pick has a `VALUE` labelled with its source (prefix, chart, or Dizzle alone).

## 5. Cross-check against the players available at that slot

Two separate lookups:

- **Class order** comes off a rookie tab / `DDTYPE=ROOKIE`. A rookie tab's `#` is a **within-class ordinal**, never a board rank; running it through the curve prices a mid-first like a top-10 asset (~4× off).
- **Board ranks for those players** come off all three boards: Dizzle's dynasty Points board (**the §4 prefix already is this**, so don't count it twice; for Dizzle the remaining cross-check is the chart), plus **Hashtag crowd (`/keeper`)** and **Hashtag expert `DDTYPE=POINT`**, which carry the class inline on their own ranks.

Take the class ordinal for the slot, read those boards' ranks over a **window around it** (a few names either side), and use the **min and max** as the range. Ranks routinely fail to rise with class order, by 100+ places; where a board's class order inverts, say so (a live class-normalising signal).

Joining a class name to a board row follows `eval-player` §*Joining names to board rows*; a failed join is never a value of 0.

Where the players and the chart disagree materially, prefer the players, publish both, and say why. Neither brackets the other: one is sourced, one derived (`Eval Definitions §Sourced vs modelled`).

Done when each pick has a player-window range beside its `VALUE`.

## 6. Cap the near-term half

Never cap BASE. Cap what the pick is worth *to this roster*, in the `Δw (season)` layer (`trades` Skill): a pick can't beat the cheapest alternative way to fill the same slot. That alternative is set by backfill availability (`Eval Definitions §Where our format pulls off consensus`): a known veteran off the wire or an auction while the pool is live, nothing once every NBA player is owned. So the near-term half of a late pick is worth ~0 while backfill exists, and rises when it doesn't.

**No external chart models this**: every chart over-prices our late picks, and so will a counterparty reading one. Done when you've named the backfill regime.

## 7. Sanity checks

- **A pick band and the players it would take are far apart in either direction** → that board's class is still normalising; distrust the row. Early bands typically price *above* the player; wide later bands can price well *below* two of the players inside them. Same symptom.
- **A band's last slot prices identically to its first**: at the wide end of a wide band the number is a ceiling, not an estimate. Consecutive identical slots are a band-width artefact; the §4 prefix resolves them, so flag it only when falling back to the chart.

# A chart prices ONE class

Slot→value off a chart (or the §4 prefix) is a claim about that draft only: the chart carries a cliff wherever *that* class thins, and another class thins elsewhere or not at all. Price every future pick off its own year's market: `future-picks.md`.

To locate the current chart's cliff: walk consecutive rows, convert each band to its midpoint rank then to a value, take the largest step down. Two expectations, both forced by `V()`'s convexity (`Eval Definitions §BASE`):

- At the *first* slot of a newly-wider band, not on the plateau before it.
- **Near the top of the chart**, where a band first widens. A small rank step high up dwarfs a large one deep down (a 30-rank step at rank 30 beats a 60-rank step at rank 215 by ~8×). So the chart's round-1/round-2 boundary is **not** the largest step; no round boundary is (a label, not a thinning).

**Cite location and class, never a remembered magnitude.**

# A pick has no production dimension in year 1

Rookie year-1 rates are typically at or below replacement, so in its first season a pick contributes as a body, not a producer. State this whenever a pick trades against a player:

- A veteran pays now; a pick pays in two years. One BASE number hides the difference.
- **For a contender, trading a mid or late pick for a durable mid-tier producer wins on this axis alone.** Say it. Reverse it only when deliberately selling the window.
- A draft haul is an asset for the season after next.
- A late pick's value is entirely its multi-year tail: price it as a lottery ticket on that tail (`Eval Definitions §SIT`, prospect tail) and nothing else.
- **Never discount a pick's VALUE for window, roster fit or pick surplus**, ours or theirs. Win-now preference lives in the win columns and `ΔP(title)`; between deals inside `Score`'s tie band, prefer the one that turns picks into producers.

# Sources

Board details and staleness: `eval-player`. Pick-specific: `dizzle-dynasty` for the dynasty board's slot-prefixed rows (start here) and its `Top N–M` chart · `hashtag-basketball` for the crowd pick bands **and** both boards' ranks on the class itself (§5) · `dynatyze` for the future-pick board (`future-picks.md`). Worked example with that day's numbers: `strategy/board-snapshots/Boards 2026-07-29.md`.
