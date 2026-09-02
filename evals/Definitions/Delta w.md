# `Δw` — wins above replacement, formula

Expands `Eval Definitions §Δw`.

Single-season wins from projected rate and GP above replacement — **not** roster- or schedule-specific. Scoring weights are already in `FPts/Gp`; this line ignores the 9-slot cap, the NBA calendar and lineup optimization. Those live in **`Δw (season)`** (`Delta w (season).md`).

**`(rate − R) × GP ÷ K`** for a 1-for-1 only. `K` ≈ **600 PF** per win — band **518–679** (`findings.md` §*PF → wins*). `R` from `sim.py replacement` at the roster size being valued; per slot group on a padded 38: guard · forward · center (`findings.md` §*Valuation formula*).

- **Never sum across pieces on one roster for `Δw (season)`** — marginal against the roster as it stands; packages need joint sim (`Delta w (season).md`). **Trade-table formula `Δw` on a multi-piece deal is a per-piece net sum** — publish it, but read `Δw (season)` for the joint price.
- **Never confuse with `Δw (season)`.** Against sim 1-for-1s the formula over-predicts by a **median +51%** — error is an offset, not a scale; no multiplier converts formula to sim. **Lean on `Δw (season)` for the call**; formula `Δw` is always shown beside it on eval and trade tables.
- **Use when no sim run exists** — quick screens, auction ordering before a team is known, explaining a BASE↔`FPts/Gp` gap. Light-night tiebreaks rank on `(rate − R) × GP` first (`Format edges.md` §4).
- **The rate is projected** — same `FPts/Gp` / `GPp` inputs as the sim (`projections`); never hand-adjust for role change or injury.
- **One season only** — multi-year value is BASE's entirely.

`sim.py formula` and `findings.md` §*Valuation formula* own the measured `R`, `K` and error bars — re-run, never quote a remembered figure.
