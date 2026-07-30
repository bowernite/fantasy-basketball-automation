# The Don (Mitch) — dynasty values

**Derived 2026-07-30.** Re-derive from scratch; do not copy this header (`team-eval`).

**BASE** is blended points-format board rank and nothing else. **WINS** is what a player
banks **for a specific roster** — so it is reported twice below, and the two are not
interchangeable.

## ⚠️ Which side of trade 483809 every number here sits on

They are the **counterparty**. **Still pending** as of this derivation (`FetchTrades`,
2026-07-30): veto window closes 2026-07-30T21:03:44Z (`expiryIso`, 5 vetoes needed), executes
**2026-07-31T00:00:00Z**. They receive our **2026 1.09**; they send **Mark Williams**, their
**own 2027 2nd** and **King Christopher's 2027 2nd**.

- **Pre-execution** (this table, `REPL`, `κ`, the pick table): `roster-161020-2025-26.json`,
  **Mark Williams still on it**, 1.09 not yet theirs.
- **Post-execution `REPL`** (25 real bodies padded to 38, measured): guard **12.0** ·
  forward **12.8** · centre **12.6**, `K` 778 — every group falls, so every player they keep
  reads slightly *more* valuable to them. Re-derive the `WINS theirs` column before pricing a
  second deal off this file.
- After it executes, re-run `fetch_data.py roster 161020`; **do not hand-edit.**

| | |
|---|---|
| Blend | 40% Dizzle Points · 35% Hashtag Points · 25% Hashtag crowd. Dynatyze not blended |
| Board depths | Dizzle **450** · Hashtag Points **772** · crowd **764** |
| Board stamps | Dizzle Jul 2026 (snapshot) · Hashtag Points 2 Jul 2026 · crowd **29 Jul 2026** |
| Curve | `D = teams x roster_size = 456` · `a = sqrt(D) = 21.354` · `V(r) = 9999*(a+1)/(D-1)*(D-r)/(a+r)`, 0 at or past `D` |
| `REPL` basis | **`sim.basis(path)` — both rosters padded to 38 bodies**, the post-Sept size, and the only way `WINS` compares across teams |
| `REPL` theirs | guard **12.4** · forward **13.6** · centre **14.0** (`K` 777 all three) |
| `REPL` ours | guard **18.0** / `K` 782 · forward **16.1** / 779 · centre **17.8** / 781 |
| Horizon | `delta = 0.875`, H = 3 seasons, `Sum delta = 2.641` |
| `kappa` theirs | **895** sim layer (n=16, quartiles 589-1771) · 594 formula layer (n=24) |

⚠️ **`WINS` is not comparable across rosters of different size, and `REPL` is dominated by
size before shape.** Measured on their **live 26** bodies `REPL` is **9.7 / 11.1 / 11.2**
against **12.4 / 13.6 / 14.0** padded — 2.5-2.8 rate points, ~0.2 wins on every player they
own, all of it flattering. Ours moves 13.7 → 16.1 (forward) over the same padding. Everything
below is on the padded 38 basis.

⚠️ **The snapshot is 26 bodies against 28 live.** `FetchRoster?season=` is a snapshot as of
the season's last lineup period, so **Bronny James and Sam Hauser** are absent from it and the
sim never sees them. They are listed below off `players-2025-26.json` instead — real, sourced
'25-26 rate and `GP`, but **no `Δw`**, because the sim measured a roster they were not on.
Body counts come from `FetchLeagueRosters`.

**Our bar is higher against this roster, by group, not by a flat amount** — guard **+5.6**,
forward **+2.5**, centre **+3.8** rate points. So `WINS ours` runs **0.15-0.45 wins** under
`WINS theirs`, widest on guards and narrowest on forwards. That gap *is* the depth penalty
`team-eval` names.
**Acquisition decisions use `WINS ours`; what they give up uses `WINS theirs`** — which for
Mark Williams is **+1.04 to them against +0.75 to us** on the formula, **+0.59 to them against
a measured +0.36 to us** on the sim (`bathroom-club.md` §*Post-execution*). We are paying for
market value, not for wins.

