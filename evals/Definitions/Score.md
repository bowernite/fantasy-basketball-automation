# Score

Expands `Eval Definitions §Score`.

Our-side composite for a trade, in BASE units. `sim_run.py` trade-screen publishes it (`score_us`).

```
Score = ΔBASE + 300·(Δw − 0.3·N) + 250·Δw(season) + 80·ΔP(title)
```

- `ΔP(title)` in percentage points. `N` = net incoming players (in − out, named cuts included, picks excluded) — formula `Δw` is a per-piece sum and reads high per extra incoming body.
- Fixed rates — never refit per team, roster or archive. Constants live in `simlib/runner.py`; change both together.
- **A baseline, not a verdict.** It gives a starting order; still read every number individually, in the context of our roster, `SIT`, `Δage` and counterparty.
- Within ~250 is a tie; wider on pick-heavy or uneven-body deals (`ΔBASE` is a band there, §BASE).
- Minimums and Too lopsided (`trades` §General guidlines, `trade-shapes` §Sections) gate on the individual numbers first. Score never rescues a failed minimum.
- Excludes `Δage`.
