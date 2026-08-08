# Lineup math — running the sim

Prices a roster change in **expected wins** on the real '25-26 NBA calendar. Come here for a
number and **re-run rather than quote it.**

- **`method.md`** — the basis, the calibration, and where to distrust the model. Read it
  before quoting anything.
- **`findings.md`** — every measured table: PF→wins, the consolidation ladder, break-evens,
  the valuation formula, GP, durability, the slot-fill curve, positional premium,
  light-night coverage, the Sept '26 expansion.

Durable valuation rules live in `Eval Definitions`; how to apply them, `eval-team`. Nothing
here restates either.

```
python3 sim.py gp            # expected GP: what predicts it, and what doesn't
python3 sim.py market        # board rank -> FPts/G, and GP persistence
python3 sim.py calibration   # NBA calendar, sim vs reality, PF -> wins and its band
python3 sim.py scenarios     # the consolidation ladder
python3 sim.py breakevens    # N-for-1 break-evens + backfill bracket (~6 min)
python3 sim.py replacement   # replacement level per position, the formula's shape
python3 sim.py schedules     # what steering the auction on the NBA calendar buys (~4 min)
python3 sim.py nights formula durability positions extras players
python3 -m unittest test_sim
python3 fetch_data.py [pool]                   # re-scrape; `pool` is ~20 min, resumable
```

The CLI knows only these names and **exits non-zero on anything else.** For a live trade,
import it:

```python
import sim
full = sim.basis()                        # whoever is loaded, padded to 38 bodies
base = sim.run(full)
deal = sim.run(sim.swap(full, ["Jalen Suggs", "Coby White"], [sim.star(48, 70, ("C",))]))
sim.wins(deal, base)                      # +wins over 20 matchups
sim.breakeven(full, ["Jalen Suggs", "Coby White"], gp=70, elig=("C",))
sim.player_wins(full, ["Jalen Suggs"])    # -> {name: (Δw, sd, per-block values)}
```

`sim.wins(after, before)` — **the argument order is the sign.** Reversed it reads "wins
lost", which is a legitimate call (the `formula` report makes it), so nothing can guard it;
name which one you mean.

⚠️ **What the import surface refuses.** Each of these raises rather than hand back a number
you would publish. Fix the call — there is no flag to pass.

| | |
|---|---|
| `swap` | a name not on the file · a name on it **twice** · one name **sent twice** (a body leaves once, so the deal is a piece shorter than you typed) · **more bodies in than out** (the roster is capped — name the drops yourself) |
| `breakeven` | a break-even outside its 20–90 search bracket. `OutOfBracket.mark` (`<20` / `>90`) is the answer; `breakeven_value` returns it instead of raising |
| `incoming_wins` | **two arrivals of one name** (rows are keyed by name, so one would silently replace the other) · a roster with **nothing padded**, since the slot an arrival takes is a padded one |
| `our_roster` (so `basis` too) | a roster file carrying **nobody** — it pads to 38, so an empty file is 38 bodies of filler, not an empty table |

## Where the code lives

`sim.py` is the CLI and the import surface — it re-exports, and defines almost nothing.
The code sits in `simlib/`, one responsibility per module, and each module's docstring
says which:

| | |
|---|---|
| `data` `lineups` `stats` | the NBA calendar and our real scores; the 9 slots and the matching; the line fits and block summaries |
| `schedule` `wins` | light nights and coverage; the one PF→wins constant |
| `board` `projections` `gp` | rank↔rate; the projected rate; expected games played |
| `engine` `roster` | `season`/`run`; loading, projecting, padding, `swap` |
| `auction` `value` | steering the September auction; replacement, `Δw`, break-evens |
| `reports/` | one module per group of reports, plus the `REPORTS` registry |

No module imports a row below its own, so the layering is checkable by reading the import
lines. In a test, **patch the module that DEFINES a function** — see `cheap_monte_carlo` in
`test_sim.py`. `sim.run`, `sim.player_wins`, `sim.gp_bootstrap`, `sim.PLAYER_BLOCKS` and
`sim.ROSTER` read *and* write through to those modules, so the facade is a live seam rather
than a snapshot; every other name it exports is a plain re-export.

## Flags

`sim.py players` prints a flag column and `sim.evidence_flags(name)` returns the pool codes
(`frag` · `miss` · `rotN` · `nopool`); the table adds **`fa`** and **`noproj`**. Those six are
the whole of what the sim publishes. `Eval Definitions §Output` defines them — and the other
four an eval may carry — once; cite it, and carry the flag with the row.

