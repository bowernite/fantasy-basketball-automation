---
description: Guidance on trades. Use whenever discussing trades with another player, coming up with trade packages, etc.
---

Instructions for evaluating / approaching teams for trades

- Read both win columns against our `SIT` (`Eval Definitions §SIT`) — contending buys `Δw (season)`.
- Compare deals by `Score` (`Eval Definitions §Score`), then read the individual numbers.
- **Price the bodies** for the delta in body-count: break-even rate · backfill regime · our roster-depth floor.
- Always load [Team Projections](/strategy/Team%20Projections.md) to see rough idea of competitors / where teams are headed

# Messages

Do not load `voice` or `write-message` until the user explicitly asks for one.

# The big numbers

Every trade table and every deal comparison must include `Score` (`Eval Definitions §Score`) and all five (our side):

- `ΔBASE`
- `Δw` — formula, league curve (`Eval Definitions §Δw`)
- `Δw (season)` — sim-measured for the fantasy season being priced (e.g. `Δw '26–'27`)
- `ΔP(title)`
- `Δage` — our weighted-age change out → in, in years, nearest tenth, signed (`+3.2`, `-1.2`); method §Age. Older is worse. A rough vector read alongside the other four, not a minimum

Picks: never convert BASE into `Δw`. Picks are `ΔBASE` and `Δage` only.

`trade-screen` JSON: `delta_base_us` · `fdw_us` · `dw_us` · `dp_title_us` · `dage_us` (plus their-side `fdw_them` / `dw_them`). Re-run with `--refresh` if stale.

_Definitions have more detail here_

# General guidlines (in current contending window)

_Where these are just minimums, do not infer anything about the target/maximum_

- `ΔP(title)` at a minimum should be roughly neutral
- `BASE` at a minimum can be slightly negative. Though ideally neutral or positive, given the information gap we have compared to other teams
- `BASE` should not be outlandishly in our favor even for opening offers / information gathering, e.g. +2k and higher. Most people aren't that dumb, it uses fatigue in the conversation (some owners are busy and _eventually_ will get sick of talking, though this will vary per owner)
  - This maximum probably goes down as the conversation goes on / we realize that an owner is smart / stays in tune with boards
- `Δw` at a minimum can be slightly negative
- `Δw (season)` at a minimum can be slightly negative

