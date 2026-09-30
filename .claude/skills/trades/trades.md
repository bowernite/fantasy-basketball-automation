---
description: Use when discussing trades with another owner or building trade packages
---

Always load [Team Projections](/strategy/Team%20Projections.md) for where competitors stand and are headed.

Load `voice` / `write-message` only when the user asks for a message.

# Brainstorm

Most of the work happens here, before any sim. Price shapes by eye off the eval files; sims only confirm the short list (§Simming).

0. **Fresh evals:** if their eval predates the roster file or the projection snapshot, re-run `--eval <team_id>` (or `sim.py players` on us) first.
1. **Pieces:** every player and pick on their side, and every tradeable player, pick and sweetener on ours. Drop only what the owner has ruled out.
2. **Our read, per piece** (`<Name>.team.md`, `Ours.team.md`): BASE or pick VALUE · FPts/G · GP · AGE · `Δw` · `Δw 'YY–'YY ours` · `ΔP(title) ours`. ΔBASE and `Δw` add across pieces. Summed `Δw 'YY–'YY ours` and `ΔP(title) ours` can miss badly either way (high when stacking incoming pieces, far low on star-for-star swaps): use them to rank pieces, and cut on them only on a wide miss.
3. **Their read, per piece:** what they can see, i.e. BASE (they read boards), FPts/G and AGE, weighted by their `SIT` (`Eval Definitions §SIT`), plus anything they've said (`.shapes.md` intro, messages). Never `Δw 'YY–'YY theirs` (`Eval Definitions §Δw (season)`).
4. **Enumerate wide:** combine pieces across their whole roster and all our sweeteners, not just neighbors of shapes already in `.shapes.md`. Use `.shapes.md` only for status and for numbers on shapes already priced, which can make the short list without a re-sim. An edge: tilt toward W22/W23 (maybe W21) games, i.e. take players with more games scheduled in this season's playoff weeks and send out low-GP ones; other owners may not look that far ahead or think they're contending yet.
5. **Cut by eye** any shape that fails a minimum or is Too lopsided (§General guidlines), can't beat the benchmark, or that the owner would plainly refuse on their read.
6. **Short list** (~5–15 shapes) → §Simming. Mid-negotiation or with a lukewarm owner, lead with small tweaks to the shape they already know (§Negotiation).

Unsimmed shapes aren't archived. At most, add one dated line to the `.shapes.md` intro naming avenues ruled out and why.

# Simming

Sim the §Brainstorm short list per `sims` Skill §Agent workflow. Opening information-gathering messages need no sim.

- A real candidate gets one `trade-screen`: all five big numbers, win columns from that field season, both rosters in. `Δw (season)` and `ΔP(title)` are joint sims; `Δw` is the per-piece net sum on the deal (`Eval Definitions §Δw` · `§Δw (season)`)
- A 1-for-1 still gets a run when any piece is near the top of our `ΔP(title)` column
- Batch the short list in one config (`trade-screen` + `player-effects`). A partner who likes a shape gets a few nearby variants in that same run
- Re-price (`--refresh`, or `"refresh": true` on one section) when a roster fetch or projection/GP snapshot changed since the shapes were priced

Done when every newly priced deal is archived in the counterparty's `.shapes.md` and `Trade Shapes.md` per `trade-shapes` Skill, in the same session. Skip duplicate bodies already in the file; re-pricing an existing shape updates its row. Skip archiving only when the user opts out or the run was throwaway info-gathering with no new bodies priced.

# Shapes

Present deals (to the user or in reports: packages, variants, side-by-side options) as one markdown table: `Out | In | Score | ΔBASE | Δw | Δw (season) | ΔP(title) | Δage`, sorted by `Score`, plus `Players (us)` (our net bodies) when body counts are uneven. Picks go on the side that sends them, in parentheses, e.g. `Duren+('27 1st)`, `Brunson+(Todd '27 1st)`. `ΔBASE` is a band, not a point value, wherever `Eval Definitions §BASE` calls for one.

- Benchmark comparisons go in the table: a benchmark row and/or a short `vs <benchmark>` column, never per-deal bullets or prose after the table
- Commentary: 1–3 short lines after the table, max

# The big numbers

Every trade table and deal comparison includes `Score` (`Eval Definitions §Score`) and all five, our side:

- `ΔBASE`
- `Δw`: formula, league curve (`Eval Definitions §Δw`)
- `Δw (season)`: sim-measured for the fantasy season being priced (e.g. `Δw '26–'27`)
- `ΔP(title)`
- `Δage`: our weighted-age change out → in, in years, nearest tenth, signed (`+3.2`, `-1.2`); method §Age. Older is worse. A rough vector read alongside the other four, not a minimum

