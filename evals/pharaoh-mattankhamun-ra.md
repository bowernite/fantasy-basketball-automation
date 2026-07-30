# Pharaoh Mattankhamun-Ra (Matthew) — dynasty values

**Derived 2026-07-30.** Re-derive from scratch; do not copy this header (`team-eval`).

**BASE** is blended points-format board rank and nothing else. **WINS** is what a player
banks **for a specific roster** — so it is reported twice below, and the two are not
interchangeable.

**Not a party to the pending trade 483809** (`FetchTrades`) — that is ours ↔ The Don, so
every number here sits on the same side of it. Their roster snapshot is
`roster-160941-2025-26.json` (`fetch_data.py roster 160941`), **26 bodies**.

| | |
|---|---|
| Blend | 40% Dizzle Points · 35% Hashtag Points · 25% Hashtag crowd. Dynatyze not blended |
| Board depths | Dizzle **450** · Hashtag Points **772** · crowd **764** |
| Board stamps | Dizzle Jul 2026 (snapshot) · Hashtag Points 2 Jul 2026 · crowd **29 Jul 2026** |
| Curve | `D = teams x roster_size = 456` · `a = sqrt(D) = 21.354` · `V(r) = 9999*(a+1)/(D-1)*(D-r)/(a+r)`, 0 at or past `D` |
| `REPL` basis | **`sim.basis(path)` — both rosters padded to 38 bodies**, the post-Sept size, and the only way `WINS` compares across teams |
| `REPL` theirs | guard **11.9** · forward **12.5** · centre **11.8** (`K` 777 all three) |
| `REPL` ours | guard **18.0** / `K` 782 · forward **16.1** / 779 · centre **17.8** / 781 |
| Horizon | `delta = 0.875`, H = 3 seasons, `Sum delta = 2.641` |
| `kappa` theirs | **682** sim layer (n=18, quartiles 428-1004) · 502 formula layer (n=23) |

⚠️ **`WINS` is not comparable across rosters of different size, and `REPL` is dominated by
size before shape.** Measured on their **live 26** bodies `REPL` is **8.7 / 9.0 / 8.1** against
**11.9 / 12.5 / 11.8** padded — ~3.5 rate points, **~0.27 wins on every player they own**, all
of it in the flattering direction, and ten times the gaps the σ column exists to police. Ours
moves 13.7 → 16.1 (forward) over the same padding. Everything below is on the padded 38 basis.

**Our bar is higher against this roster, by group, not by a flat amount** — guard **+6.1**,
forward **+3.6**, centre **+6.0** rate points. So `WINS ours` runs **0.2-0.5 wins** under
`WINS theirs`, widest on guards. That gap *is* the depth penalty `team-eval` names, and against
*this* roster it is why a mid-tier player they value we often should not. **Acquisition
decisions use `WINS ours`; what they give up uses `WINS theirs`.**

⚠️ **The sign is per group and per roster, not a league-wide fact.** King Christopher's
*forward* bar sits **above** ours and his centre bar 4.0 below it (`bathroom-club.md` §`WINS`),
which inverts the conclusion for his forwards. Run `sim.replacement` on the counterparty's
padded file before assuming a direction.

**`kappa` is stable once the basis is fixed** — formula layer 502 (them) · 594 (The Don) · 631
(us), all inside our own 413-982 for that layer (`bathroom-club.md` §`kappa`, which `team-eval`
now points at rather than restating). **Calibrate on the layer you apply
it to** (`team-eval`): against a `sim.py players` `Delta w`, use the sim layer — 682 here, 940
for us. The two layers do **not** share a row set (the sim turns negative five rows earlier),
which is why n differs. Quote the band, never the point.

**Sourced vs modelled.** Board ranks, `FPts/G`, `GP`, `AGE`, `ELIG` are sourced. `GP proj`,
both `WINS` columns, `Delta w`, `REPL`, `K`, `kappa`, `LATE` are modelled or judgment. Never
present the two as bracketing a range.

## Players

Sorted by **`Δw theirs`**, so the order matches `sim.py --roster roster-160941-2025-26.json
players`. `FPts/G` and `GP` are last season **actual**, reporting only; `GP proj` is
`sim.project_gp` as `our_roster` rounds it — the integer the sim ran.

- **`W theirs` / `W ours`** = `(rate - REPL) x GP proj / K`, per slot group, on their `REPL`
  and on ours. **Same layer, so they are comparable to each other.**
- **`Δw theirs`** = sim-measured wins lost if he were swapped for a replacement-level
  12.5-rate, 68-GP forward **on their roster**, 3 x 200 trials. **There is no `Δw ours`
  column**: measuring one means putting him on our roster (`sim.swap` + `sim.player_wins`) —
  do that before committing to a deal. Scaling `W ours` by the sim/formula ratio (~0.75 here)
  is the cheap substitute.
