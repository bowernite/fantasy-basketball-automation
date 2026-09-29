---
name: sims
description: Run lineup-math sims from JSON config — trade screens, player effects, eval reports. Run configs in $TMPDIR; --refresh re-prices all. Archive the big numbers into the team's .shapes.md and Trade Shapes.md (trades §Simming).
---

# Agent workflow — JSON only

Avoid writing your own scripts whenever possible; rely on your own logic instead. For pricing, use JSON + `sim_run.py` — not generators, tier scripts, or “read JSON and write `.md`” helpers.

1. **Write** `$TMPDIR/ff-sim-<tag>.json` (`trade-screen` deal bodies; picks via `out_us_extra_base` — see [config.md](config.md)).
2. **Run** `strategy/lineup-math/run sim_run.py` on that file (or `--refresh`).
3. **Read** stdout table **and** `results` written back into the JSON.
4. **Archive** the big numbers into both `strategy/teams/<owner>/<Name>.shapes.md` and `<Name> Trade Shapes.md` by hand (`trade-shapes`) — **required** after trade-with / trade screening when new deals were priced (unless the user opts out). Read `.shapes.md` only. Tier and sort per `trades` §Simming.

Eval refresh: `./run sim_run.py --eval <team_id>`. Other reports: `./run sim.py --help`. Use `sim_run.py` / `sim.py` — not your own imports of `sim` or `simlib`.

# Run

```bash
strategy/lineup-math/run sim_run.py "$TMPDIR/ff-sim-<tag>.json"
strategy/lineup-math/run sim_run.py --refresh "$TMPDIR/ff-sim-<tag>.json"
strategy/lineup-math/run sim_run.py --check <config.json>
strategy/lineup-math/run sim.py --help
```

Tmp path helper: `simlib.runner.sim_tmp_path("josh-kawhi")` → `$TMPDIR/ff-sim-josh-kawhi.json`.

`trade-screen` and `player-effects` write results back into the JSON. **Already-simmed deals are skipped** — append new deals, run, only the new rows compute. `--refresh` or `"refresh": true` on a section re-runs that block.

Schema: [config.md](config.md).

# Where things live

| What | Path |
|---|---|
| Run configs | `$TMPDIR/ff-sim-<tag>.json` — ephemeral; never commit |
| Eval refresh, league-wide | `strategy/lineup-math/sims/` |
| Team shape archive | `strategy/teams/<owner>/<Name>.shapes.md` (read this) and `<Name> Trade Shapes.md` (write only) — `trades` §Simming |

# Refresh

Normal run skips anything already priced in the **JSON**. Re-run when inputs changed (roster, projections) or you edited deal bodies in place.

| Flag | Effect |
|---|---|
| *(default)* | Skip deals with `results`; skip `player-effects` sections with `player_results` |
| `--refresh` on CLI | Re-price **all** trade sections in the file |
| `"refresh": true` on a section | Re-price **that section only** (flag cleared when results write back) |

Rebuild tmp JSON from `.shapes.md` rows + eval rosters (edit JSON directly), then `--refresh`. Update both archives' big numbers from stdout / JSON `results` (`trade-shapes`).

# When

- Confirming a trade short list (`trades` §Brainstorm, §Simming)
- Cross-roster player effects (tmp JSON; no `.md` archive unless asked)
- Eval sim columns (`eval-team`): `./run sim_run.py --eval <team_id>` (`eval-columns`). Do not import `sim` for those columns.
- Any built-in report from `sim.py --help`

# Future seasons

`strategy/lineup-math/run sim.py future` (~1 min, all cores): each team's PF, PF rank and P(title) for seasons 1–7, with pick counts and roster flow per draft. Reads every roster file, `data/picks-2025-26.json` (pick ledger) and `data/progression-params.json`. Its preamble lists the assumptions and known biases. Quote them with the numbers.

After a trade, an injury, or a projections / boards / BASE refresh:

1. Run `sim.py future` before the change, if its last run predates the current inputs. This is the baseline.
2. Update the inputs:
   - Trade: `./run fetch_data.py roster` and `./run fetch_data.py picks`.
   - Injury or projections: `projections`.
   - Boards: the board's skill.
3. Run `sim.py future` again and read `Δ vs last run`. The seeds are fixed, so a Δ is the change and not noise.

Never refit `progression-params.json` for this. That's once per offseason, per `fit_progression.py`'s docstring.

# Write configs, not scripts

**Agents: JSON + `sim_run.py` for pricing**; tier, sort, and archive by hand. Avoid your own scripts whenever possible — rely on your own logic. The table below is the config surface.

| Need | `kind` |
|---|---|
| `sim.py` report(s) | `reports` |
| Deal table — joint `Δw (season)` and `ΔP(title)` | `trade-screen` |
| Isolated player `Δw (season)` / `ΔP(title)` | `player-effects` |
| Full-roster ΔP(title) column | `title-column` |
| Counterparty eval player table | `eval-columns` / `--eval <team_id>` |

Multi-part: top-level `"sections": [ {...}, {...} ]`. Tag sections with `"label": "kawhi"` etc.

`their_roster` / `roster`: team id or roster filename. Id → `team-info`.

Uneven body-count deals: `trades` §Uneven bodies.

# Output

Stdout TSV per deal (`Score us`, `ΔBASE us`, `Δw us`, `Δw '26–'27 us`, `ΔP(title) us`, `Δage us`, …). Same numbers land in JSON `results` (`score_us` = `Score`, `dage_us` = `Δage`).
