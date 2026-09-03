# `Δw` — wins, league curve

Expands `Eval Definitions §Δw`.

Single-season wins a typical team in this format gets from the player's projected rate and GP. Mean 38th-body curve across all 12 rosters (`evals/lineup-math/league-curve.md`). Not our roster. Scoring weights are in `FPts/Gp`. The 9-slot cap is inside the curve. This roster's shape and the NBA calendar live in **`Δw (season)`** (`Delta w (season).md`).

`sim.formula_player_wins` interpolates the measured PF table at 60 GP, scales by `GPp / 60`, converts via `K`. Floor is 0. A player's formula `Δw` does not change by roster.

- **Never sum across pieces on one roster for `Δw (season)`** — marginal against the roster as it stands; packages need joint sim (`Delta w (season).md`). **Trade-table formula `Δw` on a multi-piece deal is a per-piece net sum** — publish it, but read `Δw (season)` for the joint price. Extra bodies on a 3-for-1 read slightly high (they compete for the same slots).
- **Never confuse with `Δw (season)`.** Re-run `sim.py formula` for the error bar. The error is an offset, not a scale; no multiplier converts formula to sim. **Lean on `Δw (season)` for the call**; formula `Δw` is always shown beside it on eval and trade tables.
- **Use when no sim run exists** — quick screens, auction ordering before a team is known, explaining a BASE↔`FPts/Gp` gap. Light-night tiebreaks rank on formula **`Δw`** first (`Format edges.md` §4).
- **The rate is projected** — same `FPts/Gp` / `GPp` inputs as the sim (`projections`); never hand-adjust for role change or injury.
- **One season only** — multi-year value is BASE's entirely.

`sim.league_pf` owns the curve. `findings.md` §*PF → wins* owns `K` — re-run `K`, never quote a remembered figure. Re-cut the curve when the calendar or the twelve roster files move (`sim.py league-curve`).
