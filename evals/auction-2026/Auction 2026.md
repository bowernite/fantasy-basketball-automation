# FA auction 2026

Mon 2026-09-28, live on the commissioner's Google Sheet right after the rookie draft. Rows and prices: `values.tsv` (columns and `Market$`: `Pricing.md`). Sales: `sales.tsv`.

Rules (Sheet, 2026-09-24):

- $200 per team, use-it-or-lose-it. Unspent $ is worth nothing. Auction $ can't be traded.
- $1 min bid, and every open spot must be filled: Sheet `Max Bid` = $ left − (open − 1).
- The pool is every unrostered player: the Sheet's 200-name list (sorted by '25-26 total FPts) plus the undrafted 2026 class, which is not on the list.
- No past auction to calibrate against: `Market$` is a model, and the live multiplier corrects it from the first sales.

# Plan

**Buy 4 on the Sheet's 4 open spots. After the auction, cut Chaney Johnson and Khris Middleton.** Keep Matković.

- The Hlina deal (`Pending Trades.md`) lands after the auction. No cuts before it. When it lands (+2 bodies, 40), the two cuts take us back to 38.
  - If our 4th buy is a T2 or worse, cut the weaker of it and Middleton (`Score ranking.md`).
- Middleton traded for a pick before the auction leaves us 5 open. Have the commissioner hold us at 4, or buy a $1 5th body and cut it with Chaney.
- **Cuts.** Chaney is the worst body on every read. For the second cut, keeping Matković over Middleton reads +0.2 to +0.45pp across four buy sets (≈ 1.5σ each, same sign every time), and BASE is tied (161 vs 162). Huff and Ellis cut instead read the same pp, but they carry BASE 372 and 278.
- **No 5th buy.** Cutting Matković too for a 5th buy reads −0.1 to −0.3pp against 4 buys: the kept body is worth about a T2, and the $ spreads thinner.
- **Target: the plan (§Bidding)**, the most summed Score our open spots hold at live `Market$`. At the open that is 2 T1 + 2 T2: Scheierman, Hayes, Collins and Strawther, $196 for Score 836. P(title) is 44% before the auction (43% with four $1 bodies).
- **More open spots** (a deal lands before the auction): the tool reads the Sheet's `Open roster spots` and re-plans. At 6 spots the plan stays 2 T1 + 2 T2, plus two $1 bodies.

## Trades that add bodies (9/28)

