# Eval Template

Cell formats and column order for every human team eval file (`eval-team` §Output). Definitions cite `Eval Definitions`; section order follows `template.md`.

# Player table columns

**Ours** (`my-team/`):

| … | GP proj (last) | **Δw** | **Δw 'YY–'YY ours** | **ΔP(title)** | **Score** | W20 | W21 | W22 | W23 | flag |

**Counterparty** (every other team):

| … | GP proj (last) | **Δw** | **Δw 'YY–'YY ours** | **Δw 'YY–'YY theirs** | **ΔP(title) ours** | **Score** | W20 | W21 | W22 | W23 | flag |

- **`Δw`** = formula wins (`Eval Definitions §Δw`) — league curve, ~600 PF per win. One column on every table. Never sum formula `Δw` across pieces on one roster for trade calls — packages need joint sim for `Δw (season)`; formula on a multi-piece deal is a per-piece net sum on trade tables only.
- **`Δw 'YY–'YY …`** = **`Δw (season)`** (`Eval Definitions §Δw (season)`). Tag from `fetch_data.season_dw_tag()`. **`Δw (season) ours`** is the only cross-team-comparable win column.
- **`Score`** = `Score.md` §Player Score, from the row's own columns (counterparty: the `ours` columns).
- Publish **both** win columns on every player row. They are different currencies — never convert, net or rank a trade on one against the other (`Eval Definitions §Δw`, `§Δw (season)`).

Sort the table by **BASE** descending unless a file states otherwise. **`σ`** footnotes name ties in the sim's **`Δw (season)`** ordering (counterparty: **theirs** column), not necessarily the BASE sort (`Eval Definitions §σ`).

# Cell formats

Every modelled number (BASE, projections, win columns, `ΔP(title)`, Score, W20–W23, VALUE) and last-season FPts/G rounds per the `rounding` Skill; last-season GP, ranks and AGE don't.

| Col | Format |
| --- | --- |
| **BASE** | bold: **8000** |
| FPts/G proj (last) | projection, then actual in parens: `48 (47)` · no sample → `34 (–)` |
| GP proj (last) | projection, then actual in parens: `70 (65)` |
| **Δw** | signed, bold: **+1.9** · **+0.44** |
| **Δw 'YY–'YY …** | same |
| **ΔP(title)** / **ΔP(title) ours** | `%` suffix: **16%** · **1.1%** · may be negative |
| **Score** | bold, may be negative: **400** |
| W20–W23 | expected PF · no projection → `–` |
| Boards | Dizzle • Hashtag (crowd): `51 • 62 (68)` · absent → `–` · Dizzle off its rookie chart (`base.py` `CHART` line) → `~342` |
| AGE | one decimal · unknown → `–` |
| POS | eligibility slash-separated: `PG/SG` |

# Flags

Carry on every row that triggers one. Sim codes only (`sim.evidence_flags` / `sim.py players`), no prose duplicates. Multiple flags: middle dot separator (`frag · rot2`).

- **`frag`**: last season 25 games or fewer (`Durability.md`)
- **`miss`**: missed a whole season
- **`rotN`**: only N rotation seasons, N < 3 (`Durability.md`)
- **`nopool`**: no pool history
- **`fa`**: unsigned (table only)
- **`noproj`**: no rate projection (table only)
- **`board split`**: eval-only, defined in `BASE.md`
