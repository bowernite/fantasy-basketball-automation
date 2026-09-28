# FA auction 2026

Mon 2026-09-28, live on the commissioner's Google Sheet right after the rookie draft. Rows and prices: `values.tsv` (columns and `Market$`: `Pricing.md`). Sales: `sales.tsv`.

Rules (Sheet, 2026-09-24):

- $200 per team, use-it-or-lose-it. Unspent $ is worth nothing. Auction $ can't be traded.
- $1 min bid, and every open spot must be filled: Sheet `Max Bid` = $ left − (open − 1).
- The pool is every unrostered player: the Sheet's 200-name list (sorted by '25-26 total FPts) plus the undrafted 2026 class, which is not on the list.
- No past auction to calibrate against: `Market$` is a model, and the live multiplier corrects it from the first sales.

# Plan

**Buy 4 on the Sheet's 4 open spots. After the auction, cut Chaney Johnson and Karlo Matković.** Middleton went to Chris in the Fox deal (9/28, 485835, body-even), so Matković is the second cut.

- The Hlina deal (`Pending Trades.md`) lands after the auction. No cuts before it. When it lands (+2 bodies, 40), the two cuts take us back to 38.
  - If our 4th buy scores under Matković (167), cut it instead of him (`Score ranking.md`). A $1 body always does.
- **Cuts.** Chaney is the worst body on every read. Matković has the lowest Score of the bodies left (167, vs Ellis 324, Bona 355, Huff 392). Huff reads less this season (keep ΔP +0.33 vs Matković +0.59), but carries BASE 372 to Matković's 161.
- **No 5th buy.** Cutting a third body for a 5th buy (pre-Fox, Matković as the extra cut) reads −0.1 to −0.3pp against 4 buys: the kept body is worth about a Score-150 buy, and the $ spreads thinner.
- **Target: the plan (§Bidding)**, the most summed Score our open spots hold at live `Market$`. At the open that is Scheierman, Dru Smith and Barlow plus a $1 body, $195 for Score 781. P(title) 53.6% with it, 52.1% before the auction (FA-grade pads), 51.0% with four $1 bodies.
- **More open spots** (a deal lands before the auction): the tool reads the Sheet's `Open roster spots` and re-plans. At 6 spots the plan keeps the same three, plus $1 bodies.

## Trades that add bodies (9/28)

