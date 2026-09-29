# League curve

How formula `Δw` is measured. Definition: `evals/Definitions/Delta w.md`. `K`: `findings.md` §*PF → wins*. This-roster value: `Delta w (season).md`.

Reproduced 2026-09-03. Re-cut: `./run sim.py league-curve`. Shipped table: `simlib/league_curve.py`.

## Measurement

Add one synthetic Clippers forward (60 GP, SF/PF) as the 38th body on each of the 12 rosters padded to 37. Mean extra season PF, 3 seed blocks (`101, 301, 501`), 19-matchup calendar.

| rate | 0 | 5 | 8 | 11 | 14 | 17 | 20 | 23 | 26 | 30 | 35 | 40 | 48 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PF @ 38, GP 60** | 0 | 12 | 19 | 35 | 61 | 104 | 168 | 255 | 358 | 522 | 738 | 955 | 1304 |

Linear region (rate ≥ 26): **43.1 PF per rate point at GP 60 = 0.718 PF/G**. x-intercept **17.8**. GP scales: 78/60 = 1.30 at rates 14, 26, 40.

A 14-rate body is **+61 PF (+0.10 wins)** — starts on light nights, never zero.

One NBA team is enough for the shape (light nights and packed nights). Clippers-specific empty nights move 17.8 a little, not 0.72. Last-slot add, not a starter swap. Equal weight on all 12, including thin tanks and our 35-body roster. 20-GP stars were not swept — scale from 60; season `Δw` for that edge.

## Rejected

- **`R = 15`, slope 1.0** — last-rostered, not format value. Overstates stars; zeros light-night bodies. Six-deal formula sum **+8.58** vs joint season **+2.51** (`evals/teams/my-team/Recent Trades.md`).
- **`R ≈ 20` / median team `REPL`** — 9-slot intercept, still slope 1.0. Makes Huff-class negative.
- **`R ≈ 25` / our fitted `REPL`** — our crowding. Stale Hlina **+0.1** was this wearing an agnostic label.
- **BASE scale** — multi-year market vs one season. No exchange rate (`Eval Definitions`).
- **Raw `rate × GP`** — a 50 @ 20 is not a 20 @ 50.

Keep the name **`Δw`**. Same column: roster-agnostic, this season, this league. New object: the curve, not `(rate − 15) × GP ÷ K`.
