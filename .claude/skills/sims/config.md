# Sim config schema

JSON only (stdlib). **Run configs** go in `$TMPDIR/ff-sim-<tag>.json` — not in `strategy/teams/`. **Agents:** edit JSON by hand; run `sim_run.py`; copy the big numbers from stdout / `results` into both shape files by hand (`trade-shapes`). Avoid your own scripts whenever possible; rely on your own logic. Archive via `trades` §Simming.

## Team shape archive

Read `strategy/teams/<owner>/<Name>.shapes.md`. Also write `<Name> Trade Shapes.md`. Never read the HTML file. Line format, tiers, and sort: `trade-shapes` Skill. Tier/sort rules: `trades` §Simming.

## Incremental runs

On `./run sim_run.py <file>`:

- **`trade-screen`** — skip deals that already have `results`; price only new deals.
- **`player-effects`** — skip sections that already have `player_results`.
- **`--refresh`** — re-run all trade sections/deals.
- **`"refresh": true`** on one section — re-run just that section (flag cleared on write).

After a run, copy the big numbers into both shape files (`trade-shapes`). Tmp JSON is disposable.

`reports` / `title-column` always run when present (eval configs in `lineup-math/sims/`).

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

Single-section configs `{ "kind": "..." }` still work for one-off runs in `lineup-math/sims/`.

## `trade-screen`

Joint `Δw (season)` and `ΔP(title)`, one row per deal. Each deal gets `results` after it runs: `score_us` (`Eval Definitions §Score`; `null` without `delta_base_us`), `delta_base_us`, `fdw_us` (formula `Δw`), `dw_us` (`Δw (season)`), `dp_title_us`, `dage_us` (`Δage`, `trades` §Age; `null` when a name has no eval row), `cut_us` / `cut_them` (bodies the sim cut to keep that side at 38, `trades` §Uneven bodies), and their-side `fdw_them` / `dw_them` / `dp_title_them`, plus `simmed` (e.g. `8/20/26`). The section gets `meta.simmed` when any deal in it is priced; the file gets top-level `meta.simmed` on write-back.

**Picks** — player arrays only; add BASE via integer fields (price with `eval-pick` Skill):

| Field | When |
|---|---|
| `out_us_extra_base` | Our picks to them (sum if multiple) |
| `in_from_us_extra_base` | Their picks to us (sum if multiple) — despite the name, **not** a mirror of `out_us_extra_base` |

Each pick goes in exactly one field; setting both for the same pick nets it to 0. Player arrays still need full mirrors (`out_us`, `in_from_them`, `out_them`, `in_from_us`). Show picks in the `.md` **Out** column in parentheses; the JSON carries the BASE integer separately. Picks move no bodies in any win column. `dage_us` reads picks (rounds 1–4) from the deal `label`, which must be the `.shapes.md` line's `out > in` (e.g. `Cade+Chris '27 2nd > SGA`). A `*_picks` field refuses.

**Stdout → archive:** `score_us` → **Score** · `delta_base_us` → **ΔBASE** · `fdw_us` → **Δw** · `dw_us` → **Δw (season)** · `dp_title_us` → **ΔP(title)** · `dage_us` → **Δage**. Round per `trade-shapes` Skill.

## `player-effects`

Isolated incoming value. Section gets `player_results` after it runs. `source: "their"` = their names incoming onto us (eval `ours` columns). `source: "us"` = our names incoming onto them. Unknown names refuse. A full 38-man side makes room by cutting its worst body (`sim.arrival_basis`, `trades` §Uneven bodies); `eval-columns` and `title-column` do the same on ours.

## `reports` / `title-column`

Eval refresh only — stdout, no write-back. See `./run sim.py --help`.

## `eval-columns`

Counterparty eval player table. `their_roster` is a team id. No `roster` key — incoming is always on us. Optional `names` subsets the roster.

```json
{"kind": "eval-columns", "their_roster": 161014}
```

```
./run sim_run.py --eval 161014
```

Ours (`my-team/`): `./run sim.py players weeks` plus `player_title` / `title-column` `include: ["ours"]`, not this kind. `sim.py title` is roster `P(title)` only.

## Examples

- Team archive: `strategy/teams/josh/Josh.shapes.md` (and `Josh Trade Shapes.md`, write only)
- Run config: `$TMPDIR/ff-sim-josh-kawhi.json`
- `strategy/lineup-math/sims/examples/eval-columns.json`
