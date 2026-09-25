# FA auction 2026 — pricing

How `values.tsv` prices a row. The plan and card: `Auction 2026.md`. `Market$` models what the room pays; it is not a win↔$ exchange rate (`Eval Definitions` has none).

# Market$

| Param | Value |
|---|---|
| `N`, spots league-wide (us 4, Hlina 10) | 93 |
| `pool$` = $2,400 − $1 × N | $2,307 |
| Undrafted 2026 class assumed | every rookie outside the top 36 by BASE |

`Market$` models a room that shops three ways and spends every dollar:

- `Market$` = $1 + `pool$` × mean(Win share, Sheet share, Board share), capped at $197
  - Win share = max(0, formula `Δw` − 0.02) ÷ Σ over the top N. Unsigned (`fa`) and `noproj` rows get 0.
  - Sheet share = max(0, `sheet_pts` − 340) ÷ Σ over the top N. Off-list rows (the 2026 class, 35 others) get 0.
  - Board share = max(0, BASE − 25) ÷ Σ over the top N.
  - Each replacement level is the mean of ranks N+1..N+3 on that metric. Rookies assumed drafted are left out of it.
- `Win$`, `Sheet$`, `Board$` are each share × `pool$`. Where they split, the room splits: Sheet-list top names draw list-shoppers, and off-list youth draws only those who prepared. `Board$` ≫ `Market$` (young, low rate): expect dynasty readers to overpay.
- A top row's real price is set by the 2nd-highest rival `Max Bid`, not by `Market$`.
- Live repricing: the live multiplier k (`Auction 2026.md` §Live).

# Other columns

- `dPtitle`: `ΔP(title) ours` in pp, one buy replacing a $1 floor body (Justin Edwards) on our post-auction roster. Method: `Auction 2026.md` §Tiers. Blank = not simmed: drafted-class rookies, unsigned, `noproj` vets, rows under ~11 FPts/G.
- `tier`: `1`, `2`, `3`, `Y` or blank, from `dPtitle` (`Auction 2026.md` §Tiers).
- `Max$`: our opening cap on a tiered row at k = 1 (`Auction 2026.md` §Bidding). Blank on T3, which is shut at the open. The live cap moves with every sale.
- `Δw '26–'27 ours`: `Δw (season)` against `REPL` (~24–25 rate), so FA rows mostly print negative.
- `noproj` rows run on last season's rate, often over a handful of games (Alondes Williams 26.1 on 16 GP → formula `Δw` 0.37). Read them on BASE and `sheet_pts`.
- Flags come from `simlib/gp.py` plus the roster row: `frag` (pool GP in the fragment band), `miss` (gap in pool seasons), `rotN` (only N < 3 pool seasons at rotation rate), `nopool`, `GPp<map` (this-season absence), `fa` (unsigned, 0 games in the season sim), `noproj`, `unlisted` (not in `Free Agents.md`), `'25 rookie`, `'26 class`.
