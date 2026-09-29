# Eval Template

Cell formats and column order for every human team eval file (`eval-team` §Output). Definitions cite `Eval Definitions`; section order follows `template.md`.

# Player table columns

**Ours** (`my-team/`):

| … | GP proj (last) | **Δw** | **Δw 'YY–'YY ours** | **ΔP(title)** | W20 | W21 | W22 | W23 | flag |

**Counterparty** (every other team):

| … | GP proj (last) | **Δw** | **Δw 'YY–'YY ours** | **Δw 'YY–'YY theirs** | **ΔP(title) ours** | W20 | W21 | W22 | W23 | flag |

- **`Δw`** = formula wins (`Eval Definitions §Δw`) — league curve, ~600 PF per win. One column on every table. Never sum formula `Δw` across pieces on one roster for trade calls — packages need joint sim for `Δw (season)`; formula on a multi-piece deal is a per-piece net sum on trade tables only.
- **`Δw 'YY–'YY …`** = **`Δw (season)`** (`Eval Definitions §Δw (season)`). Tag from `fetch_data.season_dw_tag()`. **`Δw (season) ours`** is the only cross-team-comparable win column.
- Publish **both** win columns on every player row. They are different currencies — never convert, net or rank a trade on one against the other (`Eval Definitions §Δw`, `§Δw (season)`).

Sort the table by **BASE** descending unless a file states otherwise. **`σ`** footnotes name ties in the sim's **`Δw (season)`** ordering (counterparty: **theirs** column), not necessarily the BASE sort (`Eval Definitions §σ`).

# Cell formats

| Col | Format |
| --- | --- |
| **BASE** | integer, bold: **8082** |
| FPts/G proj (last) | projection, then actual in parens: `48 (47)` · no sample → `34 (–)` |
| GP proj (last) | projection, then actual in parens: `68 (65)` |
| **Δw** | signed, two decimals, bold: **+1.85** |
| **Δw 'YY–'YY …** | same |
| **ΔP(title)** / **ΔP(title) ours** | one decimal, `%` suffix: **16.4%** · may be negative |
| W20–W23 | integer expected PF · no projection → `–` |
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
