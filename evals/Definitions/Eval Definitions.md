# Eval Definitions

Single source of truth for every shared definition, formula and threshold used to value a player, a team or a pick. **Nothing here is dated or team-specific** — no board stamps, no measured `REPL` figures, no roster numbers. Those are measurements and belong in the dated output that produced them (`evals/teams/*/*.md`, `evals/lineup-math/`).

**Cite this file by section (`Eval Definitions §X`) instead of restating any of it.** The test before writing a sentence anywhere else: if it would be true and word-for-word identical for every player, every team and every trade, it's a definition — cut it and cite the section.

**Every section here is a definition and a pointer.** The rules, formulas, thresholds and edge cases live in the linked file — **read it before applying the term**, never off the gloss alone.

What an eval **publishes** is `Eval Template.md`. When and how to apply this: `eval-team` · picks `eval-pick` · negotiation `trades` · our own roster `evals/teams/my-team/Ours.team.md`.

# The three layers

Every eval publishes three things, side by side, never folded into one number:

| Layer | What it answers | Where it comes from |
|---|---|---|
| **BASE** | Market price, dynasty-wide — what he costs | External boards (§BASE) |
| **`Δw`** | Single-season wins a typical team gets from his rate and healthy GP | league curve (§Δw) |
| **`Δw (season)`** | Wins added to a specific roster, that fantasy season | The sim (§Δw (season)) |
| **`SIT`** | How much a win is worth to that team right now | Judgment: contending / fringe / tanking (§SIT) |

**BASE owns everything multi-year** — trajectory, age, upside, risk: the boards price all of it into the rank, and nothing in this repo re-derives or stacks on top of that (`AGENTS.md` §Objective). **Formula `Δw` owns typical-team fielded value** — scoring weights, GP, and the 9-slot cap as a league-average curve, no specific roster. **`Δw (season)` owns this roster and the calendar**. The gap between BASE and either win column is the signal; `SIT` says which one the current season should listen to.

**There is deliberately no exchange rate between BASE and either win column** — no constant converts wins into BASE units, and none may be derived or remembered. A deal that needs one to look good is a tie. **Formula `Δw` and `Δw (season)` are also not interchangeable** — never convert or net them.

# Building a table

## BASE

Blended points-format dynasty board rank, converted to a value. Pure market price; **no adjustment by us for injury, durability, role, team situation, contract or aging** — the rank prices all six. `D` is the league's total rostered players; past it a player is free.

**A summed `ΔBASE` is a point value only at equal body count with no picks** — otherwise a swept band, and a band spanning zero is a BASE tie.

Boards and weights, the `V()` curve, `D` and `roster_size`, summing across a package, depth and absence, the board-split flag: `BASE.md`.

## Columns

What an eval publishes alongside BASE, never folded in — `Boards`, `FPts/G proj (last)`, `GP proj (last)`, **`Δw`**, `Δw (season)`, `AGE`, `POS`, `W20`–`W23`.

The column table with each column's source and cell format, the printing rules, and why no format-fit column exists: `Columns.md`.

## Sourced vs modelled

The classification every eval must flag: a market/API fact, a figure we derived, or a judgment that is not a value at all.

The full classification table: `Columns.md` §Sourced vs modelled.

## `Δw`

Formula wins a typical team in this format gets from the player's rate and GP — league curve, ~600 PF per win. Not roster-specific, and blind to this season's absences: `GPp` floored at the durability map. `Δw (season)`, `ΔP(title)` and `W20`–`W23` carry the absence. One column on every table. **Eval files and trade tables both publish it alongside `Δw (season)`** — eval player tables before the season-tagged columns (`Eval Template.md`).

Formula, `R`, `K`, and when not to use it: `Delta w.md`.

## `Δw (season)`

Sim-measured wins a player adds to a specific roster that fantasy season, over the 19 regular matchups `sim.py` prices (period 20 / W20 excluded — bracket R1). Published as **`Δw 'YY–'YY`** (e.g. `Δw '26–'27 ours`). One season, one roster — multi-year value is BASE's entirely. **`Δw (season) ours` is the only cross-team-comparable column.**

The basis, the counterfactual, `incoming_wins`, and every prohibition on summing, discounting or shortlisting off it: `Delta w (season).md`.

## Durability

Expected `GP`: mean(Hashtag, FanScout) when both hit; the one feed if only one hits; durability map only if neither. Map is fallback, not a vote. **No format-derived injury adjustment and no fragility discount** — never accept less production to buy durability.

Where `GP` comes from, what may not feed it, and the two blind spots that get flagged rather than patched: `Durability.md`.

## σ

`sim.py players` prints σ as the gap to a neighbouring row, in sigmas of the sim's own Monte-Carlo noise (3 independent 200-trial seed blocks). It measures whether the sim resolves the *order* of two adjacent rows — nothing about tradeability.

- **State no order below ~2σ** — treat the rows as an unordered tie, and say which ordering σ belongs to (it can differ from the published sort).
- **Never a printed table column.** One footnote below the table naming the adjacent-pair ties (`Name/Name X.Xσ`). Above ~2σ the magnitude carries no further meaning.
- **Monte-Carlo resolution is not decision resolution.** A gap can clear 2σ and still be under ~0.1 wins — a real order, and too small to trade on.
- A decision that leans on one pair's ordering computes σ for that pair on demand.

# Reading a team

## `SIT`

One dated label per team — contending / fringe / tanking — for how much a win is worth to them right now. Coarse on purpose.

How it is assigned and what it changes about what a team pays up for and sells down: `SIT.md`.

## `ΔP(title)`

Sim-measured change in **P(title)** from a player being on the roster — regular season, seeds and byes, then the bracket (`player_title` / `incoming_title`). Seed is simulated, not assumed. **A different currency from `Δw (season)`, never combined with it** — **table column** after formula **`Δw`** and **`Δw (season)`**, before `W20`–`W23`. Per-player inputs `W20`–`W23` are the next columns (§Columns).

Which report to run for whom, the two ΔP reads (`player_title` vs `incoming_title`), and what the figure may decide: `Bracket value.md`.

## Counterparty title reads

**`incoming_title` on `basis()`, not their roster.** Eval file: `--eval <team_id>`. **`ΔP(title) ours`** is our title odds if we acquire them. Their projected PF rank + `SIT` for whether they contend: `Bracket value.md` §Counterparty title reads.

# Standing rules

## Where our format pulls off consensus

The **closed list** of four places our scoring weights, the 9-slot cap or a roster's shape make the answer differ from the market's: **`Δw (season)`** · body count · multi-position eligibility · light-night coverage (formula `Δw` covers typical-team 9-slot via the curve). Everything else is in BASE — no column, no discount, no model.

Each item's direction, magnitude and the sim runs that already contain it: `Format edges.md`.

## Non-factors

Real-life contracts · NBA depth charts · same-NBA-team stacking · fragility concentration · absence *pattern* for season points · variance from a normal-sized trade · **slot-group balance as a standing target**. **Don't restate this list elsewhere — cite this section.**

Why each is excluded and the one sanctioned use of a slot-group count: `Format edges.md` §Non-factors.
