# FA auction 2026

Mon 2026-09-28, live on the commissioner's Google Sheet right after the rookie draft. Rows and prices: `values.tsv` (columns and `Market$`: `Pricing.md`). Sales: `sales.tsv`.

Rules (Sheet, 2026-09-24):

- $200 per team, use-it-or-lose-it. Unspent $ is worth nothing. Auction $ can't be traded.
- $1 min bid, and every open spot must be filled: Sheet `Max Bid` = $ left − (open − 1).
- The pool is every unrostered player: the Sheet's 200-name list (sorted by '25-26 total FPts) plus the undrafted 2026 class, which is not on the list.
- No past auction to calibrate against: `Market$` is a model, and the live multiplier corrects it from the first sales.

# Plan

**Buy 3 on the Sheet's 3 open spots. Once the Duren deal lands, 2 go: Chaney Johnson, then Karlo Matković or a $1 body in his place. Drummond stays.**

- The 2.09 deal (485845) executes on draft day: +LaRavia, +Drummond, and Hlina makes the 2.09 pick. We hold no '26 picks. The Duren deal (Duren for Green, Camara and Smith, `Pending Trades.md`) lands after the draft.
- Bodies: 35 on the Sheet, 37 with the Duren deal (+2), + 3 buys = 40. Two go to get back to 38: cut, or sent to Hlina in the Duren deal, at the same cost. No cuts before the Duren deal lands.
  - A buy under Matković's 134, or a $1 body, goes instead of him.
- **Cuts** (Score, §Ours): Chaney −98, then Matković 134. Drummond (278) is next up and stays.
- **Target: the plan (§Bidding)**, the most summed Score our open spots hold. At the open that is Scheierman, Nembhard and Dru Smith: $178 for Score 713. The $22 left over is expected: they are the pool's top three Scores, unless an undrafted rookie such as De Larrea (291) joins it.
- **P(title)**, all from one sim run: 56.5% before the auction (37 bodies + 1 FA-grade pad), 57.0% with the plan and 56.5% with four $1 bodies. Swapping in Barlow for Nembhard reads 57.6%: Score takes Nembhard for his BASE (324 vs 174).

## Trades that add bodies (9/28)

