# FA auction 2026

Mon 2026-09-28, live on the commissioner's Google Sheet right after the rookie draft. Prices live in `values.tsv`, sales go in `sales.tsv`. `Market$` and `Max$` are auction prices, not eval columns (`Eval Definitions` has no exchange rate between wins and $).

Rules (Sheet, 2026-09-24):

- $200 per team, use-it-or-lose-it. Unspent $ is worth nothing.
- $1 min bid, and every open spot must be filled: Sheet `Max Bid` = $ left − (open − 1).
- The pool is every unrostered player: the Sheet's 200-name list (sorted by '25-26 total FPts) plus the undrafted 2026 class, which is not on the list.

# Pricing

| Param | Value |
|---|---|
| `N`, spots league-wide (us 4, Hlina 10) | 93 |
| `pool$` = $2,400 − $1 × N | $2,307 |
| Undrafted 2026 class assumed | every rookie outside the top 36 by BASE |

`Market$` models a room that shops three ways and spends every dollar:

- `Market$` = $1 + `pool$` × mean(Win share, Sheet share, Board share), capped at $197
  - Win share = max(0, formula `Δw` − 0.03) ÷ Σ over the top N. Unsigned (`fa`) and `noproj` rows get 0.
  - Sheet share = max(0, `sheet_pts` − 340) ÷ Σ over the top N. Off-list rows (the 2026 class, 35 others) get 0.
  - Board share = max(0, BASE − 25) ÷ Σ over the top N.
  - Each replacement level is the mean of ranks N+1..N+3 on that metric.
- `Win$`, `Sheet$`, `Board$` are each share × `pool$`. Where they split, the room splits: the Sheet's top names (B. Williams, Barnes, Javonte Green, Garza) draw list-shoppers, and off-list youth draws only those who prepared.
- `Max$` = Brett's opening cap for card rows only: 1.5 × `Market$`, max $197.
- `noproj` rows run on last season's rate, often over a handful of games (Alondes Williams 26.1 on 16 GP → formula `Δw` 0.37). Read them on BASE and `sheet_pts`.
- 2026-class rows that get drafted Monday: delete them from `values.tsv` before the auction.
- Flags come from `simlib/gp.py` plus the roster row: `frag` (pool GP in the fragment band), `miss` (gap in pool seasons), `rotN` (only N < 3 pool seasons at rotation rate), `nopool`, `GPp<map` (this-season absence), `fa` (unsigned), `noproj`, `unlisted` (not in `Free Agents.md`), `'25 rookie`, `'26 class`.

**Read:** the best FA is worth ~0.1 wins to us over a $1 body, the decision floor (`Eval Definitions §σ`). No buy moves this season's title odds. The auction only turns free $ into bodies that beat our worst ones, with a small youth tail. So buy volume, rank by wins in 0.1-win bands, and let BASE break ties inside a band.

# Plan

**Buy 4.** Our 2 open spots plus 2 cuts: Chaney Johnson (BASE 0, ours −0.16) and Karlo Matković (BASE 161, −0.09). Each is beaten on both wins and BASE by every card vet.

- Cut both on Fleaflicker before the auction, and have the commissioner show us at 4 open (`Max Bid` 197). The Sheet already shows 4 because it predates the Hlina/Duren trade. Either way we end at 4 buys with Chaney and Matković gone.
  - If the commissioner applies the trade and won't take the cuts (2 open), buy card rows 1–4 only and bid the whole budget on the last slot.
- Keep Middleton, Ellis, Huff and Bona. A swap for any of them gains less than the card-vet edge over Matković, and each extra slot thins $ per slot toward the rivals'.
- Slots 1–3 go to card vets. Slot 4 goes to the best youth left (an undrafted rookie with BASE ≥ 240, or Nembhard) if it's there, otherwise another card vet.

## Cheat card

Vets are tied on wins (−0.06 to +0.01), so they are ordered by BASE.