⚠️ **The sign is per group and per roster, not a league-wide fact.** King Christopher's *forward*
bar sits **above** ours and his centre bar 4.0 below it (`bathroom-club.md` §`WINS`), which
inverts the conclusion for his forwards. Run `sim.replacement` on the counterparty's padded file
before assuming a direction.

**`kappa` is stable once the basis is fixed** — formula layer 594 (them) · 502 (Pharaoh) · 631
(us), all inside our own 413-982 for that layer (`bathroom-club.md` §`kappa`, which `team-eval`
now points at rather than restating). **Calibrate on the layer you apply it
to** (`team-eval`): against a `sim.py players` `Delta w`, use the sim layer — 895 here, 940 for
us. The two layers do **not** share a row set — only **16** rows clear `Delta w > 0` against
24 on the formula, which is also why their sim-layer upper quartile (1771) is so wide.
Quote the band, never the point.

**Sourced vs modelled.** Board ranks, `FPts/G`, `GP`, `AGE`, `ELIG` are sourced. `GP proj`,
both `WINS` columns, `Delta w`, `REPL`, `K`, `kappa`, `LATE` are modelled or judgment. Never
present the two as bracketing a range.

## Players

Sorted by **`Δw theirs`**, so the order matches `sim.py --roster roster-161020-2025-26.json
players`. `FPts/G` and `GP` are last season **actual**, reporting only; `GP proj` is
`sim.project_gp` as `our_roster` rounds it — the integer the sim ran.

- **`W theirs` / `W ours`** = `(rate - REPL) x GP proj / K`, per slot group, on their `REPL`
  and on ours. **Same layer, so they are comparable to each other.**
- **`Δw theirs`** = sim-measured wins lost if he were swapped for a replacement-level
  13.6-rate, 68-GP forward **on their roster**, 3 x 200 trials. **There is no `Δw ours`
  column** — measuring one means putting him on our roster (`sim.swap` + `sim.player_wins`),
  as done for Mark Williams above. Scaling `W ours` by the sim/formula ratio (~0.7 here) is
  the cheap substitute.
- **σ** = gap to the row below, in sigma of that gap. `-` = off that board.

⚠️ **State no order below ~2σ.** Unordered adjacent pairs: **Kessler/Queen 1.3σ ·
Tre Jones/Franz 0.3σ · Risacher/Riley 0.3σ · Riley/Carter 0.8σ · Carter/Richard 0.7σ ·
Richard/Mashack 0.4σ · Grant Williams/Topić 0.3σ · Hardy/Salaün 1.8σ.** Risacher, Riley,
Carter, Richard and Mashack are a **five-way tie** between −0.03 and −0.07 — that whole band
is one undifferentiated group, not a ranking.

⚠️ A negative `WINS`/`Δw` is "not a starter", **not** worse than an empty slot —
sub-replacement players still pay as light-night bodies, which no rate metric sees. `BASE` 0
means past `D`; every all-boards absence here was hand-checked (`evaluating-players`).

