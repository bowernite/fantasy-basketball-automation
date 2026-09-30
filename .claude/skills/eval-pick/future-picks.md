# Future picks: pricing a class no chart covers

Load for a pick in any draft after the current class (`SKILL.md` §*A chart prices ONE class*). Prerequisite: `SKILL.md` §1–§3 (which draft, slot, ordinal).

**VALUE = that draft year's market, never the current class.** One rule for every future pick in a deal or eval: ours and theirs, In and Out.

# Procedure, any year

1. **Year and slot** (`SKILL.md` §1, §2). `<YEAR>` = the draft held that September, `FetchLeagueDraftBoard?season=<YEAR>`, set by the **preceding** season's finish. The draft the current season sets: slot per `SKILL.md` §2. Every later draft: the **original owner's** band in `sim.py future`'s *Own-pick slot band* table (`sims` §Future seasons), same band every round.
2. **VALUE: run `pick_prices.py`** (this directory) and copy the cell, or the range row for a slot range; never compute a price by hand. Pass every range the eval uses, tagged with its draft (`pick_prices.py 27:1.05-1.11 28:1.03-1.09`). Re-cut stale snapshots first (`dynatyze`, `hashtag-basketball`). The rule it applies, identical for every year and round:
   - **Dynatyze** pick board cell (year × slot, `strategy/board-snapshots/dynatyze/`) → implied rank → `Eval Definitions §BASE` curve. Dynatyze is reference-only for players; future picks are its single standing exception.
   - **`w` is a label, never a weight**: `w > 0` = market-anchored, `w = 0` = template. Say which.
   - **Hashtag crowd `/keeper`** band containing the ordinal: averaged 50/50 in `V` with the Dynatyze value only when its pick rows name `<YEAR>`'s class, the band spans ≤ 12 picks, and the pick is not a 4th. Wider bands, other years and convergence-notice pulls: cross-check only.
   - **Cap**: no pick above an earlier ordinal of the same draft (`SKILL.md` §4); rank past `D` = 0.
   - **Slot range**: uniform mean of its slots' VALUEs.
   - Every cell prices off its own year's row and round.
3. **League comps**: `FetchTrades` history, same round and years-out, priced at today's BASE. Cross-check only (few per cell).
4. **Current-class slot value** (`SKILL.md` §4 lookup): cross-check only, never the VALUE. Future 1sts price below the same current slot, the gap widening per year out. A future row well above its current-class slot needs a named reason.
5. **Class-strength dial: check the stamp.** Neutral is not a judgment of average. Boards move after the summer circuit, and again once the college season resolves; **a stale neutral dial is missing information.**
   - **Top-of-class nudge, next class only, our ordinals 1–3 only.** Label that class's top strong / average / weak off ≥3 dated outlets (ESPN, Tankathon, SI or B/R, Dizzle), then read those slots +5% / 0 / −5 to −10% off their VALUE. Later classes and ordinals ≥4 stay neutral. Read (2026-09): 2027 weak, 2028 neutral.
   - **Where a market already moved the class**, the nudge is a cross-check only: a source pricing the top >10% off neutral is likely over-reacting.
   - Re-read the label Jan–Mar. The nudge informs trade judgment (buy/sell, tie calls) only; VALUE stays the market's.
6. **Scouting cross-check, top slot only.** "This class's 1.01 grades ~Nth on last year's board" anchors the top. **Below it you are extrapolating: bear case, not estimate.**
7. **Evaluator spread** where published. High/Low per player measures slot differentiation, which the curve assumes and never checks. Overlapping consecutive ranges → the curve's gap is too wide.

Done when every future pick in the deal or eval has a `pick_prices.py` VALUE and band, with each cross-check (3–7) either noted or marked unavailable.

# Publish

Band + central. The pick table's **VALUE** is the central; the band goes in prose or the `Notes:` line. The board-row / `rookie` cell names the market rows used (e.g. `Dynatyze '27 1.12 · crowd Pick 9–14`), never a current-class player. Where the band straddles a decision's break-even, **report the tie**.

# Traps

- **A prior is not its mode.** `V()` is convex, so a range-only slot is worth **more** than its modal slot as a point: asymmetric, favouring whoever holds the wide-range pick. Carry named and unsized.
- **No holder discount** (`SKILL.md` §*A pick has no production dimension in year 1*).
