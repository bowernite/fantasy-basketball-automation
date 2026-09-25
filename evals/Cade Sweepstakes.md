# Cade sweepstakes (9/25)

Brett is shopping Cade Cunningham to several owners in a bidding war. This file carries the context and preferences for that process, for agents and across compactions.

## Goal

Find Cade deals that beat Jon's offer (best bid from another owner, Brett's current pick) on `Score`. Push prices up and use each bid as leverage. Todd's live offer still wins this season (+1.1 vs +0.5 `Δw (season)`) and on ΔP(title) (+8% vs +5%); Jon's lead comes from BASE.

## Current bids (our side)

| Team | Out | In | Score | vs Jon | ΔBASE | Δw | Δw (season) | ΔP(title) | Δage | N |
|---|---|---|---|---|---|---|---|---|---|---|
| Jon counter (sent) | Cade+(2.09) | SGA+Sharpe+Wells | +3900 | +1400 | +2700 | +1.6 | +0.7 | +9% | +2.5 | +2 |
| Jon fallback (not sent) | Cade+(2.09) | SGA+Fears+Wells | +3700 | +1200 | +2800 | +1.4 | +0.6 | +7% | +1.6 | +2 |
| Todd counter B (sent) | Cade+Sharpe+Mark | Tatum+Porter+NAW+Mitchell | +3100 | +600 | +1000 | +1.7 | +1.5 | +16% | +3.4 | +1 |
| Jon next ask (drafted, not sent) | Cade+(2.09)+(KC '27 2nd) | SGA+Sharpe+Wells | +3000 | +500 | +1800 | +1.6 | +0.7 | +9% | +3.1 | +2 |
| Jon latest ask (drafted, not sent) | Cade+Mark+(2.09) | SGA+Sharpe+Wells+McBride | +2800 | +300 | +1700 | +1.2 | +0.8 | +9% | +2.4 | +2 |
| Jon Raynaud 2 (Us proposed 9/25) | Cade+Mark+(2.09) | SGA+Sharpe+Raynaud | +2700 | +200 | +1700 | +0.9 | +0.7 | +8% | +2.4 | +1 |
| Jon Raynaud 3 (Us proposed 9/25) | Cade+Kuminga+('27 1st)+(2.09) | SGA+Fears+Raynaud+Wells | +2700 | +200 | +1600 | +1.7 | +0.6 | +8% | +2.5 | +2 |
| Jon Raynaud 1 (Us proposed 9/25) | Cade+('27 1st)+(2.09) | SGA+Fears+Raynaud | +2600 | +100 | +1700 | +1.5 | +0.6 | +7% | +2.8 | +2 |
| Mitch Flagg (Us proposed 9/25) (sent, no reply) (out 9/25) | Cade+('27 1st)+('28 1st)+(own '27 2nd) | Deni+Flagg | +2600 | +100 | +900 | +1.6 | +1.0 | +14% | ~ | +1 |
| Chris feeler (dropped 9/25) | Cade+Walker+Kuminga | Fox+Daniels+Anunoby+Quickley+Bridges+Stewart | +2600 | +200 | +900 | +3.0 | +1.0 | +11% | +2.9 | +3 |
| Todd counter A (rejected 9/25) | Cade+Sharpe+Mark+Kuminga | Hali+Porter+NAW+Claxton+Mitchell | +2500 | +100 | +900 | +1.9 | +1.1 | +11% | +2.7 | +1 |
| Mitch lead (rejected 9/25) | Cade+Kuminga+Hunter | Deni+Franz+Queen | +2500 | 0 | +700 | +1.6 | +1.0 | +14% | −1.2 | 0 |
| **Jon's offer (Jon proposed 9/25, benchmark)** | Cade+(2.09) | SGA+Wells+McBride | +2400 | — | +1800 | +1.0 | +0.5 | +5% | +3.0 | +2 |
| Mitch fallback (rejected 9/25) | Cade | Deni+JJJ+Queen | +2400 | −100 | +900 | +1.8 | +0.8 | +12% | −0.6 | +2 |
| Matthew realistic (sent) | Cade+Sharpe+Mark+('27 1st)+('28 1st)+(2.09) | Barnes+Harper+Ausar+Black | +2400 | −100 | +1000 | +1.1 | +1.1 | +11% | +1.1 | +1 |
| Matthew backup (not sent) | Cade+Sharpe+('27 1st)+('28 1st)+(2.09) | Barnes+Harper+Ausar | +2200 | −200 | +1000 | +1.1 | +0.9 | +10% | +1.3 | +1 |
| Matthew ask (sent, Wemby now untouchable) | Cade+Kuminga+('27 1st)+('28 1st)+(2.09) | Wemby+Ausar+Black | +2200 | −300 | +700 | +1.8 | +1.1 | +10% | +0.7 | +1 |
| Todd's live offer | Cade+Sharpe+Mark | Hali+Porter+NAW+Claxton | +2200 | −300 | +900 | +1.5 | +1.1 | +8% | +2.6 | +1 |
| Matthew backup 2 (not sent) | Cade+(2.09) | Barnes+Ausar+Black | +1800 | −600 | +1000 | +1.4 | +0.4 | +7% | −0.2 | +2 |

Sorted by `Score`; vs Jon = Score minus the benchmark's (≈300 over Todd's raw +2164), nearest 100. Δage isn't in Score, so read it alongside. All Jon rows are Too lopsided under Jon's +1000 line.

Live status per owner is in each `evals/teams/<owner>/<Name>.shapes.md` intro and Status column.

## How to judge a deal

- Compare and rank by [Score](Definitions/Score.md) as the baseline. Gate first (minimums, Too lopsided) per `trades` §General guidlines and `trade-shapes` §Tiering. Jon's file uses a +1000 Too lopsided line.
- After that, read the individual numbers (including N and Δage, which isn't in Score) and the counterparty's view of value (e.g. a lopsided ΔBASE they'd never accept) with nuance.
- **Picks are on the table from us:** '27 1st, '28 1st, 2.09 (Sept '26), own '27 2nd, KC '27 2nd, Don '27 2nd, '28 2nd.
  - Privately, we want to move our picks (Brett, 9/25). Don't say so to other owners.
  - We value our picks below their BASE (Brett, 9/25): we're contending, our 1sts will likely land late, and we'll soon have more picks than roster use for. So Score undercounts deals where we add picks, since it subtracts full pick BASE. Use picks as sweeteners to buy win columns and ΔP(title) (e.g. upgrading Hali to Tatum with Todd), not BASE. Todd and Matthew both want picks.
  - Adding a later pick ('27/'28) to our Out side doesn't need a re-sim. Subtract its BASE from ΔBASE and Score, since the win columns and ΔP(title) don't change. Its age effect is small, and it makes our Out side younger.
  - The 2.09 (Sept '26) does count in the win columns, so it needs a sim.

### BASE caveat (agent analysis 9/25; BASE method stays as is)

- Jon's +1800 ΔBASE ≈ +1470 SGA over Cade + ≈340 throw-ins. Both boards rank SGA 2, Cade 6, and the [BASE](Definitions/BASE.md) curve (a = √D) charges ≈365/rank at the top.
- This season they're about even (49 vs 48 FPts/G). Cade is 3.2 years younger, and BASE has no age/horizon adjustment beyond the boards, whose horizon is likely shorter than the AGENTS.md objective (favors older stars). Hashtag keeper values have SGA only ≈3% over Cade.
- `a` is asserted, not measured. At a ≈ 10.7: Jon ≈ +2450, Todd's live offer ≈ −640. At a ≈ 42.7: Jon ≈ +1490, Todd ≈ +2990. Read as a ΔBASE band (per BASE.md for uneven-body/pick deals), Todd's live offer is a BASE tie.
- Treat Jon's lead over Todd's live offer as ≈ a tie once age counts; Todd wins this season and on ΔP(title). Be wary of BASE-driven leads in any star-for-star swap.

## Pick BASE (for `out_us_extra_base`)

| Pick | BASE |
|---|---|
| '27 1st | 1425 |
| '28 1st | 1425 |
| 2.09 | 645 |
| own '27 2nd | 540 |
| KC '27 2nd | ≈900 |
| Don '27 2nd | ≈775 |
| '28 2nd | 634 |

Sept '26 picks (2.09) also need `out_us_picks` and `in_from_us_picks` so the mock rookie counts in win columns.

## Output format

- Deal tables: `trades` §Shapes. Jon's offer is the benchmark row.
- Rounding: `trade-shapes` §Table format.

## Texts (drafts only, never send)

- Brett's voice (`voice` Skill): no colons or dashes, casual, some lowercase sentence starts, no trailing period.
- Phrase offers as "What do you think about X?". Never say a deal works on our end while spitballing.
- Picks in parentheses, e.g. Cade+('27 1st)+(2.09).
- Withhold sim numbers, board info, and why we want a player. Other owners can know Cade is in a bidding war.

## Hard rules

- Never read, grep, print or write `* Trade Shapes.md`, `*'s Team.md` or `My Team.md`. Agents read `<Name>.shapes.md` and `<Name>.team.md` only (ours is `evals/teams/my-team/Ours.team.md`).
- No custom scripts: JSON config at `$TMPDIR/ff-sim-<tag>.json` + `evals/lineup-math/run sim_run.py`. Delete tmp configs when done.
- Don't cd; relative paths. zsh: quote args with `=`. `/bin/ls`. GNU sed (`sed -i`, no '').
- No linters/formatters.

## Owner notes

- **Jon** (161015, tanking): won't take Shaedon. Standing offer (9/25 11:43a): Cade+(2.09) for SGA plus our pick of 1 or 2 of Champagnie/Wells/McBride; we keep Shaedon and Mark. Henry's '27 2nd (≈810 BASE) came only with his SGA+Fears package for Cade+('27 1st)+(2.09) (11:23a), which we declined; it's not in the standing offer. 12:20p: "Sounds like Todd's offer is going to beat mine at this point". Picks only add BASE, so they don't close the win-column gap to Todd. Ask for players instead. In his file, Out "Sharpe" = Shaedon (ours), In "Sharpe" = Day'Ron (his). Doesn't want to give both Fears and Day'Ron Sharpe. On 9/25 he re-floated Brett's old 8/2 shape Cade+Edey+(3.09) for SGA+Jaylin+(Jon 2.10), which fails our minimums; declined 3:15p. Our 3.09 went to Henry on 8/13. Edey is a hold in Cade talks (agent sim 9/25). Nudged him on the Raynaud shapes 9/25; no answer yet.
- **Todd** (161022, tanking): live offer above. Rejected counter A 9/25 (3:47p): "I'm not big on Kuminga so probably prefer the simpler deal".
- **Matthew Pook** = Pharaoh Mattankhamun-Ra (160941), young and climbing, wants young players and picks on his timeline. Won't trade Amen Thompson (we just sent Amen to him and he likes him), so never put Amen on the In side. Treat Wemby as untouchable too (Brett, 9/25). 9/25 asked "Any hypotheticals without Johnson?".
- **Chris Kelnhofer** = King Christopher of Bavaria (161014): win now, may sell everything 5–10 weeks in. Values bodies/depth highly. Passed on the 6 for 3 Cade feeler on 9/25: "I'll pass. Don't want to give up the depth. Even tho Cade is awesome". Dropped for Cade on 9/25: no Cade deal that keeps his bodies even also stops costing him about 2–3 wins this season. Hold '27 1st > Daniels or (2.09)+(KC '27 2nd) > Daniels for after Cade settles (re-price then).
- "Mark" = Mark Williams (ours).
- **Mitch** = The Don (161020): Out of the Cade talks (Brett, 9/25). Contending (6th, 9.4% title) and climbing (2nd in '28-29), so he's a short-term competitor (`trades` §Competitors). Earlier (9/3) he wasn't interested in our '27 1sts. 9/25 on Cade: "Now that does spark my attention" / "I like him more than SGHitler from Dummy who is also someone I inquired about" (he's also asked Jon about SGA). Rejected both sent shapes 9/25: "Both of those seem a bit steep to me. I think Cade > Deni but not by a ton in fantasy. Their dif was only 5 points, don't think that's worth giving up a mid 30s in JJJ and high 20s-low 30s in Queen. I have negative interest in Kuminga lol", then "I think the most I'd be willing to do is something like Deni + one other guy for Cade. Otherwise I'd be more open to trades once I see how these rooks of mine look after some nba action". Values players by FPts/G. Keep Kuminga and his Sept '26 rookies out of shapes. Deni + one other guy tops out at Cade > Deni+Franz (Score +900, −1200 vs Todd). Flagg is virtually untouchable (Brett, 9/25): no new In-side Flagg shapes. Without Flagg, getting past Todd takes Deni+Franz+Queen plus a cheap piece from us, e.g. Cade+Butler (+2800) or Cade+(KC '27 2nd) (+2900).
