# Score

Expands `Eval Definitions §Score`.

Our-side composite for a trade, in BASE units. `sim_run.py` trade-screen publishes it (`score_us`).

```
Score = ΔBASE + 300·(Δw − 0.3·N) + 250·Δw(season) + 80·ΔP(title)
```

- `ΔP(title)` in percentage points. `N` = net incoming players (in − out − `cut_us`, picks excluded) — formula `Δw` is a per-piece sum and reads high per extra incoming body.
- A sim cut (`cut_us`, `trades` §Uneven bodies) is an outgoing player: his BASE and `Δw` are charged as if named in Out.
- Which body is cut: the one whose cut leaves that side's Score highest (board BASE, `Δw`, `Δw (season)`, `ΔP(title)`). The sim shortlists the bottom `over`+4 by board BASE + 300·`Δw` (plus any within 250 of the `over`-th, max 12), sims each cut, and keeps the best; the counterparty's cut uses their seat's Score. Near-ties are not broken toward the partial.
- A cut is charged at **board** BASE (`eval-player/base.py`), a named Out at eval-file BASE. Where they differ (e.g. 2026 rookies), moving a `cut_us` into Out shifts Score by the gap.
- Fixed rates — never refit per team, roster or archive. Constants live in `simlib/score.py` (the sim's cut uses them too); change both together.
- **A baseline, not a verdict.** It gives a starting order; still read every number individually, in the context of our roster, `SIT`, `Δage` and counterparty.
- Within ~250 is a tie; wider on pick-heavy or uneven-body deals (`ΔBASE` is a band there, §BASE).
- Minimums and Too lopsided (`trades` §General guidelines, `trade-shapes` §Sections) gate on the individual numbers first. Score never rescues a failed minimum.
- Excludes `Δage`.

## Player Score

Every eval player row carries a `Score`: the formula on that row's own columns, N = 0 — the player against a replacement body (the auction's 1-for-1 swap for the $1 body).

```
Score = BASE + 300·Δw + 250·Δw(season) + 80·ΔP(title)
```

- Ours: `Δw (season)` and `ΔP(title)`. Counterparty: the `ours` columns — his Score on our roster.
- Integer, may be negative. Ranks a roster's bottom bodies (cut order) and wire adds against them; a free agent is priced with `player-effects` (`sims` Skill) and the same formula, BASE from his board rows (0 off every board).
