# League curve

How formula `Δw` is measured. Definition: `strategy/Definitions/Delta w.md`. `K`: `findings.md` §*Replacement level*. This-roster value: `Delta w (season).md`.

Re-cut 2026-09-29 (post-draft rosters, F/C flex). Re-cut: `./run sim.py league-curve`. Shipped table: `simlib/league_curve.py`.

## Measurement

Add one synthetic Clippers forward (60 GP, SF/PF) as the 38th body on each of the 12 rosters padded to 37. Mean extra season PF, 3 seed blocks (`101, 301, 501`), 19-matchup calendar.

| rate | 0 | 5 | 8 | 11 | 14 | 17 | 20 | 23 | 26 | 30 | 35 | 40 | 48 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PF @ 38, GP 60** | 0 | 15 | 25 | 38 | 57 | 90 | 148 | 233 | 335 | 497 | 712 | 930 | 1278 |

Linear region (rate ≥ 26): **43.0 PF per rate point at GP 60 = 0.717 PF/G**. x-intercept **18.4**. GP scales: 78/60 = 1.30 at rates 14, 26, 40.

A 14-rate body is **+57 PF (+0.09 wins)** — starts on light nights, never zero.

One NBA team is enough for the shape (light nights and packed nights). Clippers-specific empty nights move 18.4 a little, not 0.72. Last-slot add, not a starter swap. Equal weight on all 12. 20-GP stars were not swept — scale from 60; season `Δw` for that edge.

## Rejected

- **`R = 15`, slope 1.0** — last-rostered, not format value. Overstates stars; zeros light-night bodies. Six-deal formula sum **+8.58** vs joint season **+2.51** (six Jul–Sep '26 deals, simmed 9/2/26, pre-F/C).
- **`R ≈ 20` / median team `REPL`** — 9-slot intercept, still slope 1.0. Makes Huff-class negative.
- **`R ≈ 25` / our fitted `REPL`** — our crowding. Stale Hlina **+0.1** was this wearing an agnostic label.
- **BASE scale** — multi-year market vs one season. No exchange rate (`Eval Definitions`).
- **Raw `rate × GP`** — a 50 @ 20 is not a 20 @ 50.

Keep the name **`Δw`**. Same column: roster-agnostic, this season, this league. New object: the curve, not `(rate − 15) × GP ÷ K`.
