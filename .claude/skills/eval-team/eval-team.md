---
description: Use when creating or updating a team's eval files (`<Name>.team.md` and its human file)
---

Goal: the updated eval files for one team in `strategy/teams/` (§Output). The files answer: who is on this team, what each player is worth, roster shape, what to target.

`Eval Definitions` owns every formula, threshold and column meaning: cite it by section. `template.md` (this directory) owns the human file's section order; `Eval Template.md` owns column order and cell formats.

# Launch first

**Spawn these in parallel before reading anything else** (`AGENTS.md` §Subagents). Read `Eval Definitions.md` and `template.md` while they run.

| Subagent | Hands back |
| --- | --- |
| **boards** | each blended board's rank per player, its depth, and its stamp |
| **picks** | pick ownership and VALUE per `eval-pick`, every draft year the league has traded into |

`team-info` maps owner → `team_id`.

# Inputs

Already on disk, nothing to fetch:

- **Sim**: counterparty table `strategy/lineup-math/run sim_run.py --eval <team_id>` · `sims` Skill · `strategy/lineup-math/README.md` §*Pricing a counterparty*
- **Rosters**: `strategy/lineup-math/rosters/roster-<team_id>-<season>.json`, all 12. `strategy/lineup-math/run fetch_data.py roster <team_id>` re-cuts one. Quote these files, not the wire.
- **Boards**: `strategy/board-snapshots/`, latest dated pull.

# When to pull new data

- Boards: only if asked.
- Sims: `sims` Skill reports when writing the eval, and whenever the eval predates the roster file or the projection snapshot. Anything else only if asked.
- Roster: only if asked. **If the roster fetch is over 3 months old, stop and ask before re-fetching.**
- Player ages: use DOB if we have it anywhere (e.g. a draft board file). Otherwise re-derive it, only if it was last sourced (for that player / team) more than 2 months ago.

# Player table

Per player:

1. **BASE** (`eval-player`).
2. **Sim columns**: counterparty: `strategy/lineup-math/run sim_run.py --eval <team_id>`; copy the TSV (`Δw`, `Δw (season) ours`, `Δw (season) theirs`, `ΔP(title) ours`, `W20`–`W23`), without importing `sim` or assigning `ROSTER`. Ours (`my-team/`): `./run sim.py players weeks` plus `player_title` / `title-column` `include: ["ours"]` (`eval-player` step 7).
3. **Score**: per row, from that row's columns: `Score.md` §Player Score.
4. Flags travel with every row. Multi-piece sides get one joint sim run each, never summed rows.

Done when every rostered body has a full row.

# Output

Two files, same directory, written together on every write; any edit to one goes in the other:

| File | Path |
| --- | --- |
| Human (the user reads) | `strategy/teams/<owner>/<Name>'s Team.md` · ours `My Team.md` |
| Agent | `strategy/teams/<owner>/<Name>.team.md` · ours `Ours.team.md` · Matt Hlina `Hlina.team.md` |

Prior values you need (ages, notes) come from the agent file. Write the agent file first, then spawn a subagent to write the human file in full from it plus this run's outputs, `template.md` and `Eval Template.md` (`AGENTS.md` §Team files).

Flag **sourced vs modelled** · any discount chosen · board staleness.

Done when both files are written in this run and carry the same facts.

# Agent file

Same facts as the human file, trimmed. Plain text: no markdown tables, bold, or italics. Values unrounded (sims read them): BASE, FPts/G, GP, Score integers · win columns two decimals · `ΔP(title)` one decimal; strip `,` from numbers.

```
# {Owner} ({Team name}) · {N} bodies · {SIT} · sim {YYYY-MM-DD}
Stamps: boards {Dizzle M/D/YY · Hashtag M/D/YY · crowd M/D/YY} · proj {M/D/YY} · roster {M/D/YY} · AGE {M/D/YY}
Title: PF {rank}/12 ({PF}) · {wins} W · P(title) {x%} · ours P(title) {y%}
Notes: {team-specific reads only}

## Players
player | AGE POS | BASE | FPts/G GP | Δw Δw'26–'27-ours Δw'26–'27-theirs ΔP(title)-ours | Score | flags
Shai Gilgeous-Alexander | 28.1 PG/SG | 9550 | 49 72 | +2.57 +2.01 +2.65 15.8% | 12088
σ: {adjacent pairs the sim does not resolve, e.g. Williams/Hendricks 1.4σ}

## Picks
pick | origin | rookie | VALUE
### Sept '27 — {human header text}
own 1st | own (1.01–1.07 prior) | {rookie} → {rookie} | ≤6757–2391
Gone: own 3rd → Josh
```

- Ours: `Title:` drops the ours clause; the key drops `Δw…-theirs` and reads `ΔP(title)`.
- `Score` sits after the win columns on every row; sort stays by BASE.
- Players in the human file's order. FPts/G and GP are projections only. Omit a blank `| flags`; omit `σ:` when there are no ties.
- `trade-screen` sims read each `## Players` row's name, AGE, BASE, FPts/G and GP by position: keep the first four columns as keyed, ` | ` separators, BASE a bare integer, AGE `–` when unknown.
- Picks: one key line under `## Picks`; keep each year's header and `Gone:` line. A year with no picks: `none held`. Drop Ordinal and rank.
- `Notes:` holds targets, role bets, feed misses, pick caveats that change a VALUE read: anything a trade call would use. Definitions, formulas, methodology, `REPL` and counterfactual text stay out.