| # | Player | Tm | Age | BASE | Sheet # | Market$ | Max$ | Note |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | Baylor Scheierman | BOS | 26.0 | 268 | 16 | 73 | 110 | best on wins and BASE |
| 2 | Brandon Williams | GSW | 26.8 | 205 | 1 | 65 | 98 | top of the list; the room will chase him |
| 3 | Marvin Bagley | DEN | 27.5 | 197 | 3 | 63 | 94 | |
| 4 | Dominick Barlow | PHI | 23.3 | 174 | 4 | 69 | 104 | youngest vet |
| 5 | Julian Strawther | DEN | 24.4 | 173 | 46 | 38 | 57 | low on the list; value |
| 6 | Vít Krejčí | POR | 26.3 | 148 | 17 | 43 | 64 | |
| 7 | Tyus Jones | DEN | 30.4 | 135 | 57 | 23 | 34 | low on the list; value |
| 8 | Nae'Qwan Tomlin | CLE | 25.8 | 109 | 28 | 33 | 50 | |
| Y | Meleek Thomas | CLE | 20.1 | 246 | — | 30 | 45 | slot 4 if undrafted (ours −0.09) |
| Y | Ryan Nembhard | CHA | 23.5 | 324 | 21 | 57 | 86 | slot 4 (ours −0.17) |
| Y | best undrafted rookie | | | ≥ 240 | — | | | slot 4; watch Karaban 338, Conwell 331, Veesaar 321 (ACL), Sharp 274 |

`Sheet #` = position on the Sheet's FA list.

## Bidding

- **Hard max** = $ left − (spots left − 1).
- **Cap** on a card row = 1.5 × live `Market$`, never above hard max. Below the cap, bid whenever a card row is up. Don't chase past it: the next card row is within noise.
- **Last spot:** the cap is the hard max. Wait for the best card row left, then spend everything.
- **Endgame:** once our hard max beats every rival's `Max Bid`, nothing can outbid us. Nominate the best card row left and win it.
- Never bid on a non-card row until the last spot, and never to push a rival's price. A stuck buy costs one of our 4 spots.
- If the card runs dry, extend it down `values.tsv` by `Δw '26–'27 ours` in 0.1-win bands, then BASE.
- Waste check: finishing with more than ~$10 unspent means the caps were too tight.

## Nominating

- **Early:** list names the room will pay for and we don't want. This drains rival $ and fills rival spots, which is our competition for card rows. In order: Harrison Barnes, Javonte Green, Luka Garza, Jonas Valančiūnas (unsigned), Jaxson Hayes, Quinten Post, Simone Fontecchio, Terance Mann, Craig Porter, Pat Spencer, Clint Capela, John Konchar.
- **Mid:** card rows the room rates low: Strawther, Tyus Jones, Tomlin. Rivals shop the list top-down.
- **Last:** off-list youth (undrafted rookies) at $1, once most rivals are down to 0–1 spots.
- Per-slot $ at the start: us $50 · Mitch $50 · Bonin, Jon, Todd $33 · Joe $25 · Chris, Brian, Henry, Josh $22 · Hlina $20 · Matthew $15. Mitch is the only rival who can match us per slot. Watch his $ left.

# Live

- Log every sale in `sales.tsv` as `player  team  $`, where team is the owner's first name. Either:
  - **Agent session:** say "sold Hayes Chris 12", or let the Sheet poller append. The agent replies with the live multiplier, live `Market$` and cap for the unsold card rows, and each team's $ left, spots left and `Max Bid`.
  - **Sheet tab:** paste `values.tsv` and `sales.tsv` as tabs, then compute the multiplier below with SUM and VLOOKUP.
- **Live multiplier** k = ($ left league-wide − spots left league-wide) ÷ Σ(`Market$` − 1) over the top (spots left) unsold rows. Live `Market$` = 1 + (`Market$` − 1) × k.
- **Name match:** NFKD-ascii, lowercase, fold `’` to `'`, drop `Jr.`/`Sr.`/`II`/`III`. The Sheet writes Nae’Qwan Tomlin, D’Angelo Russell and Jae’Sean Tate with curly apostrophes.
- **Open spots at start:** Matthew 13 · Hlina 10 · Chris, Brian, Henry, Josh 9 each · Joe 8 · Bonin, Jon, Todd 6 each · Mitch 4 · us 4.