**Those rows are where `Δw` is an upper bound, not a measurement** (`Eval Definitions §Δw`),
and the flags are the only thing the sim publishes that speaks to whether a player still
holds a rotation spot at all.

## Pricing a counterparty

```
python3 fetch_data.py roster 160941      # -> roster-160941-2025-26.json
python3 sim.py --roster roster-160941-2025-26.json players replacement
python3 fetch_data.py roster 161025      # OURS is the same command, same schema.
                                         # Re-run it after any trade EXECUTES.
```

**Two different Δw columns, and the CLI only prints one.** `--roster their.json players`
prices his players **on his roster** — that is `Δw theirs`. `Δw ours` for those same
players — what `Eval Definitions §Columns` requires and what a buy decision reads — is a
separate run, on *our* roster, and it is one import call:

```python
sim.incoming_wins(sim.basis(), sim.our_roster("roster-160941-2025-26.json"))
```

Same counterfactual *shape* as `player_wins` (a replacement 68-GP body of his **own slot
group**, in rather than out) and at the **same body count**: he takes a **padded** slot — the
last one, since `pad` appends — so the room he joins is our real bodies re-padded one
shallower, and nobody off a roster file loses his place. **At 38 real bodies — ours from
Sept '26 — there is no pad and this refuses**: drop the body you would actually cut and pass
the 37.

Each column is measured against its own roster's `R`, so **neither substitutes for the other
and their difference is not a number**: a gap between them is mostly the two rosters'
replacement levels, not the player.

`--roster` serves **9 of the 13 reports** and **exits non-zero on `calibration` `scenarios`
`breakevens` `durability`, naming the 9 it does serve** — those four are built on our own
player names and our real weekly scores, so under another team's file they answer nothing.
`sim.our_roster(path)` and `sim.basis(path)` are the import path. Team ids are in
`team-info`. A row is `{n, tm, avg, tot, gp, posLabel, elig}` —
`fetch_data.roster_rows` is the schema, and `avg`/`gp` are last season as it happened, which
`our_roster` then projects forward.

⚠️ **Compare two teams only at a common body count.** `R` rises with the count, and value is
`(rate − R) × GP`, so **a roster measured short has a low `R` and every player on it reads too
valuable.** Measured **2026-08-03**, **forward group** throughout: ours **14.6 live at 28 →
17.1 padded to 38**; Pharaoh's 26 bodies **9.6 live → 12.9 padded** (per group 9.3/9.6/8.1 →
12.1/12.9/11.6 guard/forward/centre). Those 4.2 rate points are **~0.3 wins on every player he
owns** — ten times the gaps the σ column is there to police. `sim.basis()` pads to 38 for
exactly this reason. **14.6 is the *live file*; `findings.md` §*Valuation formula*'s 28 row is
a different 28 and reads 15.1.**

⚠️ **`R` is a property of a roster's shape at a moment, not a constant.** It moves on a trade,
on the rate basis and on the body count alike, and the two sides of one deal can move in
opposite directions — so **re-measure both, and never quote an `R` off an older revision of
these files.** An unsigned body still prices as a body, on the study's own schedule
(`method.md`), so a roster holding one is not thereby measured short. **Acquisition prices on
our roster; what they give up prices on theirs.**

⚠️ **`FetchRoster?season=` is a snapshot** as of the season's last lineup period: a body added
after it is absent (The Don, 26 against 28 live — take counts from `FetchLeagueRosters`), and
a player who missed the whole season carries no rate on it. That does not reach the rate —
`our_roster` takes it from the projection (`projections`), which is the same number whether
or not he played. A player the feed does not carry keeps the snapshot's rate and
prints `noproj`.

⚠️ **A July snapshot also carries unsigned players** (`proTeamAbbreviation` "FA") — **7 of
the 12 roster files hold 1–3**, Beal, Sochan and Kuminga among them. They have no NBA
schedule, so they are priced on the study's own (`SIM_TM`, `method.md`) like any other body of
unknown schedule, and `players` flags the row **`fa`** so that assumption travels with the
number. **Do not zero them out instead** — that costs each of them **≈ 0.33 of a body**, which
is a fact about the calendar date of the fetch published as a fact about the player.
