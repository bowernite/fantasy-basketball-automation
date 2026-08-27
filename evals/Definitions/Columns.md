# Columns

Expands `Eval Definitions §Columns` and §*Sourced vs modelled*.

Alongside BASE, never folded in. Sources: `get-league-info`.

| Col       | Source                                |                                                                                                                                                             |
| --------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Boards`  | §BASE's three boards                  | each board's rank for that player, blend order, one cell — so outliers stay traceable                                                                       |
| `FPts/G proj (last)` | `projections` · `FetchRoster?season=` `seasonAverage` | `FPts/Gp` then `FPts/G` in parens, one cell, so the divergence is visible. The projection is **the rate `Δw` runs on**; the actual is reporting only |
| `GP proj (last)` | `sim.project_gp` · `seasonTotal / seasonAverage` | `GPp` then `GP` in parens, one cell. The projection is what `Δw` runs on; the actual is reporting only                                       |
| `Δw ours` | `sim.py players` · `sim.incoming_wins` | sim-measured. Already ours → `players`. Not yet ours → `incoming_wins` against `basis()`, never a hand-edited roster file (`Eval Definitions §Δw`)           |
| `ΔP(title)` / `ΔP(title) ours` | `player_title` / `incoming_title` | table column — roster `P(title)` in `# Title odds` (`Bracket value.md`) |
| `AGE`     | `FetchPlayerProfile` `detail.dob`     | ms epoch, parse **UTC**. Never `detail.age`. **As of the eval's derivation date** — one convention, everywhere                                              |
| `POS`    | `proPlayer.positionEligibility`       | multi-position is underpriced. Slot group, as `sim.py` maps it: `{C}` → center · ⊆ `{PG,SG}` → guard · anything else → **forward** (so a PF/C is a forward) |
| `W20`–`W23` | `sim.py weeks`                      | expected points in bracket period *n* = `FPts/Gp` × that player's NBA games inside the period × `GPp` ÷ his NBA team's games (`Bracket value.md`). `–` with no projection or no NBA team |

**`σ` is never a table column** (`Eval Definitions §σ`) — a footnote, not a row-by-row read.

**A player with no last-season sample has no `FPts/G`** — print `–` inside the parens. He still has an `FPts/Gp`. **Never print a projection in the actuals position**, and never the reverse.

BASE and `FPts/Gp` will disagree; that's the signal. A wide `FPts/G` → `FPts/Gp` gap is a second one — the projection pricing a role change the last season cannot show.

**No format-fit column, and never a format-adjusted BASE.** Our scoring weights (`league-info`) are already inside `FPts/G` and `FPts/Gp`; the structural half — eligibility, 9 daily slots, NBA schedule — is already inside any sim `Δw`, which runs the real calendar. A third column double-counts one or the other. Use the weights to _explain_ a BASE↔`FPts/G` gap, never as a separate score. Reason about the profile directly only with no usable sample (rookie, tiny `GP`, role change).

**Never diff a board rank against an our-format ranking.** The boards are dynasty and any our-format ranking is one season, so the residual measures age, not format.

# Sourced vs modelled

The classification every eval must flag:

| Sourced (a market/API fact) | Modelled (we derived it) | Judgment (not a value) |
| --- | --- | --- |
| Per-board ranks, BASE's inputs | `FPts/Gp` (a sourced stat line, scored by us) | |
| `FPts/G`, `GP` (last season actual) | `GPp` (`sim.project_gp`) | `SIT` (`SIT.md`) |
| `AGE`, `POS` | `Δw` (theirs and ours) | |
| Body counts, roster limits, wire facts (trade terms, dates) | `REPL` (sim-internal) | |
| | `W20`–`W23`, `ΔP(title)` (`Bracket value.md`) | |

**`FPts/Gp` is modelled, not sourced** — the stat line under it is someone else's forecast, and both the scoring and the DD/TD estimate are ours. Cite it as a projection, never as a price.

**A sourced price and a modelled figure never bracket a range** — BASE and `Δw` are a gap to read, not an interval, and neither is a midpoint of the other. File-specific sourced facts (e.g. a particular trade's terms) are additive to this table, not a reason to re-derive it.