- Cuts are free (no salary or dead cap; only the cut player's BASE), and the $200 is fixed. A trade that adds bodies costs no auction spots: cut down to the same open count. The Jon deal (+4 bodies) keeps 4 buys by also cutting Matković, Ellis and Huff. Those three read ≈ 0pp on the post-trade roster.
- On a deeper roster, a buy is worth less. Three stand-ins at ≈17 FPts/G and ≈70 GP read +0.8pp on the plan roster but only +0.0 to +0.5 after the Jon deal. Expect the post-trade auction to return about half the pp above.

## Targets

- **ΔP gates, Score prices.** `score` = `Score.md` on the buy as a 1-for-1 swap for the $1 body (Justin Edwards), N = 0. A target needs `dPtitle` ≥ +0.15pp (≈ 1.5σ), whatever its Score, and `score` > 0 (beats the $1 body). Every other row is a pass.
- No tie band in the auction: every Score gap counts. The card runs by Score, and caps come from Score alone (§Bidding).
- Auction $ is use-it-or-lose-it with no other use, and `AGENTS.md` weights this season like the next six, so there is no contending premium to add.
- `dPtitle` = one buy replacing a $1 floor body (Justin Edwards, PHI) on our post-Fox roster after the cuts, at the 9/28 projections. Run at 1000 engine trials and 60k title trials over 3 seed pairs, averaged. Across the pairs, sd ≈ 0.03pp per row.
- 78 rows simmed: the top ~60 non-rookie rows by the old `Market$`, the 2026 class ranked 26–38 by BASE, and the rest of the ≥ 11 FPts/G vets.
- ΔP reads the buy's NBA schedule against ours, not just its rate: the same 9.9-rate body moved from PHI to DEN reads −0.21pp. A mid-rate body on a crowded schedule reads below the $1 body (Bagley, DEN: −0.07).
- **Vetoed by the ΔP floor** (Score, ΔP): every undrafted rookie, e.g. De Larrea (287, −0.41), Thornton (258, −0.56), Quaintance (255, −0.40), Karaban (219, −0.43), Meleek Thomas (161, −0.18), Chris Cenac (146, −0.21). Also Ryan Nembhard (207, −0.44), Goga Bitadze (179, −0.06), Marvin Bagley (173, −0.07), Brandon Williams (168, −0.11), Quinten Post (147, −0.16), Julian Strawther (113, −0.21), Zach Collins (96, +0.03), Harrison Barnes (92, −0.23), Al Horford (72, +0.01), Jaxson Hayes (44, −0.03; projection cut to 10.5 FPts/G) and Luka Garza (40, −0.03). They go on the Early list to drain rival $.

## Cheat card

`ΔP` = `dPtitle`. `Score`, `Market$`, `Score$` and `Gap` are `values.tsv` columns (`Pricing.md`). `Gap` = `Score$` − `Market$`: > 0 means the room underprices the row against our Score. `Cap` = opening cap from the live tool on the blank Sheet (`Max$`, §Bidding). `Sheet #` = position on the Sheet's FA list.

Rows: every target, plus the top 50 of the pool by `Market$` (leaving out the 36 rookies the draft takes). **Pass** rows fail the ΔP floor or don't beat the $1 body (Justin Edwards, `ref`): never bid, but the room pays for them, so nominate them early. An undrafted rookie not listed is a pass too (ΔP floor, §Targets).

***Bold italic*** rows are ours, priced as keep vs the $1 body (§Ours); not bid targets.

| Player | Tm | Age | BASE | ΔP | Score | Market$ | Score$ | Gap | Cap | Sheet # |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ***Jarace Walker*** | IND | 23.0 | 424 | +1.41 | 584 | – | – | – | – | – |
| ***De'Andre Hunter*** | SAC | 28.8 | 510 | +0.35 | 532 | – | – | – | – | – |
| ***Jay Huff*** | IND | 29.0 | 372 | +0.33 | 392 | – | – | – | – | – |
| ***Adem Bona*** | PHI | 23.4 | 257 | +1.21 | 355 | – | – | – | – | – |
| Baylor Scheierman | BOS | 26.0 | 268 | +0.87 | 332 | 66 | 197 | +131 | 124 | 16 |
| ***Keon Ellis*** | BKN | 26.7 | 278 | +1.14 | 324 | – | – | – | – | – |
| Dru Smith | MIA | 28.7 | 231 | +0.58 | 231 | 49 | 163 | +114 | 83 | 7 |
| Dominick Barlow | PHI | 23.3 | 174 | +0.73 | 218 | 68 | 154 | +86 | 77 | 4 |
| ***Karlo Matković*** | NOP | 25.4 | 161 | +0.59 | 167 | – | – | – | – | – |
| Vít Krejčí | POR | 26.3 | 148 | +0.45 | 138 | 43 | 98 | +55 | 0 | 17 |
| Kentavious Caldwell-Pope | PHI | 33.6 | 78 | +0.30 | 48 | 35 | 35 | 0 | 0 | 29 |
| Matisse Thybulle | LAL | 29.6 | 23 | +0.54 | 33 | 22 | 24 | +2 | 0 | 71 |
| Simone Fontecchio | MIA | 30.8 | 55 | +0.19 | 12 | 38 | 9 | −29 | 0 | 11 |
| ***Chaney Johnson*** | BKN | – | 0 | −0.25 | −118 | – | – | – | – | – |
| **Pass** | | | | | | | | | | |
| Ryan Nembhard | CHA | 23.5 | 324 | −0.44 | 207 | 53 | 146 | +93 | – | 21 |
| Goga Bitadze | ORL | 27.2 | 227 | −0.06 | 179 | 58 | 127 | +69 | – | 8 |
| Marvin Bagley | DEN | 27.5 | 197 | −0.07 | 173 | 64 | 122 | +58 | – | 3 |
| Brandon Williams | GSW | 26.8 | 205 | −0.11 | 168 | 68 | 119 | +51 | – | 1 |
| Meleek Thomas | CLE | 20.1 | 246 | −0.18 | 161 | 22 | 114 | +92 | – | – |
| Quinten Post | MEM | 26.5 | 202 | −0.16 | 147 | 58 | 104 | +46 | – | 15 |
| Chris Cenac | BOS | 19.6 | 244 | −0.21 | 146 | 21 | 103 | +82 | – | – |
| Julian Strawther | DEN | 24.4 | 173 | −0.21 | 113 | 34 | 80 | +46 | – | 46 |
| Zach Collins | CHI | 28.8 | 140 | +0.03 | 96 | 26 | 68 | +42 | – | 136 |
| Harrison Barnes | SAS | 34.3 | 161 | −0.23 | 92 | 54 | 66 | +12 | – | 2 |
| Patrick Williams | CHI | 25.1 | 151 | −0.10 | 88 | 44 | 63 | +19 | – | 20 |
| Caleb Love | PHI | 25.0 | 188 | −0.35 | 84 | 38 | 60 | +22 | – | 30 |
| Al Horford | GSW | 40.3 | 117 | +0.01 | 72 | 39 | 51 | +12 | – | 22 |
| Spencer Jones | DEN | 25.3 | 149 | −0.22 | 60 | 31 | 43 | +12 | – | 25 |
| D'Angelo Russell | MEM | 30.6 | 170 | −0.47 | 58 | 24 | 42 | +18 | – | 76 |
| Tyus Jones | DEN | 30.4 | 135 | −0.19 | 54 | 22 | 39 | +17 | – | 57 |
| Nae'Qwan Tomlin | CLE | 25.8 | 109 | −0.18 | 46 | 33 | 33 | 0 | – | 28 |
| Jaxson Hayes | UTA | 26.3 | 129 | −0.03 | 44 | 58 | 32 | −26 | – | 10 |
| Jamir Watkins | WAS | 25.2 | 110 | −0.28 | 41 | 32 | 30 | −2 | – | 27 |
| Luka Garza | BOS | 27.7 | 107 | −0.03 | 40 | 44 | 29 | −15 | – | 6 |
| Jarred Vanderbilt | LAL | 27.5 | 66 | +0.14 | 27 | 32 | 20 | −12 | – | 23 |
| Pat Spencer | PHX | 30.2 | 148 | −0.35 | 26 | 38 | 19 | −19 | – | 14 |
| Vince Williams | FA | 26.1 | 112 | −0.36 | 6 | 22 | 5 | −17 | – | 36 |
| Guerschon Yabusele | FA | 30.8 | 122 | −0.41 | −5 | 24 | 1 | −23 | – | 32 |
| Nick Richards | MIA | 28.8 | 36 | +0.26 | −7 | 20 | 1 | −19 | – | 49 |
| Trendon Watford | NOP | 25.9 | 66 | +0.04 | −11 | 24 | 1 | −23 | – | 41 |
| Jonas Valančiūnas | FA | 34.4 | 67 | −0.25 | −12 | 29 | 1 | −28 | – | 9 |
| Kenrich Williams | OKC | 31.8 | 32 | +0.22 | −12 | 24 | 1 | −23 | – | 35 |
| Terance Mann | BKN | 29.9 | 51 | +0.21 | −13 | 39 | 1 | −38 | – | 12 |
| Craig Porter | CLE | 26.6 | 61 | −0.18 | −16 | 32 | 1 | −31 | – | 13 |
| Tre Mann | WAS | 25.6 | 65 | −0.31 | −24 | 20 | 1 | −19 | – | 64 |
| Josh Okogie | UTA | 28.1 | 25 | +0.15 | −40 | 27 | 1 | −26 | – | 24 |
| Jabari Walker | PHI | 24.2 | 1 | +0.11 | −54 | 20 | 1 | −19 | – | 48 |
| Kris Murray | MEM | 26.1 | 45 | −0.27 | −56 | 27 | 1 | −26 | – | 26 |
| Javonte Green | DET | 33.2 | 14 | −0.27 | −57 | 40 | 1 | −39 | – | 5 |
| Jaylen Clark | MIN | 25.0 | 63 | −0.41 | −59 | 22 | 1 | −21 | – | 50 |
| Rayan Rupert | PHI | 22.3 | 31 | −0.25 | −72 | 21 | 1 | −20 | – | 34 |
| Bryce McGowens | NOP | 23.9 | 0 | −0.06 | −91 | 20 | 1 | −19 | – | 55 |
| John Konchar | NYK | 30.5 | 17 | −0.27 | −96 | 30 | 1 | −29 | – | 19 |
| Clint Capela | HOU | 32.4 | 15 | −0.31 | −101 | 28 | 1 | −27 | – | 18 |
| Quenton Jackson | IND | 28.0 | 11 | −0.45 | −102 | 24 | 1 | −23 | – | 33 |
| Svi Mykhailiuk | UTA | 29.3 | 0 | −0.14 | −102 | 20 | 1 | −19 | – | 31 |
| Justin Edwards | PHI | 22.8 | 76 | ref | ref | 22 | – | – | – | 37 |

## Ours

Our bottom 7 on the `dPtitle` basis, 9/28, post-Fox: roster after both cuts, one $1 body (Justin Edwards) plus FA-grade pads in the open spots. Kept row = keep vs swap to a second $1 body; Chaney and Matković = add back over the $1 body. Formula `Δw` for `Score`: `Ours.team.md`.

- No FA outscores Huff or Bona, and only Scheierman (332) outscores Ellis (324), so a 5th buy never beats the body it would cut. No extra cut.
- Matković (167) is the lowest-Score body left after Chaney, so he's the second cut.

## Bidding

- **Hard max** = $ left − (spots left − 1).
- **Plan** = the unsold targets with the most summed Score that fill our spots left at live `Market$`, with $1 bodies in the rest. One $1 spot counts as Matković's 167: the post-Hlina cut takes that body, not him. Re-plans after every sale.
- **Cap** on a target = the most we can pay for it and still match the plan without it: its Score + the best plan for our other spots on the $ left after paying ≥ the best plan without it. Never over hard max.
- At the open: Scheierman $124 · Dru Smith $83 · Barlow $77 · the rest $0. A 4th buy under Matković's 167 is the one cut, so it is worth nothing until we hold 2 buys or fewer of the plan's three.
- Caps assume the rest of the plan sells at live `Market$`. When room heat reads hot, the rest costs more, so caps read low.
- Don't stretch a cap to beat a rich rival by $1–2. A rival who overpays for one target can't contest the next.
- **Last spot:** the cap goes to hard max on every target that outscores Matković and the best one our $ buys at live `Market$`, and $0 on the rest.
- **Endgame:** once our cap on an unsold target beats every rival's `Max Bid`, nothing can outbid us. Nominate the best such row and win it.
- Never bid on a pass row, and never to push a rival's price. A stuck buy costs one of our spots.
- Waste check: finishing with more than ~$10 unspent means the caps were too tight.

## Nominating

Nominating opens with our $1 bid: if nobody bids, the row is ours. One nominee at a time, first match wins:

1. **Endgame** row (§Bidding).
2. **Mid:** the first unsold Mid row we still bid on, then the top-Score target we still bid on. Only once half the league's auction spots are filled, on our last spot, or when no Early row is left.
3. **Early:** the Early list in order, then the priciest unsold pass row by live `Market$`. Skip any row under $5 live `Market$`, and unsigned (`fa`) or `noproj` rows.

Lists:

- **Early:** pass rows the room pays for, in `Sheet #` order since the room prices off the list. This drains rival $ and spots: Brandon Williams, Harrison Barnes, Marvin Bagley, Javonte Green, Luka Garza, Goga Bitadze, Jaxson Hayes, Terance Mann, Pat Spencer, Quinten Post, Patrick Williams, Ryan Nembhard, Al Horford, Jarred Vanderbilt, Caleb Love, Sergio De Larrea, Bruce Thornton, Alex Karaban, Jayden Quaintance.
- **Mid:** our targets deep on the Sheet list, where the room's price trails our Score, once rivals have spent: Vít Krejčí, Kentavious Caldwell-Pope, Matisse Thybulle.
- Leave the top-list targets (Barlow, Dru Smith, Scheierman) for rivals to nominate. The endgame rule catches any that are left.
- Per-slot $ at the start: us $50 · Mitch $50 · Bonin, Jon, Todd $33 · Joe $25 · Chris, Brian, Henry, Josh $22 · Hlina $25 · Matthew $15. Mitch is the only rival who can match us per slot. Watch his $ left.

# Live

Runbook: `auction-live` Skill (`.claude/skills/auction-live/auction-live.md`).

- Log every sale in `sales.tsv` as `player  team  $`, where team is the owner's first name. Either:
  - **Agent session:** the Sheet poller appends it. The agent replies with room heat, the Score, live `Market$`, gap and cap for the unsold targets, and each team's $ left, spots left and `Max Bid`.
  - **Sheet tab:** paste `values.tsv` and `sales.tsv` as tabs, then compute the multiplier below with SUM and VLOOKUP.
- **Live multiplier** k = ($ left league-wide − spots left league-wide) ÷ Σ(`Market$` − 1) over the top (spots left) unsold rows. Live `Market$` = 1 + (`Market$` − 1) × k. Live gap = `gap` × k.
- **Room heat** = Σ(price − 1) ÷ Σ(live `Market$` just before the sale − 1) over the last 8 rival sales expected at ≥ $5. Leave out the forced fill (league spots left ≤ 2 × teams still open). Hot ≥ 1.15, cold ≤ 0.87. Advisory only: caps never use it.
- **Name match:** NFKD-ascii, lowercase, fold `’` to `'`, drop `Jr.`/`Sr.`/`II`/`III`. The Sheet writes Nae’Qwan Tomlin, D’Angelo Russell and Jae’Sean Tate with curly apostrophes. A typo the commissioner never fixes goes in `aliases.tsv` (`sheet  name`).
- **Open spots at start:** Matthew 13 · Hlina 8 · Chris, Brian, Henry, Josh 9 each · Joe 8 · Bonin, Jon, Todd 6 each · Mitch 4 · us 4.
