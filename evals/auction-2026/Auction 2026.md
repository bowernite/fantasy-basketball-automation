# FA auction 2026

Mon 2026-09-28, live on the commissioner's Google Sheet right after the rookie draft. Rows and prices: `values.tsv` (columns and `Market$`: `Pricing.md`). Sales: `sales.tsv`.

Rules (Sheet, 2026-09-24):

- $200 per team, use-it-or-lose-it. Unspent $ is worth nothing. Auction $ can't be traded.
- $1 min bid, and every open spot must be filled: Sheet `Max Bid` = $ left − (open − 1).
- The pool is every unrostered player: the Sheet's 200-name list (sorted by '25-26 total FPts) plus the undrafted 2026 class, which is not on the list.
- No past auction to calibrate against: `Market$` is a model, and the live multiplier corrects it from the first sales.

# Plan

**Buy 4: our 2 open spots, plus cut Chaney Johnson and Khris Middleton.** Keep Matković.

- The Hlina deal (`Pending Trades.md`) lands after the rookie draft. Until it does, the Sheet shows us at 4 open (`Max Bid` 197) with no cuts. When it lands (+2 bodies), cut both on Fleaflicker: before the auction, have the commissioner keep us at 4 open; after it, the cuts take us back to 38.
  - If he holds us to 2 open, buy 2 T1 and treat the 2nd as the last spot.
- **Cuts.** Chaney is the worst body on every read. For the second cut, keeping Matković over Middleton reads +0.2 to +0.45pp across four buy sets (≈ 1.5σ each, same sign every time), and BASE is tied (161 vs 162). Huff and Ellis cut instead read the same pp, but they carry BASE 372 and 278.
- **No 5th buy.** Cutting Matković too for a 5th buy reads −0.1 to −0.3pp against 4 buys: the kept body is worth about a T2, and the $ spreads thinner.
- **Target: 3 T1 + 1 T2**, and a 4th T1 if its price fits. P(title) is 44% before the auction (43% with four $1 bodies). Joint sims, pp over four $1 bodies:

| Set | ΔP(title) |
|---|---:|
| 4 T1 | +4.1 |
| 3 T1 + T2 | +3.5 to +3.8 |
| 3 T1 + Y | +3.3 to +3.5 |
| 2 T1 + 2 T2 | +3.1 to +3.5 |
| 4 T2 | +2.2 to +2.3 |

## Trades that add bodies (9/28)

