---
description: Check newly available free agents (cuts, new pool entrants) since the last check and say whether any beat a body on our roster. Use when Brett asks to check free agents / the wire / who got cut.
---

Read `last-checked.txt` (this directory; ISO UTC, one line). Missing → ask Brett for a start point. Everything below covers only what happened after it. Today's snapshot of what a pickup must beat: the `Score` column in `strategy/teams/my-team/Ours.team.md` (`Score.md` §Player Score).

## 1. Find candidates

One `general-purpose` subagent (`get-league-info` §*Fetch in a subagent*) hands back a table: player, NBA team, position, age, who cut him and when, `seasonAverage`/GP.

- `FetchLeagueTransactions`: page until older than the timestamp. Candidates = drops (`TRANSACTION_DROP`) after it.
- Drop candidates already re-rostered (`FetchLeagueRosters`) or re-added since. Keep the rest.
- `FetchPlayerListing?filter.free_agent_only=true&sort=SORT_SEASON_AVERAGE`: add any pool player with a fresh rate not already listed (e.g. new NBA signing).
- Name the owner by `team-info` Name. Mention any `FetchLeagueTransactions` commissioner rules change since the timestamp.

## 2. Price them

- Rate: the projection snapshot (`projections` Skill). A player missing from it has no projection: say so, don't guess.
- BASE: `eval-player` `base.py` (`--absent NAME` only after hand-checking each board).
- Sim: `sims` `player-effects` onto our roster (`config.md` §`player-effects`, free-agent temp roster). Score by `Score.md` §Player Score.
- Skip bodies with an obvious no (no projection, no board rank, out for the season) after a one-line reason.

## 3. Report

Table: candidate · Score · vs our lowest Score bodies. A pickup = Score above our worst body's, and name who gets cut. Bare list otherwise. Offseason FA lock (`league-info` §Offseason transaction lock) → say adds may be locked; the API can't show it.

## 4. Stamp, then offer a refresh

Write the current UTC time to `last-checked.txt`. Then ask Brett whether to do a full refresh: projections (`projections` Skill: `sleeper.py refresh`, both GP snapshots), boards for these players (`hashtag-basketball`, `dizzle-dynasty`), then redo step 2. Don't refresh unasked.
