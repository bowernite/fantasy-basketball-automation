---
name: league-info
description: League rules, format and scoring for our 12-team dynasty points league — the verified facts other skills reason from.
---

Facts only. Valuation: `eval-team`. Fetching: `get-league-info`.

- Full dynasty (keep all players), 12 teams, **points** format — never categories.
- **Daily lineups** inside a 7-day matchup: 15–20 different players score per week.
- League `30579`. Our team `161025` — **Bathroom club**.

# Lineups

9 starters (`FetchLeagueRules.rosterPositions`): **PG · SG · G(PG|SG) · SF · PF ·
F(SF|PF) · C · ANY ×2**. So 3 guard-only, 3 forward-only, 1 center-only, 2 shared.
**F does not include C.**

Read `proPlayer.positionEligibility` per player — never assume.

## Matchup periods

7-day schedule periods; the last few are playoffs and consolation. Enumerate from
`eligibleSchedulePeriods` — never assume a count or that every period is full-length.
Standings `pointsFor` covers scored regular-season periods only.

⚠️ **The scored regular season is 19 periods. Period 20 is bracket round 1** — verified
against the wire, '25-26. There is no short makeup period: the reason 4 teams finished with
20 games and 8 with 19 is that the four are **seeds 5–8 playing R1**. Any claim of a 20-period
basis is this bug, not a fact.

