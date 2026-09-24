# Durability

Expands `Eval Definitions §Durability`.

Our format prices a missed game the same way the boards do: **no format-derived injury adjustment**, never stacked on BASE, and **no fragility discount** — lineup lock-in doesn't change that. **Never accept less production to buy durability or lower variance**, and no third penalty on a fragile star bought with bodies.

Spend the effort on **expected `GP`**, identically on both sides of every deal:

- **Never hand-type `GP`, and never use current injury _status_** — a this-season fact in a dynasty league. Take it from `evals/lineup-math/run sim.py gp`, `--roster their.json` for a counterparty.
- **Last season's `GP` and rate only — no multi-season average, no age.** Neither beats one season. **`GP` is a defensible input, not a precise one** — never argue a trade on a few games.
- **`GP` is projected off last season's _actual_ rate, never the projected one** — that is the input the fit was built on, and a projected rate through it recalibrates every `GPp` in the study against a variable it never saw (`projections`).
- **`GPp` is `sim.project_gp`:** mean of Hashtag and FanScout projected GP when both hit; the one feed if only one hits; the durability map only if neither (`projections`). Map is fallback, not a vote. Refresh both feeds via `hashtag_gp.py refresh` / `fanscout_gp.py refresh`. Formula `Δw` alone floors `GPp` at the map (`Delta w.md`).
- **Flag, don't patch, two blind spots:** a fragment last season (**25 games or fewer** — the band has **no lower bound**, since a 5-game season is *present* in the pool rather than absent and is the thinnest evidence of all); and a whole missed season, absent from the fit rather than a zero — the projection is expected GP _given he plays_, blind to whole-year risk. **Both cap what a `Δw (season)` built on them can claim**, and the flag travels with the row.
- **A rotation season is a pool season at rate ≥ 15** — below that, `GP` measures _role_, not health. Fewer than 3 rotation seasons is thin evidence the role itself holds up (`Nyr role` flag, `Eval Template.md`). The same call applies inside a qualifying season: a player's first one or two seasons, an under-60 year spent earning a rotation spot (bench-to-starter climb, DNP-CDs before he won minutes) measures role, not health — name the cause (injury vs. earning-time) for every under-60 season cited.

The `GP` projection formula and its cross-validation are measured, not defined — `evals/lineup-math/findings.md` §*GP is the dominant input* owns the coefficients; this file owns only the rule for how to use them.