| Player | dizP | htP | crd | **BASE** | FPts/G | GP | GP proj | **W theirs** | **W ours** | **Δw theirs** | σ | **LATE** | AGE | ELIG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| Luka Dončić | 3 | 3 | 6 | **8874** | 57.2 | 64 | 62 | **3.48** | 3.27 | **+3.19** | 84.0 | ✓ 1 of 5 under 60 | 27.4 | SG/SF |
| Deni Avdija | 26 | 31 | 21 | **4441** | 41.5 | 66 | 63 | **2.26** | 2.05 | **+1.73** | 16.0 | ✓✓ none under 60 in 5 | 25.6 | SF/PF |
| Cooper Flagg | 5 | 7 | 2 | **8473** | 37.3 | 70 | 64 | **1.95** | 1.74 | **+1.47** | 6.4 | – 1 rotation season (70) | 19.6 | SF/PF |
| Keyonte George | 49 | 47 | 47 | **2900** | 37.0 | 54 | 59 | **1.87** | 1.43 | **+1.35** | 24.7 | ✓ 1 of 3 under 60 | 22.7 | PG/SG |
| Walker Kessler | 47 | 78 | 65 | **2386** | 40.2 | 5 | 41 | **1.38** | 1.18 | **+0.95** | 1.3 | ✗ 2 of 4 under 60 | 25.0 | C |
| Derik Queen | 86 | 83 | 56 | **1927** | 27.9 | 81 | 68 | **1.22** | 0.88 | **+0.95** | 5.7 | – 1 rotation season (81) | 21.6 | C |
| Jaren Jackson | 53 | 37 | 49 | **3010** | 32.0 | 48 | 56 | **1.33** | 1.14 | **+0.93** | 7.9 | ✓ 1 of 5 under 60 | 26.9 | PF/C |
| Reed Sheppard | 88 | 87 | 88 | **1660** | 26.2 | 82 | 67 | **1.19** | 0.70 | **+0.87** | 5.4 | – 1 rotation season (82) | 22.1 | PG/SG |
| Tre Jones | 214 | 366 | 458 | **242** | 27.7 | 65 | 62 | **1.22** | 0.77 | **+0.78** | 0.3 | ✓ 1 of 4 under 60 | 26.6 | PG/SG |
| Franz Wagner | 28 | 34 | 33 | **3971** | 32.6 | 34 | 51 | **1.25** | 1.08 | **+0.77** | 9.4 | ✓ 1 of 5 under 60 | 24.9 | SF/PF |
| Moussa Diabaté | 170 | 140 | 137 | **878** | 26.6 | 73 | 64 | **1.07** | 0.86 | **+0.61** | 2.1 | – 2 rotation seasons (71/73) | 24.5 | SF/PF |
| **Mark Williams** → us | 114 | 97 | 121 | **1307** | 27.5 | 60 | 60 | **1.04** | 0.75 | **+0.59** | 7.6 | ✗ 3 of 4 under 60 | 24.6 | C |
| Isaiah Collier | 221 | 190 | 139 | **650** | 25.8 | 60 | 59 | **1.02** | 0.59 | **+0.49** | 13.7 | – 2 rotation seasons (71/59) | 21.8 | PG/SG |
| Jordan Goodwin | 329 | 351 | 706 | **120** | 22.6 | 70 | 61 | **0.80** | 0.36 | **+0.33** | 6.8 | ✗ 2 of 4 under 60 | 27.8 | PG/SG |
| Collin Murray-Boyles | 65 | 86 | 68 | **2016** | 21.8 | 57 | 56 | **0.59** | 0.41 | **+0.24** | 10.4 | – 1 rotation season (57) | 21.1 | SF/PF |
| Robert Williams | 222 | 163 | 604 | **462** | 21.5 | 59 | 57 | **0.58** | 0.40 | **+0.06** | 4.3 | ✗ 4 of 5 under 60 | 28.8 | PF/C |
| Zaccharie Risacher | 235 | 166 | 150 | **655** | 18.7 | 67 | 58 | **0.38** | 0.19 | **-0.03** | 0.3 | – 2 rotation seasons (75/67) | 21.3 | SF/PF |
| Will Riley | 166 | 191 | 354 | **552** | 17.5 | 74 | 61 | **0.31** | 0.11 | **-0.03** | 0.8 | – 1 rotation season (74) | 20.5 | SF/PF |
| Devin Carter | 313 | 269 | 364 | **224** | 18.0 | 38 | 47 | **0.34** | 0.00 | **-0.05** | 0.7 | – 1 rotation season (38) | 24.4 | PG/SG |
| Will Richard | 325 | 376 | - | **109** | 14.7 | 69 | 57 | **0.17** | -0.24 | **-0.06** | 0.4 | – 0 rotation seasons | 23.6 | PG/SG |
| Jahmai Mashack | 424 | - | - | **14** | 15.3 | 31 | 44 | **0.16** | -0.15 | **-0.07** | 8.0 | – 1 rotation season (31) | 23.7 | PG/SG |
| Grant Williams | 326 | 310 | 643 | **149** | 16.3 | 36 | 46 | **0.16** | 0.01 | **-0.16** | 0.3 | ✓ 2 of 5 under 60 | 27.7 | SF/PF |
| Nikola Topić | 213 | 334 | 208 | **396** | 13.4 | 10 | 35 | **0.05** | -0.21 | **-0.17** | 2.5 | – 0 rotation seasons | 21.0 | PG/SG |
| Jaden Hardy | 426 | 378 | 599 | **47** | 12.5 | 57 | 52 | **0.01** | -0.37 | **-0.22** | 1.8 | – 0 rotation seasons | 24.1 | PG/SG |
| Tidjane Salaün | 285 | 431 | 434 | **125** | 13.0 | 37 | 45 | **-0.03** | -0.18 | **-0.24** | 5.9 | – 0 rotation seasons | 21.0 | SF/PF |
| Dalton Knecht | 402 | 386 | 405 | **69** | 6.9 | 54 | 49 | **-0.42** | -0.58 | **-0.30** | — | – 0 rotation seasons | 25.3 | SF/PF |
| Sam Hauser † | 218 | 380 | 335 | **270** | 18.0 | 78 | 62 | **0.35** | 0.15 | **–** | – | ✓✓ none under 60 in 3 | 28.6 | SF/PF |
| Bronny James † | 422 | 353 | 592 | **62** | 6.3 | 42 | 44 | **-0.35** | -0.66 | **–** | – | – 0 rotation seasons | 21.8 | PG/SG |