- **σ** = gap to the row below, in sigma of that gap. `-` = off that board.

⚠️ **State no order below ~2σ.** Unordered adjacent pairs: **Sharpe/Ausar 1.9σ ·
Walker/Murray 1.6σ · Murray/Eason 0.0σ · Eason/Harper 0.4σ · Sheppard/Jakučionis 1.8σ ·
Dillingham/Dick 0.3σ · Dick/Whitmore 0.3σ · Whitmore/Cissoko 1.4σ.** Murray, Eason and
Harper are a **three-way tie** at +0.54/+0.55. The σ between the last two rows is not
reported: both are artefacts.

⚠️ **Two rows are artefacts of the snapshot, not valuations** — the sim prints a number for
both; do not quote it:

- **Jonathan Kuminga** is `tm: "FA"` in the snapshot. `sim._availability` gives an unsigned
  player **no NBA schedule**, so he suits up for nothing and the sim scores him at **−0.27**,
  below the replacement body. His formula rows (+0.63 / +0.40) are the usable read until he
  signs. A this-season fact in a dynasty league; recheck before pricing him.
- **Thomas Sorber** has **no pool history at all** — a rookie who missed the season, so
  `our_roster` cannot fill a rate and he prices at **0.0**, giving a sim −0.27 that measures
  the zero, not the player. `PROJECTED_RATE` holds our names only. His **BASE 547** is the
  only real figure on that row; `team-eval` → *no usable sample*.

⚠️ A negative `WINS`/`Δw` is "not a starter", **not** worse than an empty slot —
sub-replacement players still pay as light-night bodies, which no rate metric sees. `BASE` 0
means past `D`; every all-boards absence here was hand-checked (`evaluating-players`), which
is how **Bub Carrington** was caught rendering as **Carlton Carrington** on all three boards.