- Cuts are free (no salary or dead cap; only the cut player's BASE), and the $200 is fixed. A trade that adds bodies costs no auction spots: cut down to the same open count. The Jon deal (+4 bodies) keeps 4 buys by also cutting Matković, Ellis and Huff. Those three read ≈ 0pp on the post-trade roster.
- On a deeper roster, a buy is worth less. Three T1-grade stand-ins (≈17 FPts/G at ≈70 GP) read +0.8pp on the plan roster but only +0.0 to +0.5 after the Jon deal. Expect the post-trade auction to return about half the pp above.

## Tiers

- **Rank by `tier`, then BASE inside a tier.** `Δw (season)` for every candidate sits within ±0.15 of a $1 body, under the 0.1-win decision floor, so it can't order them. `ΔP(title) ours` does: it tracks W20–W23 playoff-week output, and at this precision the tiers separate.
- **Why ΔP drives the auction:** BASE (23–340) and `Δw (season)` tie at decision resolution, so the equal-weight rule lands on ΔP. `Δw (season)` can only veto. Don't carry this into trades.
- Auction $ is use-it-or-lose-it with no other use, and `AGENTS.md` weights this season like the next six, so there is no contending premium to add.
- `dPtitle` = one buy replacing a $1 floor body (Justin Edwards) on our roster after the cuts. Run at 1000 engine trials and 60k title trials over 3 seed pairs, averaged. Across the pairs, sd ≈ 0.1pp per row.
- `score` (`Pricing.md`) rides beside the tiers and does not set them. Ranked with our bottom 8: `Score ranking.md`.
- Tier bounds: T1 ≥ +0.9pp · T2 +0.35 to +0.9 · T3 +0.15 to +0.35 · Y = 2026-class or '25 rookies at ≥ −0.15. Blank = no better than a $1 body.
- 78 rows simmed: the top ~60 non-rookie rows by `Market$`, the 2026 class ranked 26–38 by BASE, and the rest of the ≥ 11 FPts/G vets. Nothing below the top 60 reached T3.
- High-BASE undrafted rookies (De Larrea 412, Thornton 414, Quaintance 390, Karaban 338) read −0.3 to −0.6pp alone and −0.2pp in a set against Meleek Thomas, but score 229–284, top 6 FAs with Scheierman and Barlow (`Score ranking.md`). They are not on the card; nominate them to drain rival $.

## Cheat card

`ΔP` = `dPtitle`. `Δw` = `Δw (season)` over the $1 body. `Score` = `values.tsv` `score`. `Cap` = opening cap at k = 1 (`Max$`). `Sheet #` = position on the Sheet's FA list. ***Bold italic*** rows are ours, priced as keep vs the $1 body (§Ours); not bid targets.

| Tier | Player | Tm | Age | BASE | ΔP | Δw | Score | Market$ | Cap | Sheet # |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | ***De'Andre Hunter*** | SAC | 28.8 | 510 | +0.93 | +0.04 | 581 | – | – | – |
| 1 | ***Jarace Walker*** | IND | 23.0 | 424 | +1.47 | +0.17 | 588 | – | – | – |
| 1 | ***Keon Ellis*** | BKN | 26.7 | 278 | +1.13 | +0.06 | 324 | – | – | – |
| 1 | Baylor Scheierman | BOS | 26.0 | 268 | +1.35 | +0.15 | 375 | 73 | 94 | 16 |
| 1 | Dominick Barlow | PHI | 23.3 | 174 | +1.01 | +0.10 | 246 | 69 | 94 | 4 |
| 1 | Jaxson Hayes | UTA | 26.3 | 129 | +1.28 | +0.03 | 205 | 61 | 86 | 10 |
| 1 | Matisse Thybulle | LAL | 29.6 | 23 | +1.07 | +0.10 | 82 | 26 | 51 | 71 |
| 2 | ***Jay Huff*** | IND | 29.0 | 372 | +0.47 | +0.04 | 365 | – | – | – |
| 2 | ***Adem Bona*** | PHI | 23.4 | 257 | +0.76 | +0.13 | 322 | – | – | – |
| 2 | ***Khris Middleton*** | WAS | 35.1 | 162 | +0.45 | +0.07 | 203 | – | – | – |
| 2 | ***Karlo Matković*** | NOP | 25.4 | 161 | +0.80 | +0.05 | 185 | – | – | – |
| 2 | Vít Krejčí | POR | 26.3 | 148 | +0.62 | +0.10 | 159 | 43 | 44 | 17 |
| 2 | Al Horford | GSW | 40.3 | 117 | +0.48 | +0.07 | 109 | 39 | 44 | 22 |
| 2 | Luka Garza | BOS | 27.7 | 107 | +0.51 | +0.04 | 91 | 40 | 44 | 6 |
| 2 | Kentavious Caldwell-Pope | PHI | 33.6 | 78 | +0.60 | +0.07 | 89 | 36 | 44 | 29 |
| 2 | Jarred Vanderbilt | LAL | 27.5 | 66 | +0.63 | +0.05 | 65 | 31 | 39 | 23 |
| 2 | Simone Fontecchio | MIA | 30.8 | 55 | +0.63 | +0.02 | 44 | 34 | 42 | 11 |
| 2 | Terance Mann | BKN | 29.9 | 51 | +0.57 | +0.03 | 44 | 36 | 44 | 12 |
| 2 | Trayce Jackson-Davis | TOR | 26.6 | 42 | +0.57 | +0.01 | 23 | 19 | 24 | 67 |
| 2 | Nick Richards | MIA | 28.8 | 36 | +0.64 | −0.00 | 20 | 21 | 26 | 51 |
| 2 | Kenrich Williams | OKC | 31.8 | 32 | +0.40 | +0.02 | 2 | 23 | 29 | 37 |
| – | ***Chaney Johnson*** | BKN | – | 0 | +0.06 | −0.05 | −92 | – | – | – |

- **T3** (BASE, ΔP, Score, `Market$`): Dru Smith 231 (+0.25, 175, $47) · Marvin Bagley 197 (+0.29, 201, $63) · Julian Strawther 173 (+0.19, 149, $38) · Zach Collins 140 (+0.20, 107, $34) · Kevon Looney 69 (+0.17, 16, $18) · Trendon Watford 66 (+0.18, 2, $23) · Josh Okogie 25 (+0.23, −31, $23) · Jabari Walker 1 (+0.27, −41, $20)
- **Y:** Meleek Thomas 246 (+0.00, 175, $30) · Chris Cenac 244 (+0.05, 164, $28), if undrafted

## Ours

Our bottom 8 on the `dPtitle` basis, 9/28: roster after both cuts, one $1 body (Justin Edwards) plus FA-grade pads in the open spots. Kept row = keep vs swap to a second $1 body; Chaney and Middleton = add back over the $1 body. Scheierman and Thybulle re-run on this basis read +1.41 and +0.96 (card +1.35, +1.07). Formula `Δw` for `Score`: `Ours.team.md`.

- Every FA except Scheierman scores below Huff, Ellis and Bona, and the top FAs sit inside their 250 tie band (`Score.md`). No extra cut.
- Middleton 203 vs Matković 185 is a Score tie. ΔP (+0.80 vs +0.45) keeps Matković.

## Bidding

- **Hard max** = $ left − (spots left − 1).
- **Rest of plan** = the spots left after this buy, priced at live `Market$`: the cheapest unsold T1s for our remaining T1 wants, plus the cheapest unsold T2 for each other spot ($1 once T2s run out). Leave out the row being bid on.
  - T1 wants = 3 − T1s bought, counting the row being bid on if it is a T1. Capped at unsold T1s and at the spots left.
  - If that costs more than $ left − $1, drop T1 wants one at a time until it fits.
- **Cap** = min(tier cap, $ left − rest of plan, hard max, $100 while ≥ 3 spots are open):
  - T1: no tier cap. A T1 always fills the next slot, even once we hold 3.
  - T2: 1.25 × live `Market$`.
  - T3: live `Market$`, and only once the unsold T2s are fewer than our non-T1 spots left. Until then, no bid.
  - Y: $1.
- The T1 cap rises as rivals buy T1s. At the start it is $94 on Scheierman or Barlow. If only one T1 is left and we hold none, it is $200 − 3 × the cheapest T2, held to $100 until we are down to 2 spots.
- Don't stretch a T1 cap to beat a rich rival by $1–2. A rival who overpays for one T1 can't contest the next.
- **Last spot:** cap = hard max on the rows of the best tier still unsold. Lower tiers keep their tier cap, and T3 stays shut.
- **Endgame:** once our cap on an unsold tiered row beats every rival's `Max Bid`, nothing can outbid us. Nominate the best such row and win it.
- Never bid on an untiered row, and never to push a rival's price. A stuck buy costs one of our 4 spots.
- Waste check: finishing with more than ~$10 unspent means the caps were too tight.

## Nominating

One nominee at a time, first match wins:

1. **Endgame** row (§Bidding).
2. **Last:** once no T1–T3 row is worth a bid, a Y row at $1.
3. **Mid:** the first unsold Mid row whose cap is ≥ 2 × its live `Market$`, or any Mid row we still bid on once half the league's auction spots are filled.
4. **Early:** the Early list in order, then the priciest unsold untiered row by live `Market$`.

Lists:

- **Early:** untiered names the room pays for. This drains rival $ and spots: Brandon Williams, Harrison Barnes, Javonte Green, Goga Bitadze, Pat Spencer, Quinten Post, Patrick Williams, Ryan Nembhard, Caleb Love, Sergio De Larrea, Bruce Thornton, Alex Karaban, Jayden Quaintance.
- **Mid:** our targets deep on the Sheet list, once rivals have spent: Matisse Thybulle, Nick Richards, Trayce Jackson-Davis, Kenrich Williams, Jarred Vanderbilt.
- Leave the top-list T1s (Barlow, Hayes, Scheierman) for rivals to nominate. The endgame rule catches any that are left.
- Per-slot $ at the start: us $50 · Mitch $50 · Bonin, Jon, Todd $33 · Joe $25 · Chris, Brian, Henry, Josh $22 · Hlina $25 ($20 once the deal lands) · Matthew $15. Mitch is the only rival who can match us per slot. Watch his $ left.

# Live

Runbook: `auction-live` Skill (`.claude/skills/auction-live/auction-live.md`).

- Log every sale in `sales.tsv` as `player  team  $`, where team is the owner's first name. Either:
  - **Agent session:** say "sold Hayes Chris 12", or let the Sheet poller append. The agent replies with room heat, the live `Market$` and cap for the unsold tiered rows, and each team's $ left, spots left and `Max Bid`.
  - **Sheet tab:** paste `values.tsv` and `sales.tsv` as tabs, then compute the multiplier below with SUM and VLOOKUP.
- **Live multiplier** k = ($ left league-wide − spots left league-wide) ÷ Σ(`Market$` − 1) over the top (spots left) unsold rows. Live `Market$` = 1 + (`Market$` − 1) × k.
- **Room heat** = Σ(price − 1) ÷ Σ(live `Market$` just before the sale − 1) over the last 8 rival sales expected at ≥ $5. Leave out the forced fill (league spots left ≤ 2 × teams still open). Hot ≥ 1.15, cold ≤ 0.87. Advisory only: caps never use it.
- **Name match:** NFKD-ascii, lowercase, fold `’` to `'`, drop `Jr.`/`Sr.`/`II`/`III`. The Sheet writes Nae’Qwan Tomlin, D’Angelo Russell and Jae’Sean Tate with curly apostrophes. A typo the commissioner never fixes goes in `aliases.tsv` (`sheet  name`).
- **Open spots at start:** Matthew 13 · Hlina 8 (10 once the deal lands) · Chris, Brian, Henry, Josh 9 each · Joe 8 · Bonin, Jon, Todd 6 each · Mitch 4 · us 4.
