# FA auction 2026

Mon 2026-09-28, after the rookie draft. Prices live in `values.tsv`, sales go in `sales.tsv`. `Market$` and `Max$` are auction prices, not eval columns (`Eval Definitions` has no exchange rate between wins and $).

Assumed until confirmed on the day:

- **Budget:** the season's $100 FAAB (`waiverAcquisitionBudget`). Anything unspent pays for in-season waivers. If the Sheet runs its own use-it-or-lose-it budget, go to §Separate budget.
- **Min bid:** $0. No rule says you have to fill your slots.
- **Format:** live nominations on the Sheet. If it turns out to be blind claims like Oct '25, go to §Blind bids.

# Pricing

| Param | Value |
|---|---|
| `N`, spots league-wide | 91 |
| `R` = mean formula `Δw` of ranks N+1..N+3 | 0.03 |
| `pool$` (seed) | $300, 25% of $1,200 |
| `λ` = pool$ / Σ VOR | $84 per win |
| Brett floor = best `Δw '26–'27 ours` at Market$ ≤ $1 (Spencer Jones) | −0.09 |

- `VOR` = max(0, `Δw` − R)
- `Market$` = λ × VOR, rounded
  - Unsigned (`fa`) rows are priced at $0: formula `Δw` assumes they sign.
- `Max$` = λ × (ours − floor). It prices our own-team wins at the room's $/win. It is only filled for rows above the floor, and it is fixed: no live scaling.
- The $300 seed is a guess. The room holds FAAB back: Oct '25 went 19 of 20 claims at $0, and the in-season median was $13. `R` barely moves for any `N` from 75 to 91.
- `ΔP(title) ours` is noise at this size (−1.4% to +0.7%, not monotonic), so it is ignored.
- Flags, from `simlib/gp.py` plus the roster row:
  - `frag`: pool GP in the fragment band
  - `miss`: a gap in pool seasons
  - `rotN`: only N (<3) pool seasons at rotation rate
  - `nopool`: no pool history
  - `GPp<map`: GPp under the durability map, i.e. a this-season absence
  - `fa`: unsigned
  - `unlisted`: not in `Free Agents.md`
  - `'25 rookie`: last year's draft class

**Read:** the best FA is worth +0.10 wins to us over a free body, which is the decision floor (`Eval Definitions §σ`). Nothing here justifies an overpay. BASE breaks ties.

In-season $ only counts against the richest rival's $ left, because the top bid wins. With the league at 456/456 bodies, the in-season wire is thin: few breakouts, but each one is contested. Last season's top bids were $98 and $100.

# Plan

- **Buy 3:** the 2 open slots, plus cut Chaney Johnson (BASE 0, off every board, ours −0.16) when the 3rd buy lands.
  - Slots 1–2 go to card vets.
  - Slot 3 goes to the best youth at $0–1: the best undrafted 2026 rookie (from `Rookie Draft 2026.md`) or Nembhard, if BASE is about 250 or more. Otherwise take Tyus Jones or Tomlin.
  - Why: a vet in slot 3 adds 0.03 wins or less over the floor, while the objective pays for a multi-year tail.
- **Reserve is relative:** after each buy, your $ left should be at least the richest rival's $ left. Buying targets late shows you the rival balances before you spend.
  - Exception: take a card row at $3 or less even if it drops you just under one rival.
  - Hard cap: $20 in total.
- Never bid above `Max$`. It stays fixed when the room overspends, because your leftover $ gets relatively stronger.
- Let the room spend first. Early on, nominate players you don't want to drain rival budgets: Hayes, Post, Bitadze, Collins, Thybulle, and the unsigned names (Paul, Clarke, Valančiūnas).
- Nominate your own targets late, once rivals' $ and slots have thinned.
- If Hlina/Duren hasn't executed by then, hold 2 slots free for it (`Pending Trades.md`).

## Cheat card

Ordered by BASE. Wins are tied within the decision floor.

