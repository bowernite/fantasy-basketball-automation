---
name: projections
description: Projected per-game stats scored under our rules — the rate both `Δw` and `Δw (season)` run on. Fetch, score and refresh the projection snapshot.
---

# Projections

The rate behind both win columns is a **projection scored under our rules**, not last season's
`FPts/G` (`Eval Definitions §Δw (season)` · `§Δw`). This skill owns the fetch and the scoring.

Source: **RotoWire, via Sleeper's free API** — one keyless call, per-game, ~587 players
with a stat line. Single source today; see *Adding a source*.

## Fetch in a subagent

`refresh` and `roster` run inside a dedicated `Agent` (`CLAUDE.md` §*Subagents*) — have it
hand back the printed table, never raw JSON.

```bash
python3 .claude/skills/projections/sleeper.py refresh              # rewrite the snapshot
python3 .claude/skills/projections/sleeper.py roster <roster.json> # last vs projected rate
python3 .claude/skills/projections/hashtag_gp.py refresh           # rewrite the Hashtag GP snapshot
python3 .claude/skills/projections/fanscout_gp.py refresh          # rewrite the FanScout GP snapshot
python3 .claude/skills/projections/test_scoring.py                 # offline guards, no network
python3 .claude/skills/projections/test_sleeper.py
python3 .claude/skills/projections/test_hashtag_gp.py
python3 .claude/skills/projections/test_fanscout_gp.py
python3 .claude/skills/projections/test_overrides.py
```

Rate snapshot: `strategy/board-snapshots/projections/sleeper-2026.json`. GP snapshots: `hashtag-gp-2026.json`, `fanscout-gp-2026.json`. **Re-run rate + both GP snapshots before any eval.**

## Manual overrides

When a feed still prices a player the league knows is out (`overrides-2026.json`), set
`gp` and/or `rate` there. The sim reads overrides **after** the feed and refresh never
touches the file — add a row, re-run evals; remove it when the feeds catch up.

```json
"Shaedon Sharpe": {"gp": 0, "reason": "out for season"}
```

Only `gp` and `rate` are honored; `reason` is for humans. A `gp` override moves the season columns only — formula `Δw` floors `GP` at the durability map (`Delta w.md`).

## What the scoring does

`scoring.py` is the executable copy of `league-info` §Scoring, verified exact against
Fleaflicker's own `pointsActual` on 4352/4352 played-game rows.

| | |
| --- | --- |
| `fantasy_points(line)` | one game's raw line |
| `rate(avg_line)` | a **season-average** line — what a projection is |

**Score a projection with `rate()`, never `fantasy_points()`.** Every term is linear under
averaging except the DD/TD bonus, which is a per-game threshold: counting it off the
averages charges +2 to every game of a 10.1-rebound player and nothing to a 9.9-rebound
one — up to **2.7 FPts/G**, enough to reorder rows. `rate()` pays each category its Poisson
probability of reaching 10 (mean error **0.09** against **0.54**).

Two feed traps, both handled in `line_from_sleeper`:

- **`OReb = reb − dreb`** — the feed publishes the total and the defensive half only.
- **Never use the feed's own `dd`/`td`** — missing on 45 of the top 150 scorers, and
  missing is indistinguishable from zero.

## Joining names

Same hazard as the boards (`eval-player` §*Joining names to board rows*) — a failed join
and a player with no projection both leave a stale rate wearing a fresh label. `index()`
**refuses** a normalised-name collision; `apply()` returns the unmatched names. The feed
drops generational suffixes Fleaflicker keeps.

A player with no projection keeps last season's rate and **must carry `no projection`**
(`Eval Template.md`).

## Projected GP

Sleeper's `gp` field is a per-game dummy (`1.0`) — not season GP.

Hashtag: `fantasy-basketball-projections`, `DDSHOW=900`, `DDDURATION` = 2026-27 Rest of Season
(not STREAM / short-term). Preseason ROS is a season projection; once games have been
played, that column is games **remaining** and is not season GP.
`hashtag_gp.py refresh` writes `strategy/board-snapshots/projections/hashtag-gp-2026.json`.

FanScout: `fanscout_gp.py refresh` writes `strategy/board-snapshots/projections/fanscout-gp-2026.json`
(names, GP, fetch time, incoming-rookie proof). Fetches `?players=1000` — the site defaults to
the top 150 — and refuses under 400 rows. Parse refuses unless AJ Dybantsa,
Darryn Peterson and Cameron Boozer are on the board — the site has served the previous
season under a current-season title.

`sim.project_gp` is mean(Hashtag, FanScout) when both hit; the one feed if only one hits; the durability map only if neither (`Eval Definitions §Durability`). Map is fallback, not a vote. Refreshing Hashtag GP always refreshes FanScout too.

## Adding a source

One source is a house view, not a market. Blend when a second lands, and re-cut every eval
that quoted the old rate.

| | |
| --- | --- |
| Hashtag Basketball | `hashtagbasketball.com/fantasy-basketball-projections` — free, 465 players at `DDSHOW=900`, and `hashtag-basketball` already has the postback harness. **OREB and DREB are their own columns via the `CBOREB`/`CBDREB` checkboxes**, off by default; makes and attempts live inside the percentage cells (`0.574 (10.5/18.3)`). Poll `DDDURATION` for a `2026-27` value — the control is season-scoped and rolls forward |
| Basketball-Reference SPS | `basketball-reference.com/friv/projections.cgi` — free, 581 players, ORB split. **Per-36 only**, so it needs a minutes assumption we would be supplying ourselves |

Two traps on a Hashtag **rate** pull: `/fantasy-basketball-points-league-projections`
drops OREB/DREB, so pull the 9-cat projections page with the checkboxes, not the points
page. GP snapshots are `hashtag_gp.py refresh` / `fanscout_gp.py refresh`, not this table.

**No board we already use carries stat projections.** Dizzle is rank-only (its rookie stat
block is NCAA actuals); Dynatyze has no NBA projection surface; the Hashtag *expert
dynasty* board's stat line is realized actuals. Don't re-check these hoping otherwise —
only Hashtag's projections page is a rate path.

Checked and rejected: FantasyPros (no makes/attempts at all) · DARKO, Dunks & Threes, BBall
Index (impact metrics, no box line) · Basketball Monster, RotoWire direct, FantasyLabs
(paywalled) · Fantasy Nerds, numberFire, RotoGrinders (dead). DFS/props are game-level and
never reach 400 players.
