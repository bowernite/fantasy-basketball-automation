# Future picks — pricing a class no chart covers

Load when a deal involves a pick from any draft but the next one. `SKILL.md` owns slot resolution and the ordinal (§1–§3) and is a prerequisite.

**VALUE = that draft year's market, never the current class.** One rule for every future pick in a deal or eval — ours and theirs, In and Out.

# Procedure, any year

1. **Year and slot** (`SKILL.md` §1, §2). `<YEAR>` = the draft held that September, `FetchLeagueDraftBoard?season=<YEAR>`, set by the **preceding** season's finish.
2. **Market rows for `<YEAR>`**, each rank → `Eval Definitions §BASE` curve. Rank sourced, conversion modelled.
   - **Hashtag crowd `/keeper`** pick band containing the ordinal, only when its pick rows price `<YEAR>`'s class (they roll to the next class once the NBA draft passes). Convergence notice → drop it (`SKILL.md` §4).
   - **`dynatyze` pick board**, year × slot → implied dynasty rank. Weight each cell by its trade weight `w`; **`w = 0` = template, no market.** Near-year 1sts are usually anchored; later years and 2nds usually are not. Say which.
   - **4th round: Dynatyze R4 cell alone**, even at `w = 0` (label it template; step 3 doesn't apply). No crowd band (`SKILL.md` §4). Cap at the same year's 3.12 (`SKILL.md` §4); rank past `D` = 0.
   - **League comps**: `FetchTrades` history, same round and years-out, priced at today's BASE. Cross-check only — few per cell.
3. **No market in the cell** (no crowd row, `w = 0`): take the nearest priced year's value for the same slot, move it by the per-year gap that market shows for that round, label it modelled.
4. **Current-class slot value** (`SKILL.md` §4 lookup): cross-check only, never the VALUE. Future 1sts price below the same current slot, the gap widening per year out. A future row well above its current-class slot needs a named reason.
5. **Class-strength dial — check the stamp.** Neutral is not a judgment of average. Boards move after the summer circuit, again once the college season resolves. **A stale neutral dial is missing information.**
6. **Scouting cross-check, top slot only.** "This class's 1.01 grades ~Nth on last year's board" anchors the top. **Below it you are extrapolating — bear case, not estimate.**
7. **Evaluator spread** where published. High/Low per player measures slot differentiation, which the curve assumes and never checks. Overlapping consecutive ranges → the curve's gap is too wide.

# Publish

Band + central. The pick table's **VALUE** is the central; the band goes in prose or the `Notes:` line. The board-row / `rookie` cell names the market rows used (e.g. `Dynatyze '27 1.12 · crowd Pick 9–14`), never a current-class player. Where the band straddles a decision's break-even, **report the tie**.

# Traps

- **A prior is not its mode.** `V()` is convex, so a range-only slot is worth **more** than its modal slot as a point — asymmetric, favouring whoever holds the wide-range pick. Carry named and unsized.
- **No holder discount** (`SKILL.md` §*A pick has no production dimension in year 1*).

`dynatyze` is reference-only for players (`Eval Definitions §BASE`); future picks are the single standing exception.
