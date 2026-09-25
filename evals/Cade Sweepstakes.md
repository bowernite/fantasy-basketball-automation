# Cade sweepstakes (9/25)

Brett is shopping Cade Cunningham to several owners in a bidding war. This file carries the context and preferences for that process, for agents and across compactions.

## Goal

Find Cade deals that beat Todd's live offer on a flat read of the four big numbers plus age. Push prices up and use each bid as leverage.

## Current bids (our side)

| Team | Out | In | ΔBASE | Δw | Δw (season) | ΔP(title) | Age change | Players (us) |
|---|---|---|---|---|---|---|---|---|
| **Todd's live offer (benchmark)** | Cade+Sharpe+Mark | Hali+Porter+NAW+Claxton | +900 | +1.5 | +1.1 | +8% | +2.6 | +1 |
| Todd counter (sent) | Cade+Sharpe+Mark+Kuminga | Hali+Porter+NAW+Claxton+Mitchell | +900 | +1.9 | +1.1 | +11% | +2.7 | +1 |
| Todd counter (sent) | Cade+Sharpe+Mark | Tatum+Porter+NAW+Mitchell | +1000 | +1.7 | +1.5 | +16% | +3.4 | +1 |
| Matthew lead (floated) | Cade+Kuminga+Walker+('27 1st)+('28 1st)+(2.09) | Johnson+Barnes | +900 | +1.5* | +1.3 | +17% | 0.0 | −2 |
| Jon's offer (9/25, added Henry '27 2nd) | Cade+('27 1st)+(2.09) | SGA+Fears+(Henry '27 2nd) | +1500 | +0.9* | +0.5 | +6% | +1.3 | +1 |
| Mitch lead (not yet floated) | Cade+Kuminga+Hunter | Deni+Franz+Queen | +700 | +1.6 | +1.0 | +14% | −1.2 | 0 |
| Mitch fallback (not yet floated) | Cade | Deni+JJJ+Queen | +900 | +1.8 | +0.8 | +12% | −0.6 | +2 |
| Chris feeler (rejected 9/25, depth) | Cade+Walker+Kuminga | Fox+Daniels+Anunoby+Quickley+Bridges+Stewart | +900 | +3.0 | +1.0 | +11% | +2.9 | +3 |

Live status per owner is in each `evals/teams/<owner>/<Name>.shapes.md` intro and Status column.

## How to judge a deal

- Weigh ΔBASE, Δw, Δw (season) and ΔP(title) roughly equally. Title odds help, but don't over-index on this year's.
- **Age:** Brett doesn't want to get significantly older. Report the age change on every deal: weighted mean age, weight = max(0, FPts/G proj − 18) × GP proj, out → in in years. Picks carry no weight.
- **Body adds:** slightly discount deals that are good mostly because we net extra bodies. That's basically free at any point and we can only do it so many times. Show a net "Players (us)" column when bodies are uneven.
- **Picks are on the table from us:** '27 1st, '28 1st, 2.09 (Sept '26), own '27 2nd, KC '27 2nd, Don '27 2nd, '28 2nd.
- Minimums (fail if any): ΔP < 0, ΔBASE ≤ -1000, Δw < -0.25, Δw (season) < -0.25.
- Too lopsided to float: our ΔBASE ≥ about +1250–1400 (Jon: ≥ +1000). The counterparty should see it as a real offer.

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

- Markdown tables for deals: Out | In | ΔBASE | Δw | Δw (season) | ΔP(title) | Age change (+ Players (us) when bodies are uneven). Picks in parentheses on the Out side, e.g. Cade+('27 1st)+(2.09). No deals in prose or bullets.
- Rounding: ΔBASE nearest 100, win columns nearest tenth, ΔP nearest whole %. `*` on Δw when a pick is in the deal.

## Texts (drafts only, never send)

- Brett's voice (`voice` Skill): no colons or dashes, casual, some lowercase sentence starts, no trailing period.
- Phrase offers as "What do you think about X?". Never say a deal works on our end while spitballing.
- Picks in parentheses, e.g. Cade+('27 1st)+(2.09).
- Withhold sim numbers, board info, and why we want a player. Other owners can know Cade is in a bidding war.

## Hard rules

- Never read, grep, print or write `* Trade Shapes.md`. Only `*.shapes.md`.
- No custom scripts: JSON config at `$TMPDIR/ff-sim-<tag>.json` + `evals/lineup-math/run sim_run.py`. Delete tmp configs when done.
- Don't cd; relative paths. zsh: quote args with `=`. `/bin/ls`. GNU sed (`sed -i`, no '').
- No linters/formatters.

## Owner notes

- **Jon** (161015, tanking): won't take Shaedon. On 9/25 he added Henry's '27 2nd (≈810 BASE) to his offer. Picks only add BASE, so they don't close the win-column gap to Todd. Ask for players instead. In his file, Out "Sharpe" = Shaedon (ours), In "Sharpe" = Day'Ron (his). Doesn't want to give both Fears and Day'Ron Sharpe.
- **Todd** (161022, tanking): live offer above.
- **Matthew Pook** = Pharaoh Mattankhamun-Ra (160941), young and climbing, wants young players and picks on his timeline. Won't trade Amen.
- **Chris Kelnhofer** = King Christopher of Bavaria (161014): win now, may sell everything 5–10 weeks in. Values bodies/depth highly. Passed on the 6 for 3 Cade feeler on 9/25: "I'll pass. Don't want to give up the depth. Even tho Cade is awesome". Dropped for Cade on 9/25: no Cade deal that keeps his bodies even also stops costing him about 2–3 wins this season. Hold '27 1st > Daniels or (2.09)+(KC '27 2nd) > Daniels for after Cade settles (re-price then).
- "Mark" = Mark Williams (ours).
- **Mitch** = The Don (161020): contending (6th, 9.4% title) and climbing (2nd in '28-29), so he's a short-term competitor (`trades` §Competitors). Earlier (9/3) he wasn't interested in our '27 1sts. 9/25 on Cade: "Now that does spark my attention" / "I like him more than SGHitler from Dummy who is also someone I inquired about" (he's also asked Jon about SGA).