- Cuts are free (no salary or dead cap; only the cut player's BASE), and the $200 is fixed. A trade that adds bodies costs no auction spots: cut down to the same open count. The Jon deal (+4 bodies) keeps 4 buys by also cutting Matković, Ellis and Huff. Those three read ≈ 0pp on the post-trade roster.
- On a deeper roster, a buy is worth less. Three stand-ins at ≈17 FPts/G and ≈70 GP read +0.8pp on the plan roster but only +0.0 to +0.5 after the Jon deal. Expect the post-trade auction to return about half the pp above.

## Targets

- **Score decides.** `score` = `Score.md` on the buy as a 1-for-1 swap for the $1 body (Justin Edwards), N = 0. A target is any row with `score` > 0 (beats the $1 body) and no `fa` (unsigned) or `noproj` flag. `dPtitle` feeds the Score and gates nothing. Every other row is a pass.
- No tie band in the auction: every Score gap counts. The card runs by Score, and caps come from Score alone (§Bidding).
- Auction $ is use-it-or-lose-it with no other use, and `AGENTS.md` weights this season like the next six, so there is no contending premium to add.
- `dPtitle` = one buy replacing a $1 floor body (Justin Edwards, PHI) on our post-485845 roster after the three cuts, at the 9/28 projections. Run at 1000 engine trials and 60k title trials over 3 seed pairs, averaged. Across the pairs, sd ≈ 0.03pp per row.
- 78 rows simmed: the top ~60 non-rookie rows by the old `Market$`, the 2026 class ranked 26–38 by BASE, and the rest of the ≥ 11 FPts/G vets.
- ΔP reads the buy's NBA schedule against ours, not just its rate: the same 9.9-rate body moved from PHI to DEN reads −0.21pp. A mid-rate body on a crowded schedule reads below the $1 body (Bagley, DEN: −0.05).
- Undrafted rookies without `noproj` are targets. Most read negative ΔP this season, but their BASE carries the Score (De Larrea 291, Quaintance 261). Thornton, Saunders, Conwell, Miller and Sharp are `noproj`: pass. The tool treats the top 36 of the class by BASE as drafted until the draft lands, so they carry no opening cap.

## Cheat card

`ΔP` = `dPtitle`. `Score`, `Market$`, `Score$` and `Gap` are `values.tsv` columns (`Pricing.md`). `Gap` = `Score$` − `Market$`: > 0 means the room underprices the row against our Score. `Cap` = opening cap from the live tool on the live Sheet (`Max$`, §Bidding). `Sheet #` = position on the Sheet's FA list.

Rows: every target, plus the top 50 of the pool by `Market$` (leaving out the 36 rookies the draft takes). **Pass** rows don't beat the $1 body (Justin Edwards, `ref`), are `fa` or `noproj`, or are unscored: never bid, but the room pays for them, so nominate them early. `Cap` `†` = the cap if that rookie alone goes undrafted; the tool sets the live cap once the draft lands.

***Bold italic*** rows are ours, priced as keep vs the $1 body (§Ours); not bid targets.

| Player | Tm | Age | BASE | ΔP | Score | Market$ | Score$ | Gap | Cap | Sheet # |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ***Jarace Walker*** | IND | 23.0 | 424 | +1.65 | 599 | – | – | – | – | – |
| ***De'Andre Hunter*** | SAC | 28.8 | 510 | +0.24 | 521 | – | – | – | – | – |
| ***Jake LaRavia*** | LAL | 24.8 | 247 | +1.55 | 477 | – | – | – | – | – |
| ***Jay Huff*** | IND | 29.0 | 372 | +0.33 | 389 | – | – | – | – | – |
| ***Adem Bona*** | PHI | 23.4 | 257 | +0.93 | 330 | – | – | – | – | – |
| ***Keon Ellis*** | BKN | 26.7 | 278 | +1.02 | 314 | – | – | – | – | – |
| Baylor Scheierman | BOS | 26.0 | 268 | +0.52 | 296 | 66 | 197 | +131 | 155 | 16 |
| Sergio De Larrea | DAL | 20.8 | 412 | −0.33 | 291 | 33 | 197 | +164 | 129† | – |
| ***Andre Drummond*** | NYK | 33.1 | 225 | +0.53 | 278 | – | – | – | – | – |
| Bruce Thornton | HOU | 23.0 | 414 | −0.32 | 272 | 32 | 196 | +164 | – | – |
| Jayden Quaintance | SAS | 19.2 | 390 | −0.33 | 261 | 30 | 188 | +158 | 78† | – |
| Koa Peat | PHX | 19.7 | 351 | −0.12 | 241 | 27 | 174 | +147 | 78† | – |
| Alex Karaban | SAC | 23.9 | 338 | −0.23 | 235 | 32 | 170 | +138 | 78† | – |
| Henri Veesaar | ATL | 22.5 | 321 | −0.14 | 223 | 27 | 161 | +134 | 78† | – |
| Ryan Nembhard | CHA | 23.5 | 324 | −0.30 | 213 | 53 | 154 | +101 | 78 | 21 |
| Dru Smith | MIA | 28.7 | 231 | +0.31 | 204 | 49 | 147 | +98 | 74 | 7 |
| Richie Saunders | MEM | 25.0 | 349 | −0.41 | 200 | 27 | 144 | +117 | – | – |
| Goga Bitadze | ORL | 27.2 | 227 | +0.12 | 191 | 58 | 138 | +80 | 0 | 8 |
| Ryan Conwell | MIA | 22.3 | 331 | −0.36 | 186 | 26 | 134 | +108 | – | – |
| Isaiah Evans | MIN | 20.8 | 325 | −0.40 | 185 | 25 | 134 | +109 | 0† | – |
| Dominick Barlow | PHI | 23.3 | 174 | +0.29 | 181 | 68 | 131 | +63 | 0 | 4 |
| Baba Miller | LAC | 22.6 | 317 | −0.38 | 178 | 24 | 129 | +105 | – | – |
| Marvin Bagley | DEN | 27.5 | 197 | −0.05 | 174 | 64 | 126 | +62 | 0 | 3 |
| Meleek Thomas | CLE | 20.1 | 246 | −0.19 | 165 | 22 | 119 | +97 | 0 | – |
| Brandon Williams | GSW | 26.8 | 205 | −0.09 | 164 | 68 | 119 | +51 | 0 | 1 |
| Quinten Post | MEM | 26.5 | 202 | −0.11 | 153 | 58 | 111 | +53 | 0 | 15 |
| Chris Cenac | BOS | 19.6 | 244 | −0.17 | 147 | 21 | 106 | +85 | 0 | – |
| ***Karlo Matković*** | NOP | 25.4 | 161 | +0.15 | 134 | – | – | – | – | – |
| Emanuel Sharp | SAC | 22.5 | 274 | −0.36 | 129 | 21 | 94 | +73 | – | – |
| Vít Krejčí | POR | 26.3 | 148 | +0.26 | 118 | 43 | 86 | +43 | 0 | 17 |
| Julian Strawther | DEN | 24.4 | 173 | −0.19 | 114 | 34 | 83 | +49 | 0 | 46 |
| Zach Collins | CHI | 28.8 | 140 | +0.21 | 110 | 26 | 80 | +54 | 0 | 136 |
| Patrick Williams | CHI | 25.1 | 151 | +0.08 | 102 | 44 | 74 | +30 | 0 | 20 |
| Harrison Barnes | SAS | 34.3 | 161 | −0.22 | 90 | 54 | 66 | +12 | 0 | 2 |
| Caleb Love | PHI | 25.0 | 188 | −0.20 | 90 | 38 | 66 | +28 | 0 | 30 |
| Cameron Payne | FA | 32.1 | 188 | −0.22 | 86 | 15 | 63 | +48 | – | 90 |
| D'Angelo Russell | MEM | 30.6 | 170 | −0.23 | 75 | 24 | 55 | +31 | 0 | 76 |
| Al Horford | GSW | 40.3 | 117 | +0.01 | 70 | 39 | 51 | +12 | 0 | 22 |
| Killian Hayes | FA | 25.2 | 184 | −0.24 | 60 | 14 | 44 | +30 | – | 96 |
| Spencer Jones | DEN | 25.3 | 149 | −0.24 | 58 | 31 | 43 | +12 | 0 | 25 |
| Jamir Watkins | WAS | 25.2 | 110 | −0.17 | 49 | 32 | 36 | +4 | 0 | 27 |
| Nae'Qwan Tomlin | CLE | 25.8 | 109 | −0.15 | 48 | 33 | 35 | +2 | 0 | 28 |
| Tyus Jones | DEN | 30.4 | 135 | −0.23 | 48 | 22 | 35 | +13 | 0 | 57 |
| Bogoljub Marković | MIL | – | 145 | −0.19 | 41 | 14 | 30 | +16 | 0 | – |
| Jaxson Hayes | UTA | 26.3 | 129 | −0.10 | 38 | 58 | 28 | −30 | 0 | 10 |
| Pat Spencer | PHX | 30.2 | 148 | −0.20 | 36 | 38 | 27 | −11 | 0 | 14 |
| Kentavious Caldwell-Pope | PHI | 33.6 | 78 | +0.09 | 27 | 35 | 20 | −15 | 0 | 29 |
| Luka Garza | BOS | 27.7 | 107 | −0.20 | 21 | 44 | 16 | −28 | 0 | 6 |
| Vince Williams | FA | 26.1 | 112 | −0.25 | 18 | 22 | 14 | −8 | – | 36 |
| Liam McNeeley | CHA | 21.0 | 126 | −0.22 | 14 | 12 | 11 | −1 | 0 | 118 |
| Matisse Thybulle | LAL | 29.6 | 23 | +0.31 | 9 | 22 | 7 | −15 | 0 | 71 |
| Guerschon Yabusele | FA | 30.8 | 122 | −0.28 | 5 | 24 | 5 | −19 | – | 32 |
| Cole Anthony | FA | 26.4 | 125 | −0.28 | 1 | 14 | 2 | −12 | – | 68 |
| ***Chaney Johnson*** | BKN | – | 0 | −0.01 | −98 | – | – | – | – | – |
| **Pass** | | | | | | | | | | |
| Simone Fontecchio | MIA | 30.8 | 55 | −0.11 | −9 | 38 | 1 | −37 | – | 11 |
| Jarred Vanderbilt | LAL | 27.5 | 66 | −0.21 | −9 | 32 | 1 | −31 | – | 23 |
| Trendon Watford | NOP | 25.9 | 66 | −0.00 | −9 | 24 | 1 | −23 | – | 41 |
| Terance Mann | BKN | 29.9 | 51 | +0.21 | −10 | 39 | 1 | −38 | – | 12 |
| Kenrich Williams | OKC | 31.8 | 32 | +0.23 | −11 | 24 | 1 | −23 | – | 35 |
| Jonas Valančiūnas | FA | 34.4 | 67 | −0.23 | −13 | 29 | 1 | −28 | – | 9 |
| Craig Porter | CLE | 26.6 | 61 | −0.18 | −19 | 32 | 1 | −31 | – | 13 |
| Nick Richards | MIA | 28.8 | 36 | +0.11 | −19 | 20 | 1 | −19 | – | 49 |
| Tre Mann | WAS | 25.6 | 65 | −0.21 | −21 | 20 | 1 | −19 | – | 64 |
| Kris Murray | MEM | 26.1 | 45 | −0.07 | −35 | 27 | 1 | −26 | – | 26 |
| Josh Okogie | UTA | 28.1 | 25 | +0.10 | −52 | 27 | 1 | −26 | – | 24 |
| Javonte Green | DET | 33.2 | 14 | −0.23 | −56 | 40 | 1 | −39 | – | 5 |
| Jaylen Clark | MIN | 25.0 | 63 | −0.38 | −59 | 22 | 1 | −21 | – | 50 |
| Jabari Walker | PHI | 24.2 | 1 | +0.02 | −61 | 20 | 1 | −19 | – | 48 |
| Rayan Rupert | PHI | 22.3 | 31 | −0.15 | −64 | 21 | 1 | −20 | – | 34 |
| Svi Mykhailiuk | UTA | 29.3 | 0 | −0.00 | −88 | 20 | 1 | −19 | – | 31 |
| Quenton Jackson | IND | 28.0 | 11 | −0.24 | −90 | 24 | 1 | −23 | – | 33 |
| John Konchar | NYK | 30.5 | 17 | −0.14 | −91 | 30 | 1 | −29 | – | 19 |
| Bryce McGowens | NOP | 23.9 | 0 | −0.05 | −92 | 20 | 1 | −19 | – | 55 |
| Clint Capela | HOU | 32.4 | 15 | −0.23 | −94 | 28 | 1 | −27 | – | 18 |
| Tyrese Martin | PHI | 27.6 | 116 | – | – | 18 | – | – | – | 58 |

## Ours

Our bottom 9 on the `dPtitle` basis, 9/28, post-485845: roster after the three cuts, one $1 body (Justin Edwards) plus FA-grade pads in the open spots. A kept row = keep vs swap to a second $1 body. A cut row (Chaney, Matković, Drummond) = add back over the $1 body. Formula `Δw` for `Score`: `Ours.team.md`.

- Cut order: Chaney (−98), then Matković (134) or a $1 body in his place. Drummond (278) stays.
- LaRavia (477, ΔP +1.55) is a keeper: his 22.8 rate is the best of our bottom bodies.

## Bidding

- **Hard max** = $ left − (spots left − 1).
- **Plan** = the unsold targets with the most summed Score that fill our spots left at live `Market$` × room heat (heat only when above 1), with $1 bodies in the rest. The Score counted is the roster after the cuts (§Plan), so a $1 body keeps Matković's 134. Re-plans after every sale.
- **Cap** on a target = the most we can pay for it and still match the plan without it: its Score + the best plan for our other spots on the $ left after paying ≥ the best plan without it. Never over hard max.
- At the open: Scheierman $155 · Nembhard $78 · Dru Smith $74 · the rest $0.
- Don't stretch a cap to beat a rich rival by $1–2. A rival who overpays for one target can't contest the next.
- **Last spot:** the cap goes to hard max on every target that outscores our lowest keeper and the best one our $ buys at live `Market$` × heat, and $0 on the rest.
- **Endgame:** once our cap on an unsold target beats every rival's `Max Bid`, nothing can outbid us. Nominate the best such row and win it.
- Never bid on a pass row, and never to push a rival's price. A stuck buy costs one of our spots.
- Leftover $ after the plan's buys is expected: the plan is the pool's top Scores, and a cold room sells them under our caps. The caps were too tight only if a target went to a rival just over our cap and we still finished with $ left.

## Nominating

Nominating opens with our $1 bid: if nobody bids, the row is ours. One nominee at a time, first match wins:

1. **Endgame** row (§Bidding).
2. **Mid:** the first unsold Mid row we still bid on, then the top-Score target we still bid on. Only once half the league's auction spots are filled, on our last spot, or when no Early row is left.
3. **Early:** the Early list in order, then the priciest unsold row we bid $0 on, by live `Market$`. Skip any row we bid on, any row under $5 live `Market$`, and unsigned (`fa`) or `noproj` rows.

Lists:

- **Early:** rows we bid $0 on (pass rows and $0-cap targets) the room pays for, in `Sheet #` order since the room prices off the list. This drains rival $ and spots. Left with us at $1, a $0-cap target costs what a $1 body does: Brandon Williams, Harrison Barnes, Marvin Bagley, Dominick Barlow, Javonte Green, Luka Garza, Goga Bitadze, Jaxson Hayes, Simone Fontecchio, Terance Mann, Craig Porter, Pat Spencer, Quinten Post, Clint Capela, John Konchar, Patrick Williams, Al Horford, Jarred Vanderbilt, Josh Okogie, Kris Murray, Caleb Love, Kenrich Williams, Trendon Watford.
- **Mid:** our targets deep on the Sheet list or off it, where the room's price trails our Score, once rivals have spent: Ryan Nembhard, Sergio De Larrea, Jayden Quaintance, Koa Peat, Alex Karaban. Henri Veesaar is off: he tore his ACL and is out for 2026–27.
- Leave the top-list targets (Dru Smith, Scheierman) for rivals to nominate. The endgame rule catches any that are left.
- Per-slot $ at the start: us $67 · Mitch $50 · Bonin, Jon, Todd $33 · Joe $25 · Chris, Brian, Henry, Josh, Hlina $22 · Matthew $15. No rival matches us per slot. Mitch comes closest: watch his $ left.

# Live

Runbook: `auction-live` Skill (`.claude/skills/auction-live/auction-live.md`).

- Log every sale in `sales.tsv` as `player  team  $`, where team is the owner's first name. Either:
  - **Agent session:** the Sheet poller appends it. The agent replies with room heat, the Score, live `Market$`, gap and cap for the unsold targets, and each team's $ left, spots left and `Max Bid`.
  - **Sheet tab:** paste `values.tsv` and `sales.tsv` as tabs, then compute the multiplier below with SUM and VLOOKUP.
- **Live multiplier** k = ($ left league-wide − spots left league-wide) ÷ Σ(`Market$` − 1) over the top (spots left) unsold rows. Live `Market$` = 1 + (`Market$` − 1) × k. Live gap = `gap` × k.
- **Room heat** = Σ(price − 1) ÷ Σ(live `Market$` just before the sale − 1) over the last 8 rival sales expected at ≥ $5. Leave out the forced fill (league spots left ≤ 2 × teams still open). Hot ≥ 1.15, cold ≤ 0.87. Above 1, it prices the rest of the plan (§Bidding).
- **Name match:** NFKD-ascii, lowercase, fold `’` to `'`, drop `Jr.`/`Sr.`/`II`/`III`. The Sheet writes Nae’Qwan Tomlin, D’Angelo Russell and Jae’Sean Tate with curly apostrophes. A typo the commissioner never fixes goes in `aliases.tsv` (`sheet  name`).
- **Open spots at start:** Matthew 13 · Chris, Brian, Henry, Josh, Hlina 9 each · Joe 8 · Bonin, Jon, Todd 6 each · Mitch 4 · us 3.
