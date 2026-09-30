# Sim config schema

JSON only (stdlib), edited by hand. Run configs go in `$TMPDIR/ff-sim-<tag>.json` (workflow, incremental runs and `--refresh`: `sims` Skill). League-wide eval configs live in `strategy/lineup-math/sims/`; single-section configs `{ "kind": "..." }` work there for one-off runs.

## Shape

```json
{
  "sections": [
    {
      "label": "kawhi",
      "kind": "trade-screen",
      "their_roster": 161024,
      "their_label": "Josh",
      "deals": [{ "label": "...", "out_us": [], "in_from_them": [], "out_them": [], "in_from_us": [] }]
    }
  ],
  "meta": { "simmed": "8/30/26", "dp_title_note": "both rosters change in the 12-team field" }
}
```

## `trade-screen`

Joint `Δw (season)` and `ΔP(title)`, one row per deal. Each deal gets `results` after it runs:

- `score_us` (`Eval Definitions §Score`; `null` without `delta_base_us`)
- `delta_base_us`: named players' BASE from each side's `<Name>.team.md`, plus pick fields
- `fdw_us` (formula `Δw`), `dw_us` (`Δw (season)`), `dp_title_us`
- `dage_us` (`Δage`, `trades` §Age; AGE / FPts/G / GP from the same files)
- `eval_gap`, only when set: why `delta_base_us` / `dage_us` are `null` (e.g. a named player missing from the `.team.md`, or a label pick with its BASE field unset); stdout prints it as a `! <label>:` line. Fix the eval or config, then `--refresh`
- `cut_us` / `cut_them`: bodies the sim cut to keep that side at 38 (`trades` §Uneven bodies)
- their side: `fdw_them` / `dw_them` / `dp_title_them`
- `simmed` (e.g. `8/20/26`)

The section gets `meta.simmed` when any deal in it is priced; the file gets top-level `meta.simmed` on write-back. Results → archive columns and rounding: `trade-shapes` §Workflow.

### Picks

Player arrays hold players only; add pick BASE via integer fields (price with `eval-pick` Skill):

| Field | When |
|---|---|
| `out_us_extra_base` | Our picks to them (sum if multiple) |
| `in_from_us_extra_base` | Their picks to us (sum if multiple). Despite the name, **not** a mirror of `out_us_extra_base` |

- Each pick goes in exactly one field; setting both for the same pick nets it to 0. A `*_picks` field refuses.
- Player arrays still need full mirrors (`out_us`, `in_from_them`, `out_them`, `in_from_us`).
- Picks move no bodies in any win column.
- `dage_us` reads picks (rounds 1–4) from the deal `label`, which must be the `.shapes.md` line's `out > in` (e.g. `Cade+Chris '27 2nd > SGA`). `.md` pick format: `trade-shapes`.

## `player-effects`

Isolated incoming value; the section gets `player_results` after it runs.

- `source: "their"` = their names incoming onto us (eval `ours` columns); `source: "us"` = our names incoming onto them. Unknown names refuse.
- A free agent: a temp `rosters/roster-fa-tmp.json` (roster-file rows, rates off `data/players-<season>.json`) as `their_roster`; delete it after.
- A full 38-man side makes room by cutting its worst body by `Score`, whoever arrives (`sim.arrival_basis`, `trades` §Uneven bodies); `eval-columns` and `title-column` do the same on ours.

## `reports` / `title-column`

Eval refresh only: stdout, no write-back. See `./run sim.py --help`.

## `eval-columns`

Counterparty eval player table. `their_roster` is a team id; no `roster` key (incoming is always on us). Optional `names` subsets the roster.

```json
{"kind": "eval-columns", "their_roster": 161014}
```

Same as `./run sim_run.py --eval 161014`. Example: `strategy/lineup-math/sims/examples/eval-columns.json`.

Ours (`strategy/teams/my-team/`): `./run sim.py players weeks` plus `player_title` / `title-column` `include: ["ours"]`, not this kind. `sim.py title` is roster `P(title)` only.
