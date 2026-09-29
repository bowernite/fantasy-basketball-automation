---
name: eval-team
description: How to produce a team's eval files — human file plus agent .team.md. Which columns to pull, what to compute, and what the files may and may not contain.
---

Your only job is to create the updated eval files for a team, in `evals/teams/` (§Output).

`Eval Definitions` owns every formula, threshold and column meaning — cite it by section, never restate it. `template.md` (this directory) owns section order.

# Launch first

**Spawn these before reading anything else, in parallel** (`CLAUDE.md` §Subagents). Read `Eval Definitions.md` and `template.md` while they run.

| Subagent | Hands back |
| --- | --- |
| **boards** | each blended board's rank per player, its depth, and its stamp |
| **picks** | pick ownership per `eval-pick` |

`team-info` maps owner → `team_id`.

# Inputs

Already on disk — nothing here needs fetching:

- **Sim** — counterparty table: `evals/lineup-math/run sim_run.py --eval <team_id>` · `sims` Skill · `README.md` §*Pricing a counterparty*
- **Rosters** — `evals/lineup-math/rosters/roster-<team_id>-<season>.json`, all 12. `evals/lineup-math/run fetch_data.py roster <team_id>` re-cuts one and applies assumed-through overlays (`Pending Trades.md`). Do not quote the wire over those files.
- **Boards** — `evals/board-snapshots/`, latest dated pull.

# When to pull new data

- Boards: only if asked.
- Sims: `sims` Skill reports when writing the eval, and whenever the eval predates the roster file or the projection snapshot. Anything else only if asked.
- Roster: only if asked. **If the roster fetch is over 3 months old, stop and ask before re-fetching.**
- Player ages: Use DOB if we have it anywhere (e.g. a draft board file). Otherwise, fallback to calculating it fresh, but only if the last time we sourced (for the particular player / team) is more than 2 months ago

# Applying it

_See /evals/Definitions/Eval Definitions.md for definitions to these when needed_

Calculate these columns for each player to construct the player table

1. **BASE** - calculate for each player
2. **Sim columns** — counterparty: `evals/lineup-math/run sim_run.py --eval <team_id>`. Copy the TSV (`Δw`, `Δw (season) ours`, `Δw (season) theirs`, `ΔP(title) ours`, `W20`–`W23`). Do not import `sim` for these columns. Do not write scripts (`CLAUDE.md` §Scripts). Do not assign `ROSTER`. Ours (`my-team/`): `./run sim.py players weeks` plus `player_title` / `title-column` `include: ["ours"]`. `sim.py title` is roster `P(title)` for `# Title odds`, not the table column.
3. Flags travel with every row. Multi-piece sides get one joint sim run each, never summed rows.

Column order and cell formats: `Eval Template.md`.

# Picks

Make tables for picks (see template file)

Every draft year the league has traded into, not just the next one

# Output

Two files, same directory, written together on every write — any edit to one goes in the other:

| File | Path |
| --- | --- |
| Human (Brett reads) | `evals/teams/<owner>/<Name>'s Team.md` · ours `My Team.md` |
| Agent | `evals/teams/<owner>/<Name>.team.md` · ours `Ours.team.md` · Matt Hlina `Hlina.team.md` |

Read the agent file only. Never read, grep, or shell-print the human file. Prior values you need (ages, notes) come from the agent file.

`template.md` (this directory) owns the human file's section order. Follow it and `Eval Definitions` for every human file so the eval set reads across.

The files answer: who is on this team, what each player is worth, roster shape, what to target.

Flag **sourced vs modelled** · any discount chosen · board staleness.

# Agent file

Same facts as the human file, trimmed. No markdown tables, bold, or italics. Values as the human file rounds them; strip `,` from numbers.

```
# {Owner} ({Team name}) · {N} bodies · {SIT} · sim {YYYY-MM-DD}
Stamps: boards {Dizzle M/D/YY · Hashtag M/D/YY · crowd M/D/YY} · proj {M/D/YY} · roster {M/D/YY} · AGE {M/D/YY}
Title: PF {rank}/12 ({PF}) · {wins} W · P(title) {x%} · ours P(title) {y%}
Notes: {team-specific reads only}

## Players
player | AGE POS | BASE | FPts/G GP | Δw Δw'26–'27-ours Δw'26–'27-theirs ΔP(title)-ours | flags
Shai Gilgeous-Alexander | 28.1 PG/SG | 9550 | 49 72 | +2.57 +2.01 +2.65 15.8%
σ: {adjacent pairs the sim does not resolve, e.g. Williams/Hendricks 1.4σ}

## Picks
pick | origin | rookie | VALUE
### Sept '26 — {human header text}
1.02 | own | AJ Dybantsa | 5959
own 1st | own (1.01–1.07 prior) | Cameron Boozer → Mikel Brown Jr. | ≤6757–2391
Gone: own 3.02 → Josh
```

- Ours: `Title:` drops the ours clause; the key drops `Δw…-theirs` and reads `ΔP(title)`.
- Players in the human file's order. FPts/G and GP are projections only. Omit a blank `| flags`; omit `σ:` when there are no ties.
- Picks: one key line under `## Picks`; keep each year's header and `Gone:` line. A year with no picks: `none held`. Drop Ordinal and rank.
- `Notes:` targets, role bets, feed misses, pending-trade overlays, pick caveats that change a VALUE read — anything a trade call would use. No definitions, formulas, methodology, `REPL`, or counterfactual text.