**Archive fail** (`trade-shapes` §Doesn't meet our minimums) when **any** our-side number fails:

| Metric | Fail when |
|---|---|
| `ΔP(title)` | **< 0** |
| `ΔBASE` | **≤ -1000** |
| `Δw` | **< -0.25** |
| `Δw (season)` | **< -0.25** |

# Competitors

For teams that are top competitors in the short term:

Since our `ΔP(title)` sim inherently takes into account helping/hurting another team, it really doesn't matter -- all that matters is our own ΔP(title). However we _do_ care about not helping them very much in the few coming years. This comes from BASE somewhat (helping their base might load them for the coming years) and `Δw (them) (PF-based, not sim based)` (this represent how much the trade/players help their team in our format, in the short term)

One advantage, when picking out deals to float out / sim, might be to optimize for W22/W23, maybe W21 (getting players that have higher games scheduled in playoff weeks this year, sending out players with low games played). Other owners may not be thinking that far ahead, may not know how important it is, or maybe don't think they're contending yet and don't think it matters

# "Findings"

A downstream file/skill may have you read `findings.md`

# Who knows what they are thinking

With our different league format, daily lineups, slightly different scoring, and not many dynasty fantasy rankings out there, other owners' perception of players (both on their side and our side) could easily go far in one direction or the other

Less so for better / star players

So, point is, we should be open to anything and everything, and same on their side. We have no idea what they value and undervalue, and what inefficiences there are

# Brainstorm

Most of the work happens here, before any sim. Price shapes by eye off the eval files; sims only confirm the short list (§Simming).

1. **Pieces:** every player and pick on their side, and every tradeable player, pick and sweetener on ours. Drop only what the owner has ruled out.
2. **Our read, per piece** (`<Name>.team.md`, `Ours.team.md`): BASE or pick VALUE · FPts/G · GP · AGE · `Δw` · `Δw 'YY–'YY ours` · `ΔP(title) ours`. ΔBASE and `Δw` add across pieces. Summed `Δw 'YY–'YY ours` and `ΔP(title) ours` can miss badly either way (high when stacking incoming pieces, far low on star-for-star swaps). Use them to rank pieces, and cut on them only on a wide miss.
3. **Their read, per piece:** what they can see, i.e. BASE (they read boards), FPts/G and AGE, weighted by their `SIT` (`Eval Definitions §SIT`), plus anything they've said (`.shapes.md` intro, messages). Never `Δw 'YY–'YY theirs` (`Eval Definitions §Δw (season)`).
4. **Enumerate wide:** combine pieces across their whole roster and all our sweeteners, not just neighbors of shapes already in `.shapes.md`. Use `.shapes.md` only for status and for numbers on shapes already priced, which can make the short list without a re-sim.
5. **Cut by eye** any shape that fails a minimum or is Too lopsided (§General guidlines), can't beat the benchmark, or that the owner would plainly refuse on their read.
6. **Short list** (~5–15 shapes) → §Simming. Mid-negotiation or with a lukewarm owner, lead with small tweaks to the shape they already know (§Negotiation).

Unsimmed shapes aren't archived. At most, add one dated line to the `.shapes.md` intro naming avenues ruled out and why.

# Simming

Load `sims` Skill — **§Agent workflow** (JSON + `sim_run.py` for pricing). Avoid your own scripts whenever possible; tier and archive by hand with your own logic. Sim the §Brainstorm short list. If that eval predates the roster file or the projection snapshot, re-run `--eval <team_id>` (or `players` on us) before brainstorming.

Archive both files (`trade-shapes`): read/rebuild from **`strategy/teams/<owner>/<Name>.shapes.md`**; also write **`<Name> Trade Shapes.md`**. Never read the HTML file. Tiers: above floor / floor / below bar, then **`## Too lopsided`** (our **ΔBASE ≥ +1250**), then **`## Doesn't meet our minimums`** at the absolute bottom (fails any threshold in §General guidlines — archive fail table). Run configs go in **`$TMPDIR/ff-sim-<tag>.json`** only.

Each row: **`Out | In`** (picks in **Out** only, in parentheses) + `Score` + our five big numbers + optional **Status** (rejected, interested, etc.). Tier and sort per `trade-shapes` §Tiering. Skip duplicate bodies already in the file; refresh numbers when re-pricing an existing shape. Display rounding: `trade-shapes` Skill.

```bash
strategy/lineup-math/run sim_run.py "$TMPDIR/ff-sim-<tag>.json"   # new deals only
strategy/lineup-math/run sim_run.py --refresh "$TMPDIR/ff-sim-<tag>.json"   # re-price everything
```

Write deal bodies to tmp JSON, run, read stdout / JSON `results`, copy `Score` and our five big numbers into the right tier in both shape files by hand (`trade-shapes`; minimums here in §General guidlines). Avoid scripts for tiering, sorting, or archiving — rely on your own logic.

**Archive is part of the workflow** — after pricing new deals in a trade session (`trade-with`, negotiation, screening), update the counterparty's `.shapes.md` and `Trade Shapes.md` in the same session. Skip only when the user opts out or the run was throwaway info-gathering with no new bodies priced.

**When to refresh** — roster fetch or projection/GP snapshot changed and old joint prices may be stale:

- **`--refresh`** — re-run all trade sections in the file
- **`"refresh": true`** on one section — re-run just that block (cleared on write)

Skip for opening information-gathering messages.

- A real candidate gets one `trade-screen` — all five big numbers, win columns from that field season, both rosters in. `Δw (season)` and `ΔP(title)` are joint sims; `Δw` is per-piece net sum on the deal (`Eval Definitions §Δw` · `§Δw (season)`).
- A 1-for-1 still gets a run when any piece is near the top of our `ΔP(title)` column
- Batch the short list in one config (`trade-screen` + `player-effects`). A partner who likes a shape gets a few nearby variants in that same run

# Uneven bodies

Our roster is full at 38 with no filler, so every extra incoming body costs us a real player.

- **Build shapes body-even on our side:** when a shape nets us bodies, add our worst players (the sim's `cut_us`) to **Out**. It costs us what a cut would, and they get something for it.
- **The sim cuts the rest.** Any side a deal takes over 38 drops the bodies whose cut leaves that side's `Score` highest, sim terms included (`Score.md`). `trade-screen` names them in `cut_us` / `cut_them` and charges ours in `ΔBASE`, `Δw` and `Score`. A `cut_us` means the shape isn't body-even yet: move him into **Out** and re-run. Never pick a cut by hand.
- A counterparty at 38 cuts for each extra body we send (`cut_them`).

# Shapes

Whenever presenting deals (to the user or in reports) — packages, variants, or side-by-side options — use a single markdown table: `Out | In | Score | ΔBASE | Δw | Δw (season) | ΔP(title) | Δage`, sorted by `Score`, plus `Players (us)` (our net bodies) when body counts are uneven. Picks in **Out** only, in parentheses — e.g. `Duren+('27 1st)` (`sims` Skill §Team archive). `ΔBASE` is a band, not a point value, wherever `Eval Definitions §BASE` calls for one.

- Benchmark comparisons go in the table: a benchmark row and/or a short `vs <benchmark>` column. Never a per-deal bullet or prose list after the table
- Commentary: 1–3 short lines after the table, max

# Negotiation

- At the start of the conversation, when we don't know where the owner stands on things or who they value etc, we may want to optimize for information gathering. One example we may want to use for that is throwing out a few different shapes with different players and/or on both sides, to see how they value them
- Information gap: other teams don't have nearly the level of info that we do (board aggregation, sim data, etc). Because of this, do not assume the other team values players like we do
- **Shape-change cost:** owners have limited attention and tire, and they don't see numbers like we do. Every new shape costs them re-thinking. Once an owner has a shape in mind, prefer small tweaks to it (swap or add one piece, add a pick) over new shapes, more so as talks go on or when the owner is lukewarm. Float a new shape only for a clearly bigger gain

## Reveal / withhold

- **Withhold:** board ranks and which boards · that we blend · that we simulate · that we score their assets at all · any win figure · our ordering of their assets · **why** we want a specific player.

# Age

Method for `Δage` (§The big numbers; `sim_run.py` reports it as `dage_us`). Each side's age is a weighted mean:

- **Player:** age = `AGE`; weight = max(0, `FPts/G` − 18) × `GP` (`<Name>.team.md` columns)
- **Undrafted pick:** age = 20 − (draft year − current year), e.g. in 2026 a '27 pick is 19, '28 is 18; weight by our round: 1st **700** · 2nd **300** · 3rd **100** · 4th **50**
- **Drafted pick:** the player's row

Example: Cade+('27 1st) > SGA+Fears. Out (24.9×2040 + 19×700) / 2740 = 23.4; In (28.1×2232 + 19.9×666) / 2898 = 26.2 → **+2.8**

# Notes

- `strategy/` holds rosters, per-team valuations and the projections picks depend on. `team-info` maps owner username → real name.
- When reading a team-eval, it might state things about what they want or don't want. These are just guesses, before we have even spoken to them. Do not take them to be true necessarily.
- When trying to find a deal shape with someone, should be phrased as something like "What do you think about x?". This will allow us to to sim it if they like the shape, without us committing to it.
  - So if we're spitballing / gathering information, never say it works on our end.