† **Absent from the roster snapshot the sim ran** (added after the season's last lineup
period). `FPts/G`, `GP`, `AGE` and `ELIG` here come from `players-2025-26.json`, which is
sourced and re-scored under current rules; `GP proj` and both `WINS` columns are computed the
same way as every other row. **They have no `Δw`** — add them to the roster file and re-run
before pricing either.

`LATE` legend, causes and thresholds: **`team-eval` §`LATE`** (`bathroom-club.md` §*`LATE`* has
the worked scoring) — same rule, so the column is comparable across files.

## Picks — Sept '26

Off the Dizzle dynasty board's **slot-prefixed rookie rows**, by **overall ordinal**
`(R-1)*12 + S`. Originators off `draftOrder[]` against each round's cells. **Never off the
label**, on either lookup.

**`VALUE` is Dizzle alone, not the 50/50 pick blend** — `evaluating-picks` §*4. BASE* drops
the crowd board while its pick rows carry a class-normalising notice, which they do.

| Pick | originates | ordinal | chart slot | board rank | **VALUE** | would take |
|---|---|---:|---|---:|---:|---|
| 1.03 | own | 3 | 1.03 | 17 | **5623** | Darryn Peterson |
| 1.04 | Mongol | 4 | 1.04 | 30 | **4075** | Caleb Wilson |
| 1.08 | Yao Ming | 8 | 1.08 | 69 | **2104** | Kingston Flemings |
| **1.09** | **ours — incoming, 483809** | 9 | 1.09 | 95 | **1524** | Brayden Burries |
| 1.10 | Jesus Christ | 10 | 1.10 | 99 | **1457** | Yaxel Lendeborg |
| 2.03 | own | 15 | 1.15 | 139 | **971** | Bennett Stirtz |
| 3.11 | King Christopher | 35 | 2.05 | 274 | **303** | Ryan Conwell |

Their own **3.03 is already gone** (→ Han, trade 475769), so this is the whole holding.

**Post-execution they hold five of the top ten Sept-'26 ordinals** (3, 4, 8, 9, 10) — the
shape `team-projections.md` flags as their likely path to consolidating firsts into a second
star. That is the deal's real cost to us, not the 1524.

**Outgoing: two 2027 2nds** — their own (no `originalOwner`) and **King Christopher's**
(`originalOwner`, `traded: true`). ⚠️ The `slot` values in the trade record (2.03, 2.11) are
placeholders keyed to the **2026** order: `FetchLeagueDraftBoard?season=2027` returns `{}`, and
the '27 order is set by the '26-27 finish. Price by **originating team** off
`team-projections.md`, method in `evaluating-picks` §*Future picks*.