| Player | dizP | htP | crd | **BASE** | FPts/G | GP | GP proj | **W theirs** | **W ours** | **Δw theirs** | σ | **LATE** | AGE | ELIG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| Victor Wembanyama | 1 | 1 | 1 | **9999** | 50.4 | 64 | 62 | **3.02** | 2.73 | **+2.84** | 8.2 | ✓ 1 of 3 under 60 | 22.6 | PF/C |
| Jalen Johnson | 9 | 12 | 9 | **6991** | 48.2 | 72 | 65 | **2.99** | 2.68 | **+2.67** | 34.2 | ✗ 2 of 3 under 60 | 24.6 | SF/PF |
| Scottie Barnes | 12 | 10 | 12 | **6696** | 40.5 | 80 | 68 | **2.45** | 2.13 | **+2.22** | 124.3 | ✓✓ none under 60 in 5 | 25.0 | SG/SF |
| Neemias Queta | 142 | 219 | 707 | **547** | 28.0 | 76 | 66 | **1.38** | 0.86 | **+1.15** | 16.3 | – 2 rotation seasons (28/76) | 27.0 | C |
| Shaedon Sharpe | 135 | 120 | 99 | **1176** | 30.3 | 50 | 57 | **1.35** | 0.90 | **+0.98** | 1.9 | ✗ 2 of 4 under 60 | 23.2 | PG/SG |
| Ausar Thompson | 79 | 123 | 63 | **1707** | 27.5 | 74 | 64 | **1.24** | 0.94 | **+0.95** | 3.1 | ✓ 1 of 3 under 60 | 23.5 | SG/SF |
| Anthony Black | 109 | 93 | 98 | **1437** | 27.8 | 64 | 61 | **1.25** | 0.76 | **+0.89** | 3.1 | – 2 rotation seasons (78/64) | 22.5 | PG/SG |
| Kyshawn George | 85 | 94 | 84 | **1659** | 29.3 | 48 | 56 | **1.21** | 0.95 | **+0.83** | 8.1 | – 2 rotation seasons (68/48) | 22.6 | SF/PF |
| Devin Vassell | 121 | 121 | 96 | **1244** | 24.6 | 67 | 61 | **0.95** | 0.67 | **+0.69** | 6.2 | ✓ 1 of 5 under 60 | 25.9 | SG/SF |
| Jarace Walker | 306 | 184 | 152 | **533** | 22.2 | 76 | 63 | **0.79** | 0.49 | **+0.58** | 1.6 | – 1 rotation season (76) | 22.9 | SF/PF |
| Keegan Murray | 115 | 70 | 119 | **1513** | 27.4 | 23 | 46 | **0.88** | 0.67 | **+0.55** | 0.0 | ✓ 1 of 4 under 60 | 25.9 | SF/PF |
| Tari Eason | 107 | 147 | 127 | **1122** | 23.8 | 60 | 58 | **0.84** | 0.57 | **+0.55** | 0.4 | ✗ 2 of 4 under 60 | 25.2 | SF/PF |
| Dylan Harper | 20 | 18 | 13 | **5569** | 22.6 | 69 | 61 | **0.84** | 0.36 | **+0.54** | 5.0 | – 1 rotation season (69) | 20.4 | PG/SG |
| Bub Carrington | 292 | 194 | 254 | **402** | 21.4 | 82 | 65 | **0.79** | 0.28 | **+0.44** | 3.6 | – 2 rotation seasons (82/82) | 21.0 | PG/SG |
| Noah Clowney | 266 | 179 | 162 | **565** | 21.3 | 66 | 59 | **0.67** | 0.39 | **+0.39** | 16.6 | – 2 rotation seasons (46/66) | 22.0 | PF/C |
| Olivier-Maxence Prosper | 443 | 394 | 739 | **31** | 18.0 | 53 | 53 | **0.38** | 0.13 | **+0.14** | 3.5 | – 1 rotation season (53) | 24.1 | SF/PF |
| Cody Williams | 319 | 254 | 414 | **217** | 16.8 | 67 | 58 | **0.32** | 0.05 | **+0.11** | 4.2 | – 1 rotation season (67) | 21.7 | SF/PF |
| Ben Sheppard | 432 | 338 | 640 | **67** | 14.6 | 65 | 56 | **0.19** | -0.24 | **+0.04** | 1.8 | – 0 rotation seasons | 25.0 | PG/SG |
| Kasparas Jakučionis | 172 | 212 | 326 | **514** | 14.8 | 53 | 52 | **0.19** | -0.21 | **-0.01** | 2.5 | – 0 rotation seasons | 20.2 | PG/SG |
| Ousmane Dieng | 232 | 195 | 635 | **381** | 15.1 | 57 | 53 | **0.18** | -0.07 | **-0.05** | 3.6 | – 1 rotation season (57) | 23.2 | SF/PF |
| Rob Dillingham | 251 | 319 | 333 | **260** | 12.1 | 65 | 55 | **0.01** | -0.41 | **-0.12** | 0.3 | – 0 rotation seasons | 21.6 | PG/SG |
| Gradey Dick | 333 | 277 | 296 | **233** | 10.5 | 76 | 58 | **-0.15** | -0.42 | **-0.13** | 0.3 | – 1 rotation season (54) | 22.7 | SG/SF |
| Cam Whitmore | 433 | 210 | 313 | **245** | 15.2 | 21 | 40 | **0.14** | -0.05 | **-0.13** | 1.4 | ✗ 3 of 3 under 60 | 22.1 | SF/PF |
| Sidy Cissoko | - | 584 | 763 | **0** | 11.8 | 75 | 58 | **-0.01** | -0.46 | **-0.16** | 5.0 | – 0 rotation seasons | 22.3 | PG/SG |
| Thomas Sorber | 154 | 228 | 316 | **547** | – | 0 | – | **–** | – | **–** | – | – no pool history | 20.6 | C |
| Jonathan Kuminga | 176 | 182 | 342 | **549** | 22.5 | 36 | 49 | **0.63** | 0.40 | **artefact** | – | ✓ 2 of 5 under 60 | 23.8 | SF/PF |

`LATE` legend, causes and thresholds: **`team-eval` §`LATE`** (`bathroom-club.md` §*`LATE`* has
the worked scoring) — same rule, so the column is comparable. Note how little it resolves here: **16 of 26 are `–`**,
because this is the youngest roster in the league and `team-eval` will not let one or two
seasons stand in for a durable trait.

## Picks — Sept '26

Off the Dizzle dynasty board's **slot-prefixed rookie rows**, by **overall ordinal**
`(R-1)*12 + S` — never by the label.

**`VALUE` is Dizzle alone, not the 50/50 pick blend** — `evaluating-picks` §*4. BASE* drops
the crowd board while its pick rows carry a class-normalising notice, which they do.

| Pick | own/acq | ordinal | chart slot | board rank | **VALUE** | would take |
|---|---|---:|---|---:|---:|---|
| 1.05 | own | 5 | 1.05 | 50 | **2795** | Darius Acuff Jr. |
| 2.05 | own | 17 | 1.17 | 145 | **918** | Cameron Carr |
| 3.05 | own | 29 | 1.29 | 240 | **406** | Chris Cenac Jr. |