| # | Player | Tm | Age | BASE | Market$ | Max$ | Note |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | Baylor Scheierman | BOS | 26.0 | 268 | 14 | 8 | the room likely takes him |
| 2 | Brandon Williams | GSW | 26.8 | 205 | 9 | 6 | |
| 3 | Marvin Bagley | DEN | 27.5 | 197 | 10 | 8 | |
| 4 | Dominick Barlow | PHI | 23.3 | 174 | 14 | 6 | youngest; the room likely takes him |
| 5 | Julian Strawther | DEN | 24.4 | 173 | 6 | 6 | likely buy |
| 6 | Vít Krejčí | POR | 26.3 | 148 | 6 | 6 | likely buy |
| 7 | Tyus Jones | DEN | 30.4 | 135 | 2 | 3 | likely buy |
| 8 | Nae'Qwan Tomlin | CLE | 25.8 | 109 | 5 | 3 | |
| — | Spencer Jones | DEN | 25.3 | 149 | 1 | 0 | free fallback, $0–1 |
| — | Ryan Nembhard | CHA | 23.5 | 324 | 4 | 1 | slot-3 youth (ours −0.17), $0–1 |
| — | best undrafted 2026 rookie | | | ~250–350 | — | 1 | slot-3 youth, $0–1 |

Undrafted rookies after 36 picks:

- By chalk, what's left starts around rookie-board #37: Meleek Thomas 246, Chris Cenac Jr. 244.
- Watch for fallers: Saunders 349 (ACL, likely out '26-27), Karaban 338, Conwell 331.
- Rookie BASE uses the Sep 14 Hashtag board, while `values.tsv` uses Aug 25. Treat a gap under 100 BASE as a tie.

**Stop** once you have 3 bodies, or once your next buy would take you below the richest rival's $ left or over $20.

# Live

- Log every sale in `sales.tsv` as `player  team  $`, where team is the owner's first name. Either:
  - **Agent session:** say "sold Hayes Chris 12". The agent appends the row and replies with the scale, live `Market$` for the unsold card rows, each team's $ left and slots left, and the richest rival's $ left.
  - **Sheet tab:** paste `values.tsv` and `sales.tsv` as tabs. Scale = `SUM(sales $) / SUM(Market$ of sold rows)`, via VLOOKUP. Live `Market$` = column × scale.
- **Scale:** Σ paid ÷ Σ `Market$` over sold rows with `Market$` > 0. Use it once 5 or more have sold. Only `Market$` scales. `Max$` and the $20 cap stay fixed.
- **Rival max bid** = that team's $ left.
- **Open slots** (who is hungry):
  - Matthew 13 · Hlina 10
  - Chris, Brian, Henry, Josh 9 each · Joe 8
  - Bonin, Jon, Todd 6 each · Mitch 4 · us 2

# Separate budget

If the Sheet $ doesn't carry into the season, it is worth nothing afterwards, so spend it.

- If all $1,200 goes, expect about 4× the column (λ ≈ $337).
- Ceiling for a target = $ left − live `Market$` of the other planned buys. Overpaying on #1 costs nothing.
- Also cut Karlo Matković (BASE 161, ours −0.09 = floor), for 4 buys.
- The reserve rule and the $20 cap don't apply.

# Blind bids

Sealed claims, and you pay your own bid. $1–3 beats the room's usual $0.

| Player | Bid |
|---|---:|
| Scheierman, Bagley | 4 |
| B. Williams, Barlow, Strawther, Krejčí | 3 |
| Tyus Jones | 2 |
| Tomlin, Spencer Jones, best undrafted rookie, Nembhard | 1 |

- Put the claims in card order. Put the slot-3 youth claim third.
- Attach "drop Chaney Johnson" to claim #1. At most 3 claims can land.
- Rival balances can't be seen here, so keep the total at $20 or less.

# Cuts

- **Chaney Johnson:** cut for any 3rd buy.
- **Matković:** cut only in §Separate budget, or for a card row that falls to $1 or less.
- **Keep:**
  - Sharpe and Mark Williams (out long-term, BASE 1036 and 1350)
  - Middleton, Ellis and Huff: an FA upgrade over them is worth less than the 0.1-win decision floor and costs $.
