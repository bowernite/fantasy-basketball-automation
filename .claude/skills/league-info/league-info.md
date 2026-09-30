---
description: Use when reasoning from league rules — lineups, playoff bracket and seeding, roster cap, draft order, offseason transaction lock, scoring
---

Verified facts only. Valuation: `eval-team`. Fetching: `get-league-info`.

- Full dynasty (keep all players), 12 teams, **points** format (never categories)
- **Daily lineups** inside a 7-day matchup: 15–20 different players score per week

# Lineups

9 starters (`FetchLeagueRules.rosterPositions`): **PG · SG · G(PG|SG) · SF · PF · F/C(SF|PF|C) · C · ANY ×2**. So 3 guard-only, 2 forward-only, 1 center-only, 1 frontcourt (F/C), 2 shared. **F/C includes C.**

Read `proPlayer.positionEligibility` per player.

## Matchup periods

7-day schedule periods; the last few are playoffs and consolation. Enumerate from `eligibleSchedulePeriods`, never assuming a count or that every period is full-length. Standings `pointsFor` covers scored regular-season periods only.

⚠️ **The scored regular season is 19 periods. Period 20 is bracket R1** (verified against the wire, '25-26). There is no short makeup period: 4 teams finished with 20 games and 8 with 19 because the four are **seeds 5–8 playing R1**. Any 20-period regular-season basis is wrong.

**Bracket: 8 of 12 teams (bubble at 8/9), 4 rounds, periods 20–23** (03-02 · 03-09 · 03-16 · 03-23 in '25-26). R1 seeds 5–8, paired **5v8 and 6v7** → R2 winners meet seeds 3–4 → R3 those winners meet seeds 1–2 → R4 final (period 23, `isChampionshipGame`; the other game is the two R3 losers, `isThirdPlaceGame`). Seeds 1–2 are **double-byed**: 2 wins to the title, 3 from seeds 3–4, 4 from 5–8. Seeded off the **19-period** standings.

**Draw sides are fixed**: two halves, each climbed worst seed first — **8-5-4-1** and **7-6-3-2**. So the 5/8 winner meets 4 then 1, the 6/7 winner meets 3 then 2, and seeds 1 and 3 (or 2 and 4) cannot meet before the final.

⚠️ **Fleaflicker can't label R1, but the bracket is real.** Its bracket tool tops out at the 6-team/3-round shape it generated for periods 21–23, so the owner creates R1 as **two ordinary matchups inside period 20** carrying **no `isPlayoffs` and no `isConsolation` key**. Anything classifying "no flag" as regular season silently scores a playoff round, and Fleaflicker's own standings do exactly that: `pointsFor` is contaminated for those four teams (ours reads 27,228.75 including R1; the clean 19-period figure is 25,573).

Periods 20–23 are the played bracket and reconstruct it: period 21 pairs **3v7**, not 3v6, because seed 7 won the 6v7 game in period 20. Periods 21–23 alone yield a plausible 6-team/3-round bracket that never happened. Take the round count and window from this section, never from period `kinds`.

⚠️ **Bracket R1 feeds `recordOverall.rank`, which sets the draft order.** Winning it *worsens* the pick and can move a slot across the top-4 draft cut (our R1 win: 12-8 → rank 4 → slot 9; the team we knocked out stayed 11-8 → rank 5 → slot 8).

**Seeds tie-break on points-for, not `recordOverall.rank`** (verified: of two 14-5 teams, the one ranked 3rd took the bye on top-of-league PF). `recordOverall.rank` is authoritative for the **draft**, not the bracket. Bracket size is 8; the draft-order split at the top **4 by record** is a different cut.

# Roster size — a hard, binding cap

Re-read the `FetchLeagueRules` roster fields before relying on any figure below.

| Starters · Bench · IR | `maxRosterSize` | `maxActive` |
|---|---|---|
| 9 · 29 · 0 | **38** | 38 |

`maxRosterSize` counts IR. `IR` and `TAXI` entries sit in `rosterPositions[]` with **no `start` key** — zero slots, so neither exists here. Absent `start` = 0 slots, not "unlimited".

**Legality is `count_after ≤ maxRosterSize`, per side** — not body-neutrality. A side that would finish over attaches `playersReleased` to the trade. **Body-uneven shapes are routine here, and three-team trades exist.** Count both sides live (`FetchLeagueRosters` → `rosters[].players[]`) before pricing a deal. `trades` owns the check and the price of the drops.

At 12 × 38 = 456 essentially every NBA-rostered player is owned, so the FA pool is empty and **a shipped-out body is not replaceable**. Consequences: `trades` (body pricing), `eval-pick` (pick value), `Eval Definitions §Where our format pulls off consensus` (backfill regime).

**The FA event every offseason is a live auction right after the rookie draft**, run on a Google Sheet with its own use-it-or-lose-it budget — not the Fleaflicker $100 FAAB, never blind bids. Only the current draft class is in the rookie draft; undrafted rookies and every older player are auction FAs. Fleaflicker transaction history is not a record of past FA-event format.

# Offseason transaction lock

**FA adds lock at some point in the offseason and reopen at the rookie draft + FA event. Trades and releases stay open throughout.** A drop with no add appears on the wire inside both lock windows (e.g. a trade's `playersReleased`).

The lock start is unknown — ask rather than assume. It is not end-of-season: the transaction log shows adds well into the following June. Seen locked in late July '26. The API can't show the lock (`get-league-info` §Offseason).

# Drafting

Rookie draft every offseason. Not an auction; rookies only. 4 rounds × 12 = 48 picks, every round tradeable. **A season's finish sets the following offseason's draft.**

**All 4 rounds share one order** (`draftOrder[]`, no snake), so round-1 positioning propagates into every later round.

- **Top 4 by `recordOverall.rank`** take slots 9–12 in **reverse rank order** — exact on both boards. Read `rank`, not a win percentage you compute: a tied matchup splits them (a 16-2-1 team ranked *below* a 15-3-1 one, and the board followed `rank`). Not by playoff advancement (verified: the bracket's 4th-place finisher picked 8th, the 4th-by-record team 9th) and not by seed. A team can play in the bracket and still pick 1.07/1.08
- **Bottom 8 by record (5th–12th)** fill slots 1–8, worst-to-best, then a **lottery** reorders them — in every round. Its scope is not fixed: the '26 board swapped only slots 2 and 3 and the worst team kept 1.01; the '25 board shows no reorder at all

So `slot = 13 − record rank` holds for the top 4 and is only a **prior** for the bottom 8 — read their slot off the board. Draft labelling traps: `get-league-info` §Draft boards.

# Scoring (verified against `FetchLeagueRules`)

`seasonAverage` and `pointsActual` are already scored under these rules — use them as-is, never hand-recompute off a stat line. Scoring a *projection* is the one exception, and it runs through `projections` §Scoring.

| Category | Value |
|---|---|
| Points · Rebounds · 3PM | 1 |
| **Offensive rebounds** | **+1 additional** (OReb = 2, DReb = 1) |
| Assists | 1.5 |
| **Steals** | **3** |
| Blocks | 2 |
| Turnovers | −1 |
| FG missed | −0.25 |
| 3PT missed | −0.25 (a missed three costs −0.50 total) |
| Double-double · Triple-double | +2 · +5 |
| Fouls · missed FTs | **not scored** |

**DD and TD are cumulative** — a triple-double pays **+7**. Double-digit categories are Pts/Reb/Ast/Stl/Blk at **≥ 10**; shooting counters never count.

**Volume and usage dominate; the miss penalties are near-cosmetic** — a shot breaks even at ~11% from either range, and an FTA has zero downside. Efficiency is a tiebreak, not a penalty. Use this table, not a generic points-league model.
