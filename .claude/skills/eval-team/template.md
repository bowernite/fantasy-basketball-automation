# {Owner} (`{Team name}`)

> _{N} bodies · **{SIT}** · sim {YYYY-MM-DD}_

## Players

| Player                              |  AGE | POS     |    Boards    | **BASE** | FPts/G proj (last) | GP proj (last) | **Δw** | **Δw 'YY–'YY ours** | **Δw 'YY–'YY theirs** | **ΔP(title)** | **Score** | W20 | W21 | W22 | W23 | flag |
| ----------------------------------- | ---: | ------- | :----------: | -------: | :----------------: | :------------: | -------: | ----------: | ------------: | --: | -------: | --: | --: | --: | --: | ---- |
| {every rostered body, no shortlist} | 25.8 | PG/SG   |  10 • 8 (9)  | **7500** |      45 (46)       |     60 (70)    | **+2.1** |   **+1.7** |     **+2.3** | 12% | **9500** | 180 | 110 | 110 | 110 |      |

`Boards` = Dizzle Points • Hashtag Points (Hashtag crowd in parens — printed, not blended) (`Eval Definitions §BASE`). `FPts/G proj (last)` and `GP proj (last)` = projection, then last season's actual in parens. Cell formats, rounding and flag names: `Eval Template.md`.

## Picks

{One table per draft year the league has traded into. Per year, name which of their **own** picks are gone. Ranks sourced, conversions modelled.}

### Sept '{YY} — {sourced | modelled off projected finish}

| Pick | Origin | Ordinal | Board row | rank | **VALUE** |
| ---- | ------ | ------: | --------- | ---: | --------: |

{Do not offer any commentary for picks. Just the tables.}

# Details

**Counterfactual:** {one line — what the `Δw (season)` columns swap him against, and the per-group `R` each was fitted at. Formula **`Δw`** — cite `Eval Definitions §Δw`. `Δw (season) ours` is the only cross-team-comparable column; `Δw (season) theirs` is fitted against _their_ `R` and the two differ by several rate points between teams, so the theirs−ours gap is not a number and no target may be ranked on `Δw (season) theirs`.}

# Title odds

{**Counterparty:** projected season PF and rank, `SIT`. **`ΔP(title) ours`** in the table (`--eval` / `incoming_title` on `basis()`).}

{**Ours:** roster `P(title)` from `sim.py title`. **`ΔP(title)`** in the table (`player_title` / `title-column` `include: ["ours"]`).}
