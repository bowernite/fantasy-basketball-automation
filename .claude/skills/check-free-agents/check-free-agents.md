---
description: Use when the user asks to check free agents, the wire, or who got cut
---

Read `last-checked.txt` (this directory; ISO UTC, one line); missing → ask the user for a start point. Everything below covers only what happened after it. The bar a pickup must beat: the `Score` column in `strategy/teams/my-team/Ours.team.md` (`Score.md` §Player Score).

## 1. Find candidates

One `general-purpose` subagent (`get-league-info` §Fetch in a subagent) hands back a table: player, NBA team, position, age, who cut him and when, `seasonAverage`/GP.

- `FetchLeagueTransactions`: page until older than the timestamp. Candidates = drops (`TRANSACTION_DROP`) after it
- Remove candidates already re-rostered (`FetchLeagueRosters`) or re-added since
- `FetchPlayerListing?filter.free_agent_only=true&sort=SORT_SEASON_AVERAGE`: add any pool player with a fresh rate not already listed (e.g. new NBA signing)
- Flag any commissioner rules change in `FetchLeagueTransactions` since the timestamp

Done when the table covers every post-timestamp drop still unowned plus fresh pool entrants.

## 2. Price them

- Rate: the projection snapshot (`projections` Skill). A player missing from it has no projection: say so, don't guess
- BASE: `eval-player` `base.py` (`--absent NAME` only after hand-checking each board)
- Sim: `sims` `player-effects` onto our roster (`config.md` §`player-effects`, free-agent temp roster). Score by `Score.md` §Player Score
- Skip obvious nos (no projection, no board rank, out for the season) with a one-line reason

Done when every candidate has a Score or a one-line skip reason.

## 3. Report

Table: candidate · Score · vs our lowest-Score bodies. A pickup = Score above our worst body's; name who gets cut. Bare list otherwise. During the offseason FA lock (`league-info` §Offseason transaction lock), say adds may be locked; the API can't show it.

## 4. Stamp, then offer a refresh

Write the current UTC time to `last-checked.txt`. Then ask the user whether to do a full refresh: projections (`projections` Skill: `sleeper.py refresh`, both GP snapshots), boards for these players (`hashtag-basketball`, `dizzle-dynasty`), then redo step 2. Refresh only when asked.