- Cuts are free (no salary or dead cap; only the cut player's BASE), and the $200 is fixed. A trade that adds bodies costs no auction spots: cut down to the same open count. The Jon deal (+4 bodies) keeps 4 buys by also cutting Matković, Ellis and Huff. Those three read ≈ 0pp on the post-trade roster.
- On a deeper roster, a buy is worth less. Three T1-grade stand-ins (≈17 FPts/G at ≈70 GP) read +0.8pp on the plan roster but only +0.0 to +0.5 after the Jon deal. Expect the post-trade auction to return about half the pp above.

## Tiers

- **Score sets the tier, and ΔP gates it.** `score` = `Score.md` on the buy as a 1-for-1 swap for the $1 body (Justin Edwards), N = 0. A row needs `dPtitle` ≥ +0.15pp (≈ 1.5σ) to be tiered at all, whatever its Score: no speculative bodies that don't help this season.
- Tier bounds on `score`: T1 > 200 · T2 100–200 · T3 0–100. Blank = under the ΔP floor, or no better than a $1 body.
- Within ~250 is a tie, so tiers are coarse bins. Inside a tier, the card runs by Score.
- Auction $ is use-it-or-lose-it with no other use, and `AGENTS.md` weights this season like the next six, so there is no contending premium to add.
- `dPtitle` = one buy replacing a $1 floor body (Justin Edwards) on our roster after the cuts. Run at 1000 engine trials and 60k title trials over 3 seed pairs, averaged. Across the pairs, sd ≈ 0.1pp per row.
- 78 rows simmed: the top ~60 non-rookie rows by the old `Market$`, the 2026 class ranked 26–38 by BASE, and the rest of the ≥ 11 FPts/G vets.
- **Vetoed by the ΔP floor** (Score, ΔP): every undrafted rookie, e.g. De Larrea (284, −0.45), Thornton (261, −0.52), Quaintance (242, −0.56), Karaban (229, −0.30), Meleek Thomas (175, +0.00), Chris Cenac (164, +0.05). Also Ryan Nembhard (202, −0.49), Brandon Williams (187, +0.11), Goga Bitadze (177, −0.04), Quinten Post (169, +0.09) and Harrison Barnes (106, −0.04). They go on the Early list to drain rival $.

## Cheat card

`ΔP` = `dPtitle`. `Score`, `Market$`, `Score$` and `Gap` are `values.tsv` columns (`Pricing.md`). `Gap` = `Score$` − `Market$`: > 0 means the room underprices the row against our Score. `Cap` = opening cap from the live tool on the blank Sheet (`Max$`). `Sheet #` = position on the Sheet's FA list. ***Bold italic*** rows are ours, priced as keep vs the $1 body (§Ours); not bid targets.

| Tier | Player | Tm | Age | BASE | ΔP | Score | Market$ | Score$ | Gap | Cap | Sheet # |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | ***Jarace Walker*** | IND | 23.0 | 424 | +1.47 | 588 | – | – | – | – | – |
| 1 | ***De'Andre Hunter*** | SAC | 28.8 | 510 | +0.93 | 581 | – | – | – | – | – |
| 1 | Baylor Scheierman | BOS | 26.0 | 268 | +1.35 | 375 | 66 | 197 | +131 | 74 | 16 |
| 1 | ***Jay Huff*** | IND | 29.0 | 372 | +0.47 | 365 | – | – | – | – | – |
| 1 | ***Keon Ellis*** | BKN | 26.7 | 278 | +1.13 | 324 | – | – | – | – | – |
| 1 | ***Adem Bona*** | PHI | 23.4 | 257 | +0.76 | 322 | – | – | – | – | – |
| 1 | Dominick Barlow | PHI | 23.3 | 174 | +1.01 | 246 | 68 | 142 | +74 | 74 | 4 |
| 1 | Jaxson Hayes | UTA | 26.3 | 129 | +1.28 | 205 | 58 | 119 | +61 | 68 | 10 |
| 1 | ***Khris Middleton*** | WAS | 35.1 | 162 | +0.45 | 203 | – | – | – | – | – |
| 1 | Marvin Bagley | DEN | 27.5 | 197 | +0.29 | 201 | 64 | 116 | +52 | 74 | 3 |
| 2 | ***Karlo Matković*** | NOP | 25.4 | 161 | +0.80 | 185 | – | – | – | – | – |
| 2 | Dru Smith | MIA | 28.7 | 231 | +0.25 | 175 | 49 | 101 | +52 | 42 | 7 |
| 2 | Vít Krejčí | POR | 26.3 | 148 | +0.62 | 159 | 43 | 92 | +49 | 42 | 17 |
| 2 | Julian Strawther | DEN | 24.4 | 173 | +0.19 | 149 | 34 | 86 | +52 | 42 | 48 |
| 2 | Al Horford | GSW | 40.3 | 117 | +0.48 | 109 | 39 | 64 | +25 | 42 | 22 |
| 2 | Zach Collins | CHI | 28.8 | 140 | +0.20 | 107 | 26 | 62 | +36 | 34 | 136 |
| – | ***Chaney Johnson*** | BKN | – | 0 | +0.06 | −92 | – | – | – | – | – |

- **T3** (Score, ΔP, `Market$`, Gap), shut at the open: Luka Garza (91, +0.51, $44, +9) · Kentavious Caldwell-Pope (89, +0.60, $35, +17) · Matisse Thybulle (82, +1.07, $22, +26) · Jarred Vanderbilt (65, +0.63, $32, +6) · Terance Mann (44, +0.57, $39, −13) · Simone Fontecchio (44, +0.63, $38, −12) · Trayce Jackson-Davis (23, +0.57, $17, −3) · Nick Richards (20, +0.64, $20, −8) · Kevon Looney (16, +0.17, $14, −4) · Kenrich Williams (2, +0.40, $24, −22) · Trendon Watford (2, +0.18, $24, −22)

## Ours

Our bottom 8 on the `dPtitle` basis, 9/28: roster after both cuts, one $1 body (Justin Edwards) plus FA-grade pads in the open spots. Kept row = keep vs swap to a second $1 body; Chaney and Middleton = add back over the $1 body. Scheierman and Thybulle re-run on this basis read +1.41 and +0.96 (card +1.35, +1.07). Formula `Δw` for `Score`: `Ours.team.md`.

- Every FA except Scheierman scores below Huff, Ellis and Bona, and the top FAs sit inside their 250 tie band (`Score.md`). No extra cut.
- Middleton 203 vs Matković 185 is a Score tie. ΔP (+0.80 vs +0.45) keeps Matković.

## Bidding

- **Hard max** = $ left − (spots left − 1).
- **Plan** = the unsold T1 and T2 rows with the most summed Score that fill our spots left at live `Market$`, with $1 bodies in the rest. It sets how many T1s and T2s we hold room for, and re-plans after every sale.
- **Rest of plan** = the plan's other T1s and T2s, priced at the cheapest unsold rows of each tier, plus $1 per other spot. Leave out the row being bid on. It takes one slot of its own tier; a row the plan has no slot for takes a $1 slot, then a T2 slot, then a T1 slot.
- **Cap** = min(tier cap, $ left − rest of plan, hard max, $100 while ≥ 3 spots are open):
  - T1: no tier cap.
  - T2: 1.25 × live `Market$`.
  - T3: live `Market$`, and only once the unsold T2s are fewer than our spots left beyond the plan's T1s. Until then, no bid.
- At the open: Scheierman, Barlow and Bagley $74 · Hayes $68 · Dru Smith, Krejčí, Strawther and Horford $42 · Collins $34.
- Don't stretch a T1 cap to beat a rich rival by $1–2. A rival who overpays for one T1 can't contest the next.
- **Last spot:** cap = hard max on the rows of the best tier still unsold. Lower tiers keep their tier cap, and T3 stays shut.
- **Endgame:** once our cap on an unsold tiered row beats every rival's `Max Bid`, nothing can outbid us. Nominate the best such row and win it.
- Never bid on an untiered row, and never to push a rival's price. A stuck buy costs one of our spots.
- Waste check: finishing with more than ~$10 unspent means the caps were too tight.

## Nominating

One nominee at a time, first match wins:

1. **Endgame** row (§Bidding).
2. **Mid:** the first unsold Mid row we still bid on, once half the league's auction spots are filled.
3. **Early:** the Early list in order, then the priciest unsold untiered row by live `Market$`.

Lists:

- **Early:** untiered names the room pays for, in `Sheet #` order since the room prices off the list. This drains rival $ and spots: Brandon Williams, Harrison Barnes, Javonte Green, Goga Bitadze, Pat Spencer, Quinten Post, Patrick Williams, Ryan Nembhard, Caleb Love, Sergio De Larrea, Bruce Thornton, Alex Karaban, Jayden Quaintance.
- **Mid:** our tiered rows deep on the Sheet list, where the room's price trails our Score, once rivals have spent: Julian Strawther, Zach Collins, Matisse Thybulle, Nick Richards, Trayce Jackson-Davis.
- Leave the top-list T1s (Bagley, Barlow, Hayes, Scheierman) for rivals to nominate. The endgame rule catches any that are left.
- Per-slot $ at the start: us $50 · Mitch $50 · Bonin, Jon, Todd $33 · Joe $25 · Chris, Brian, Henry, Josh $22 · Hlina $25 · Matthew $15. Mitch is the only rival who can match us per slot. Watch his $ left.

# Live

Runbook: `auction-live` Skill (`.claude/skills/auction-live/auction-live.md`).

- Log every sale in `sales.tsv` as `player  team  $`, where team is the owner's first name. Either:
  - **Agent session:** say "sold Hayes Chris 12", or let the Sheet poller append. The agent replies with room heat, the Score, live `Market$`, gap and cap for the unsold tiered rows, and each team's $ left, spots left and `Max Bid`.
  - **Sheet tab:** paste `values.tsv` and `sales.tsv` as tabs, then compute the multiplier below with SUM and VLOOKUP.
- **Live multiplier** k = ($ left league-wide − spots left league-wide) ÷ Σ(`Market$` − 1) over the top (spots left) unsold rows. Live `Market$` = 1 + (`Market$` − 1) × k. Live gap = `gap` × k.
- **Room heat** = Σ(price − 1) ÷ Σ(live `Market$` just before the sale − 1) over the last 8 rival sales expected at ≥ $5. Leave out the forced fill (league spots left ≤ 2 × teams still open). Hot ≥ 1.15, cold ≤ 0.87. Advisory only: caps never use it.
- **Name match:** NFKD-ascii, lowercase, fold `’` to `'`, drop `Jr.`/`Sr.`/`II`/`III`. The Sheet writes Nae’Qwan Tomlin, D’Angelo Russell and Jae’Sean Tate with curly apostrophes. A typo the commissioner never fixes goes in `aliases.tsv` (`sheet  name`).
- **Open spots at start:** Matthew 13 · Hlina 8 · Chris, Brian, Henry, Josh 9 each · Joe 8 · Bonin, Jon, Todd 6 each · Mitch 4 · us 4.
