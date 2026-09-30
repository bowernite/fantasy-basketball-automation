---
description: Sims — use when pricing trades or player effects with lineup-math, refreshing eval sim columns, running a `sim.py` report, or re-running `sim.py future` after a trade, injury or projections/boards/BASE refresh
---

# Agent workflow

Price with JSON configs + `sim_run.py` (schema: [config.md](config.md)); for a live trade that's a `trade-screen` config, not the import route `sim.py --help` mentions.

1. **Write** `$TMPDIR/ff-sim-<tag>.json` (`simlib.runner.sim_tmp_path("<tag>")` gives the path): `trade-screen` deal bodies, picks via `out_us_extra_base` / `in_from_us_extra_base` (config.md §Picks). Run configs are ephemeral; never commit them.
2. **Run** `strategy/lineup-math/run sim_run.py` on that file (`--refresh` when inputs changed, §Refresh).
3. **Read** the stdout table **and** the `results` written back into the JSON.
4. **Archive**, **same session, before returning**: after pricing new deals (trade-with, negotiation, screening), copy the big numbers by hand into both `strategy/teams/<owner>/<Name>.shapes.md` and `<Name> Trade Shapes.md` per `trade-shapes` §Workflow (tiers, sort, rounding). Skip only when the user opts out or the run priced no new bodies. Done when every newly priced deal has a row in both files.

```bash
strategy/lineup-math/run sim_run.py "$TMPDIR/ff-sim-<tag>.json"             # new deals only
strategy/lineup-math/run sim_run.py --refresh "$TMPDIR/ff-sim-<tag>.json"   # re-price all
strategy/lineup-math/run sim_run.py --check <config.json>                    # validate a config
strategy/lineup-math/run sim_run.py --eval <team_id>                         # counterparty eval columns
strategy/lineup-math/run sim.py --help                                       # built-in reports
```

# When

| Need | How |
|---|---|
| Confirm a trade short list (`trades` §Simming) | `trade-screen`: deal table, joint `Δw (season)` and `ΔP(title)` |
| Isolated player `Δw (season)` / `ΔP(title)`, cross-roster | `player-effects` (tmp JSON; no `.md` archive unless asked) |
| Counterparty eval sim columns (`eval-team`) | `sim_run.py --eval <team_id>` (kind `eval-columns`) |
| Full-roster ΔP(title) column | `title-column` |
| Any built-in `sim.py` report | `reports`, or run `sim.py <report>` directly |

Multi-part: top-level `"sections": [ {...}, {...} ]`, each tagged `"label": "kawhi"` etc. `their_roster` / `roster`: team id (→ `team-info`) or roster filename. Uneven body counts: `trades` §Uneven bodies.

Stdout: TSV per deal (`Score us`, `ΔBASE us`, `Δw us`, `Δw '26–'27 us`, `ΔP(title) us`, `Δage us`, …); the same numbers land in JSON `results` (fields: config.md §`trade-screen`).

# Refresh

A normal run skips anything already priced **in the JSON**: append new deals and only those compute. Re-price when inputs changed (roster, projections/GP snapshot) or you edited deal bodies in place.

| Flag | Effect |
|---|---|
| *(default)* | Skip deals with `results`; skip `player-effects` sections with `player_results`; `reports` / `title-column` always run |
| `--refresh` on CLI | Re-price **all** trade sections in the file |
| `"refresh": true` on a section | Re-price **that section only** (flag cleared on write-back) |

Re-pricing archived shapes: `trade-shapes` §Workflow.

# Future seasons

`strategy/lineup-math/run sim.py future` (~1 min, all cores): each team's PF, PF rank and P(title) for seasons 1–7, with pick counts and roster flow per draft, and each original team's own-pick slot band (`eval-pick` prices later drafts off it). Reads every roster file, `data/picks-2025-26.json` (pick ledger) and `data/progression-params.json`. Its preamble lists the assumptions and known biases; quote them with the numbers. Season 1 there runs on the model's GP; the year-1 numbers of record are `sim.py title`.

After a trade, an injury, or a projections / boards / BASE refresh:

1. Run `sim.py future` before the change for a baseline. The baseline is whatever run came last, by anyone (`$TMPDIR/ff-sim-future-last.json`).
2. Update the inputs:
   - Trade: `./run fetch_data.py roster` and `./run fetch_data.py picks`.
   - Injury or projections: `projections`.
   - Boards: the board's skill.
3. Run `sim.py future` again and read `Δ vs last run`. Seeds are fixed, so an unchanged input repeats to the digit; a change reshuffles later draft orders, which moves every team a little. Cells under the printed floor are that drift. Done when `Δ vs last run` is read against that floor.

Leave `progression-params.json` as-is here; refitting is once per offseason, per `fit_progression.py`'s docstring.