**Bracket: 8 of 12 teams, 4 rounds, periods 20–23** (03-02 · 03-09 · 03-16 · 03-23 in '25-26).
R1 seeds 5–8, paired **5v8 and 6v7** → R2 winners meet seeds 3–4 → R3 those winners meet
seeds 1–2 → R4 final (period 23, `isChampionshipGame`; the other game is the two R3 losers,
`isThirdPlaceGame`). Seeds 1–2 are **double-byed**: 2 wins to the title, 3 from seeds 3–4,
4 from 5–8. Seeded off the **19-period** standings.

**Which side of the draw is fixed**: two halves, each climbed worst seed first —
**8-5-4-1** and **7-6-3-2**. So the 5/8 winner meets 4 then 1, the 6/7 winner meets 3 then 2,
and seeds 1 and 3 (or 2 and 4) cannot meet before the final.

⚠️ **What Fleaflicker cannot express is R1's *label*, not the bracket.** Its bracket tool
tops out at the 6-team/3-round shape it generated for periods 21–23, so the owner creates R1
as **two ordinary un-flagged matchups inside period 20**. Those games carry **no `isPlayoffs`
and no `isConsolation` key at all**, so anything classifying "no flag" as regular season
silently scores a playoff round — and Fleaflicker's own standings do exactly that. `pointsFor`
is contaminated for those four teams (ours reads 27,228.75 including R1; the clean 19-period
figure is 25,573).

**The matchups themselves are real and the bracket does reconstruct from them** — periods
20–23 are the played bracket. The lock is that period 21 pairs **3v7**, not 3v6: seed 7 is
only there because he won a 6v7 game in period 20, so the bracket is *not* reconstructable
without it. Reading periods 21–23 alone yields a plausible-looking 6-team/3-round bracket that
never happened. **Never take the round count or the window from period `kinds`.**

⚠️ **Bracket R1 therefore feeds `recordOverall.rank`, which sets the draft order.** Winning it
*worsens* your pick: our R1 win took us to 12-8 → rank 4 → slot 9, while the team we knocked
out stayed 11-8 → rank 5 → slot 8. A bracket game can move a slot across the top-4 draft cut.

**Seeds are not `recordOverall.rank`** — they tie-break on points-for (verified: two 14-5
teams, the one ranked 3rd took the bye on top-of-league PF). `recordOverall.rank` is
authoritative for the **draft**, not the bracket. Do **not** infer bracket size from the
draft-order rule below either: that rule splits at the top **4 by record**, a different cut.

Downstream, the playoff cut is **8 of 12**, so a bubble sits at **8/9** — `Mₜ`
(`strategy/Team Projections.md`) reads against that line and nothing else.

# Roster size — a hard cap, and it is binding

`FetchLeagueRules` fields: `maxRosterSize` · `maxActive` · `numStarters` · `numBench` ·
`rosterPositions[]`. Re-read them before relying on any figure below.

| | '25-26 (verified) | '26-27, from Sept '26 (announced) |
|---|---|---|
| Starters · Bench · IR | 9 · 15 · 4 | 9 · 29 · 0 |
| `maxRosterSize` | **28** | **38** |
| `maxActive` | 24 | 38 |

`maxRosterSize` counts IR. `rosterPositions[]` still carries a `TAXI` entry, but with
**no `start` key** — zero slots, so taxi does not exist here; only `IR` (`start: 4`)
does. Absent `start` = 0 slots, not "unlimited".

**Legality is `count_after ≤ maxRosterSize`, per side** — not body-neutrality. A side that
would finish over attaches `playersReleased` to the trade. **Body-uneven shapes are routine
here, and three-team trades exist.** Count both sides live (`FetchLeagueRosters` →
`rosters[].players[]`) before pricing a deal, not after. `trades` owns the check and the
price of the drops.

**`maxActive` binds separately.** Teams at 28 run 24 active + 4 full IR slots, so a
body-neutral IR-for-healthy swap still adds an active body — **ask before pricing one**. IR
occupancy does not track current injury flags: healthy players sit parked there. Dated —
expires with IR in Sept '26.

The 10 new slots fill in one September: **the rookie draft, then the FA auction**. At
12 × 38 = 456 essentially every NBA-rostered player is owned, so the FA pool empties
and **a shipped-out body stops being replaceable**. Consequences: `trades` (timing),
`eval-pick` (pick value), `Eval Definitions §Where our format pulls off consensus`
(backfill regime, and 5 for steering auction bodies on light-night coverage — a free tiebreak
worth about the decision floor, whose whole case is avoiding the stacked shape).

**The FA event every offseason is a live auction right after the rookie draft**, run on a
Google Sheet with its own use-it-or-lose-it budget — not the Fleaflicker $100 FAAB, never
blind bids. Only the current draft class is in the rookie draft; undrafted rookies and every
older player are auction FAs. Fleaflicker transaction history is not a record of past
FA-event format.

# Offseason transaction lock

**FA adds lock at some point in the offseason and reopen at the rookie draft + FA event.
Trades stay open throughout — and so do releases.** A drop with no add appears on the wire
inside both lock windows, and a pending trade is releasing a player during this one.

**The lock start is not a known rule — do not assume one.** It is not end-of-season:
the transaction log shows adds well into the following June. Locked as of late July '26.

No API field reports the lock. Transaction history and the free-agent listing both look
live during it, and `transactionStatus` is byte-identical for rostered and free players,
so **there is no wire-live check — ask rather than infer** (`get-league-info`).

# Drafting

Rookie draft every offseason. Not an auction; rookies only. 3 rounds × 12 = 36 picks.
**A season's finish sets the following offseason's draft.**

**Rounds 1–3 share one order** — `draftOrder[]` is a single array for the whole draft, no
snake — so round-1 positioning propagates into rounds 2 and 3.

- **Top 4 by `recordOverall.rank`** take slots 9–12 in **reverse rank order** — exact on both
  boards. Read `rank`; never a win percentage you compute — a tied matchup splits them (a
  16-2-1 team ranked *below* a 15-3-1 one, and the board followed `rank`). Not by playoff
  advancement (verified: the bracket's 4th-place finisher picked 8th, the 4th-by-record team
  9th) and not by seed. This cut is 4 and the bracket's is wider — a team can play in the
  bracket and still pick 1.07/1.08.
- **Bottom 8 by record (5th–12th)** fill slots 1–8, worst-to-best, then a **lottery**
  reorders them — in all three rounds. Its scope is not fixed:
  the '26 board swapped only slots 2 and 3 and the worst team kept 1.01; the '25 board shows
  no reorder at all.

So `slot = 13 − record rank` holds for the top 4 and is only a **prior** for the bottom 8 —
read their slot off the board (`get-league-info`), never derive it. Fleaflicker's draft
labelling is a trap — `get-league-info`.

# Scoring (verified against `FetchLeagueRules`)

**Never hand-recompute fantasy points off a Fleaflicker stat line** — `seasonAverage` and
`pointsActual` are already scored under these rules. Scoring a *projection* is the one
exception, and it runs through `projections` §*What the scoring does*, never by hand.

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

**DD and TD are cumulative** — a triple-double pays **+7**, not +5. Double-digit categories
are Pts/Reb/Ast/Stl/Blk at **≥ 10**; shooting counters never count.

**Volume and usage dominate; the miss penalties are near-cosmetic** — a shot breaks even
at ~11% from either range, and an FTA has zero downside. Efficiency is a tiebreak, not a
penalty. Never use a generic points-league model.

# Notes

- `team-info` maps owner username → real name.