Compare deals by `Score` first, then read each number. Read both win columns against our `SIT` (`Eval Definitions §SIT`): contending buys `Δw (season)`. Picks are `ΔBASE` and `Δage` only; never convert BASE into `Δw`.

# General guidlines

These apply in the current contending window. Minimums say nothing about the target/maximum.

- `ΔP(title)`: at minimum roughly neutral
- `ΔBASE`: at minimum slightly negative, ideally neutral or positive given the information gap
- `ΔBASE` stays well short of outlandish (+2k and up) even for opening / information-gathering offers: most owners see through it, and it spends their patience (some are busy and eventually tire of talking; varies per owner). The ceiling drops as talks go on or once an owner proves sharp / tracks boards
- `Δw` and `Δw (season)`: at minimum slightly negative

**Archive fail** (`trade-shapes` §Sections, `## Doesn't meet our minimums`) when **any** our-side number fails:

| Metric | Fail when |
|---|---|
| `ΔP(title)` | **< 0** |
| `ΔBASE` | **≤ -1000** |
| `Δw` | **< -0.25** |
| `Δw (season)` | **< -0.25** |

**Too lopsided:** our `ΔBASE` **≥ +1250**. Archived for reference, never floated.

# Uneven bodies

Price the bodies for the delta in body count: break-even rate · backfill regime · our roster-depth floor. Our roster is full at 38 with no filler, so every extra incoming body costs us a real player.

- **Build shapes body-even on our side:** when a shape nets us bodies, add our worst players (the sim's `cut_us`) to **Out**. It costs us what a cut would, and they get something for it.
- **The sim cuts the rest.** Any side a deal takes over 38 drops the bodies whose cut leaves that side's `Score` highest, sim terms included (`Score.md`). `trade-screen` names them in `cut_us` / `cut_them` and charges ours in `ΔBASE`, `Δw` and `Score`. A `cut_us` means the shape isn't body-even yet: move him into **Out** and re-run (Score can move by his board-vs-eval BASE gap, `Score.md`). Cuts come from the sim only, never by hand.
- A counterparty at 38 cuts for each extra body we send (`cut_them`).

# Competitors

For top short-term competitors: our `ΔP(title)` sim already prices helping/hurting them this season, so only our own `ΔP(title)` matters there. Across the next few years, limit how much we help them: their BASE gain (loads them for coming years) and `Δw (them)` (formula, PF-based, not sim; their short-term gain in our format; `fdw_them` / `dw_them` in `trade-screen` results).

# Negotiation

- Other owners lack our info (board aggregation, sims) and our format (daily lineups, slightly different scoring, few dynasty rankings) makes their perception of players, on both sides, liable to swing far either way; less so for stars. Stay open to any shape on both sides, and never assume they value players like we do
- A team eval's read of what an owner wants is a pre-conversation guess, not fact
- Early, when we don't know where the owner stands or whom they value, optimize for information: e.g. float a few different shapes, with different players on either or both sides, to see how they value them
- Float shapes as questions ("What do you think about x?"), so we can sim it if they like it without committing. While spitballing / gathering info, never say it works on our end
- **Shape-change cost:** owners have limited attention, tire, and don't see our numbers. Every new shape costs them re-thinking. Once an owner has a shape in mind, prefer small tweaks to it (swap or add one piece, add a pick), more so as talks go on or when the owner is lukewarm. Float a new shape only for a clearly bigger gain
- **Withhold:** board ranks and which boards · that we blend · that we simulate · that we score their assets at all · any win figure · our ordering of their assets · **why** we want a specific player

# Age

Method for `Δage` (`sim_run.py` reports it as `dage_us`). Each side's age is a weighted mean:

- **Player:** age = `AGE`; weight = max(0, `FPts/G` − 18) × `GP` (`<Name>.team.md` columns)
- **Undrafted pick:** age = 20 − (draft year − current year), e.g. in 2026 a '27 pick is 19, '28 is 18; weight by our round: 1st **700** · 2nd **300** · 3rd **100** · 4th **50**
- **Drafted pick:** the player's row

Example: Cade+('27 1st) > SGA+Fears. Out (24.9×2040 + 19×700) / 2740 = 23.4; In (28.1×2232 + 19.9×666) / 2898 = 26.2 → **+2.8**

Per-player decline and exit risk behind an age gap: `eval-player` §Rules (progression).

# Notes

- `strategy/` holds rosters, per-team valuations and the projections picks depend on
- `strategy/lineup-math/findings.md` is fine to read when a downstream file/skill points to it
