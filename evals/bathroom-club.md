# Bathroom club (us) — dynasty values

**Derived 2026-07-30.** Re-derive from scratch; do not copy this header (`team-eval`).

**BASE** is blended points-format board rank and nothing else — no adjustment by us for
injury, role, situation or contract. **WINS** is what he banks for *that* roster next
season. They are separate layers; never blend them.

## ⚠️ Which side of trade 483809 every number here sits on

**Still pending as of this derivation** (`FetchTrades`, 2026-07-30): veto window closes
2026-07-30T21:03:44Z (`expiryIso`, 5 vetoes needed), executes **2026-07-31T00:00:00Z**.
Out: our **2026 1.09**. In: **Mark Williams** + The Don's **2027 2nd** and King
Christopher's **2027 2nd**. **Marvin Bagley is released as part of it.**

- **Pre-execution** (this table, `REPL`/`K`, `κ`, the pick table): 28 bodies including
  Bagley, no Mark Williams — `roster-161025-2025-26.json` as committed.
- **Unaffected either way:** per-board ranks, `BASE`, `FPts/G`, `GP`, `AGE`, `ELIG`.
- **Post-execution `REPL` and medians** are measured in their own section at the bottom. Per-
  player post `Delta w` is **not published** — the trade moves `REPL`, the medians and the top
  of the ordering, so it is a re-run, never a read off this table.
- After it executes, re-run `fetch_data.py roster 161025` and re-derive; **do not hand-edit.**

| | |
|---|---|
| Blend | 40% Dizzle Points · 35% Hashtag Points · 25% Hashtag crowd. Dynatyze not blended |
| Board depths | Dizzle **450** · Hashtag Points **772** · crowd **764** |
| Board stamps | Dizzle Jul 2026 (snapshot) · Hashtag Points 2 Jul 2026 · crowd **29 Jul 2026** |
| Curve | `D = teams x roster_size = 456` · `a = sqrt(D) = 21.354` · `V(r) = 9999*(a+1)/(D-1)*(D-r)/(a+r)`, 0 at or past `D` |
| `roster_size` | **38 — the announced post-Sept size**, not today's 28. Flagged per `team-eval` |
| `REPL` / `K` | guard **18.0** / 782 · forward **16.1** / 779 · centre **17.8** / 781 (`sim.py replacement`, 38 bodies) |
| Horizon | `delta = 0.875`, H = 3 seasons, `Sum delta = 2.641` |
| `kappa` | **940** BASE per discounted win-season **on the sim layer**, quartiles 630-1312 (n=21) |

## `kappa` — two layers, and they are not interchangeable

`team-eval` requires `kappa` be calibrated on the same layer as the `Delta w` it multiplies,
and `trades` step 6 feeds it a **sim-measured** `Delta w`. Both layers, same 21 rows
(`Delta w > 0` **and** `BASE > 0`; the 7 excluded rows are all sub-replacement, and no
`BASE = 0` row clears `Delta w > 0` here):

| layer | `w` used | `kappa` | quartiles |
|---|---|---:|---|
| **sim** — use this against a `sim.py players` `Delta w` | measured `Delta w` | **940** | 630-1312 |
| formula first cut | `(rate - REPL) x GP / K` | 631 | 413-982 |

The sim layer is **1.49x** the formula layer, which is the formula's own median +33%
over-prediction (`lineup-math/README.md`) reappearing as a calibration constant. Applying
`team-eval`'s formula-layer figure to a sim `Delta w` understates the wins term by a third.

`team-eval` §`kappa` **points here** for both layers rather than restating them, and fixes the
band as Q1-Q3 via `statistics.quantiles(v, n=4, method="exclusive")` — the quartiles above are
that method. Measured the same way on two other rosters (padded to 38):
formula layer **502** Pharaoh · **594** The Don; sim layer **682** · **895**. On those two
rosters the layers do **not** share a row set — the sim turns negative several rows earlier —
so their n differs; ours happens to be the same 21 either way. Both layers use full-precision
rates; the table's 1-dp `FPts/G` reproduces them to within ~2. **Quote a band, never a point
estimate, and state the layer.**

⚠️ **`WINS` compares across rosters only on a common body count.** `REPL` tracks roster
*size* before slot-group shape. Ours is on the 38 basis; measured there the counterparties
sit at **11.9 / 12.5 / 11.8** (Pharaoh) and **12.4 / 13.6 / 14.0** (The Don) against our
**18.0 / 16.1 / 17.8** — our bar is **2.5-6.1 points higher**, by group, not a flat gap. On
their live 26 bodies their own `REPL` falls a further **2.5-3.7 points** (`sim.replacement` on
the unpadded file), so a counterparty measured short has every player on him read too
valuable. See `the-don.md` / `pharaoh-mattankhamun-ra.md`, which publish both columns.

⚠️ **Higher against those two is not higher against all eleven — the sign is per group and
per roster.** King Christopher, 28 bodies padded to 38, measures **16.5 / 16.9 / 13.8**: his
*forward* bar is **0.8 above** ours, his centre **4.0 below** — ours is a **guard** glut (12
pure PG/SG), his a **forward** glut (19 of 28). So his forwards are worth **more** to us than
to him (Durant **+2.04 `W ours`** against **+1.97 `W theirs`**, formula; the sim agrees in
direction but inside the ~0.1-win tie band), which is what keeps him top of `trade-targets.md`
Tier 2. **Run `sim.replacement` on the counterparty's padded file before assuming a sign.**

**Sourced vs modelled.** Board ranks, `FPts/G`, `GP`, `AGE` and `ELIG` are sourced. `GP proj`,
`WINS`, `Delta w`, `REPL`, `K`, `kappa` and `LATE` are modelled or judgment. A sourced price
and a modelled figure never bracket a range.

## Players

Sorted by **`Delta w`**, the sim's measurement — so the order matches `sim.py players`.
Every row is reproducible from `sim.py players` plus `sim.py replacement`.

- `FPts/G` and `GP` are last season **actual**, reporting only. *Italic* `FPts/G` =
  `sim.PROJECTED_RATE`: a hand-typed rate for a player with **no usable sample**, never an
  age haircut on a rate he posted.
- `GP proj` is `sim.project_gp` as `our_roster` rounds it — the integer the sim actually ran.
- **`WINS`** = `(rate - REPL) x GP proj / K`, per slot group (`ELIG` mapping: `{C}` centre ·
  subset of `{PG,SG}` guard · anything else **forward**). A **first cut** — see the ordering
  warning below.
- **`Delta w`** = wins lost if he were swapped for a replacement-level 16.1-rate, 68-GP
  forward, averaged over 3 x 200 trials. **That is the counterfactual** — not "if the slot
  went empty".
- **σ** = gap to the row below, in sigma of that gap. `-` = off that board.

⚠️ **State no order below ~2σ.** Unordered here: **Reid/Garland 1.1σ · Edey/VanVleet 0.8σ ·
Bagley/Coby 1.6σ · Bona/Chaney 0.9σ · Matković/Maluach 0.9σ · Sion/Ellis 0.8σ ·
Ellis/Holmes 0.4σ.** And **resolvable is not tradeable**: Cade over Amen is 3.2σ but 0.02
wins, an order of magnitude inside the formula's error (22-33%) and PF→wins' (±14%).

⚠️ **`WINS` reorders the table and cannot be trusted to.** It puts **Suggs at 0.96 against
the sim's 0.57** — **+68%**, moving him 11th → 13th, and `lineup-math/README.md` names him as
the formula's worst row (+91% single-`R`, +65% per-position). Worse, it gives **Chaney Johnson
+0.15 where the sim measures −0.10** — a *sign flip*. Both are the documented failure mode:
`(rate - REPL) x GP` charges the replacement body only at the departing player's own `GP`, so a
40-GP body is never charged for the 68 games the replacement plays. Sort with `Delta w`; use
`WINS` only where no sim run exists.

⚠️ **A negative `WINS`/`Delta w` does not mean worse than an empty slot.** It is a *producer*
metric, unreliable at and below replacement. Sub-replacement players still pay as
**light-night bodies**, which no rate-based formula sees — never price them at zero, and
never ship one as though it were free. Read the sign as "not a starter".

⚠️ **`BASE` 0 means past `D`** — outside the rosterable band on every board that reaches it.
That is a statement of value, **not** a failed name join. Every all-boards absence here was
hand-checked (`evaluating-players`), which is how three of our own rows were caught: the
boards carry **Marvin Bagley III**, **DaRon Holmes II** and **Karlo Matkovic** (no diacritic),
all of which a naive join records as absent from every board and `team-eval` then reads as
BASE ~0. They carry real ranks. `boards-2026-07-29.md` has the worked cases.

| Player | dizP | htP | crd | **BASE** | FPts/G | GP | GP proj | **WINS** | **Δw** | σ | **LATE** | AGE | ELIG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| Kawhi Leonard | 68 | 107 | 90 | **1724** | 44.4 | 65 | 63 | 2.29 | **+2.10** | 17.1 | ✗ age 35 · 2/4 under 60 | 35.1 | SF/PF |
| Cade Cunningham | 6 | 6 | 5 | **8163** | 46.7 | 65 | 62 | 2.28 | **+1.93** | 3.2 | ✓ 1 of 5 under 60 | 24.8 | PG/SG |
| Amen Thompson | 18 | 24 | 14 | **5360** | 39.3 | 79 | 68 | 2.03 | **+1.91** | 46.9 | ✓✓ none under 60 in 3 | 23.5 | SG/SF |
| Josh Giddey | 24 | 28 | 44 | **4137** | 42.2 | 54 | 59 | 1.83 | **+1.49** | 6.4 | ✓ 2 of 5 under 60 | 23.8 | PG/SG |
| Jalen Duren | 35 | 36 | 27 | **3817** | 39.2 | 70 | 64 | 1.75 | **+1.42** | 15.7 | ✓✓ none under 60 in 4 | 22.7 | C |
| Jimmy Butler | 181 | 153 | 154 | **777** | 37.6 | 38 | 53 | 1.46 | **+1.26** | 9.3 | ✗ age 37 · 3/5 under 60 | 36.9 | SF/PF |
| Kyrie Irving | 70 | 95 | 122 | **1650** | *38.0* | 0 | 57 | 1.46 | **+1.15** | 21.2 | ✗ age 34 · 3/4 under 60 | 34.4 | PG/SG |
| Desmond Bane | 57 | 66 | 67 | **2309** | 33.0 | 82 | 69 | 1.32 | **+0.93** | 12.2 | ✓ 2 of 5 under 60 | 28.1 | PG/SG |
| Naz Reid | 105 | 77 | 104 | **1553** | 27.4 | 77 | 66 | 0.96 | **+0.82** | 1.1 | ✓✓ none under 60 in 5 | 26.9 | PF/C |
| Darius Garland | 32 | 43 | 58 | **3281** | 31.9 | 45 | 55 | 0.98 | **+0.80** | 8.8 | ✓ 2 of 5 under 60 | 26.5 | PG/SG |
| Zach Edey | 51 | 61 | 69 | **2451** | 33.7 | 11 | 43 | 0.88 | **+0.62** | 0.8 | – 2 rotation seasons (66/11) | 24.2 | C |
| Fred VanVleet | 134 | 74 | 161 | **1295** | *29.0* | 0 | 60 | 0.84 | **+0.61** | 4.4 | ✗ missed '25-26 whole | 32.4 | PG/SG |
| Jalen Suggs | 80 | 92 | 103 | **1630** | 30.5 | 57 | 60 | 0.96 | **+0.57** | 11.5 | ✗ 4 of 5 under 60 | 25.2 | PG/SG |
| Myles Turner | 129 | 104 | 135 | **1162** | 24.7 | 71 | 63 | 0.70 | **+0.47** | 9.9 | ✓ 1 of 5 under 60 | 30.3 | PF/C |
| Jakob Poeltl | 133 | 135 | 307 | **820** | 25.8 | 46 | 54 | 0.55 | **+0.35** | 5.9 | ✗ 3 of 5 under 60 | 30.8 | C |
| **Marvin Bagley** → released | 317 | 453 | 637 | **82** | 22.8 | 60 | 58 | 0.50 | **+0.27** | 1.6 | ✗ 3 of 4 under 60 | 27.4 | SF/PF |
| Coby White | 93 | 113 | 106 | **1400** | 25.8 | 50 | 55 | 0.55 | **+0.25** | 3.7 | ✓ 1 of 5 under 60 | 26.5 | PG/SG |
| Jay Huff | 271 | 223 | 534 | **288** | 20.7 | 82 | 65 | 0.24 | **+0.21** | 5.7 | – 2 rotation seasons (7/82) | 28.9 | C |
| De'Anthony Melton | 229 | 231 | 418 | **342** | 22.7 | 49 | 54 | 0.32 | **+0.17** | 3.4 | ✗ 3 of 5 under 60 | 28.2 | PG/SG |
| Anfernee Simons | 198 | 155 | 155 | **734** | 21.4 | 55 | 55 | 0.24 | **+0.15** | 17.2 | ✗ 3 of 5 under 60 | 27.1 | PG/SG |
| Khris Middleton | 347 | 331 | 553 | **119** | 18.8 | 63 | 57 | 0.20 | **+0.04** | 25.2 | ✗ age 35 · 3/5 under 60 | 35.0 | SF/PF |
| Adem Bona | 284 | 303 | 410 | **205** | 14.2 | 71 | 58 | -0.14 | **-0.09** | 0.9 | – 0 rotation seasons | 23.3 | SF/PF |
| Chaney Johnson | - | - | - | **0** | 19.1 | 18 | 40 | 0.15 | **-0.10** | 2.6 | – 1 rotation season (17) | 24.1 | SG/SF |
| Karlo Matković | 338 | 342 | 448 | **121** | 14.2 | 62 | 55 | -0.13 | **-0.13** | 0.9 | – 1 rotation season (42) | 25.3 | PF/C |
| Khaman Maluach | - | 154 | 340 | **559** | *16.0* | 46 | 50 | -0.12 | **-0.14** | 4.1 | – 0 rotation seasons | 19.9 | C |
| Sion James | 384 | 294 | 344 | **161** | 13.9 | 82 | 62 | -0.33 | **-0.19** | 0.8 | – 0 rotation seasons | 23.7 | PG/SG |
| Keon Ellis | 346 | 214 | 411 | **248** | 14.7 | 72 | 59 | -0.25 | **-0.20** | 0.4 | – 1 rotation season (80) | 26.6 | PG/SG |
| DaRon Holmes | 310 | 333 | 390 | **166** | *14.0* | 26 | 41 | -0.11 | **-0.21** | — | – 0 rotation seasons | 24.0 | SF/PF |

### `LATE` — how this column was scored

Legend, causes and the four thresholds: **`team-eval` §`LATE`**. Same rule on all three eval
files, so the column is comparable across them.

Scored on the two of `team-eval`'s three causes this repo can evidence: **`AGE`** (the column),
and **chronic absence** off pool `GP` for '21-'25 (`sim.py gp`). The rate **≥ 15**
rotation-season filter is what keeps Huff (7/82) and Ellis (80) out of the `✗` bucket instead
of a hand-typed override. **9 of our 28** land on `–` for under 3 rotation seasons; that is the
honest answer, not a gap.

⚠️ **"NBA team habitually out of it late" is not scored** — no in-repo source for NBA standings,
and `team-eval` gives team-incentive risk no dynasty weight. Check by hand if a call turns on it.

⚠️ **A screen, not a verdict.** It is blind to *when* in the season games were missed, which is
the thing `LATE` actually names.

**The shop decision lands on this column.** Kawhi is the roster's #1 row at 17.1σ *and* its
worst `LATE` risk — the file's one genuinely hard call, and `team-eval` caps the answer at a
tiebreak: no discount, no column, no aging term in `Δw`.

## Picks — Sept '26 (pre-execution)

Priced off the Dizzle dynasty board's **slot-prefixed rookie rows** — an exact board
rank per slot, on the same board used for players. Look up by **overall ordinal**
`(R-1)*12 + S`, never by the label.

**`VALUE` here is Dizzle alone, not the 50/50 pick blend** — `evaluating-picks` §*4. BASE*
drops the crowd board while its pick rows carry a class-normalising notice, which they do.

| Pick | ordinal | chart slot | board rank | **VALUE** | would take | after 483809 |
|---|---:|---|---:|---:|---|---|
| 1.09 | 9 | 1.09 | 95 | **1524** | Brayden Burries | **gone** → The Don |
| 2.09 | 21 | 1.21 | 185 | **645** | Karim Lopez | kept |
| 3.09 | 33 | 2.03 | 255 | **357** | Richie Saunders | kept |

**Post-execution we hold 2 rookie picks, not 3** — so we fill to 38 in September with 2
rookies + 7 auction bodies + 1 hole, against `sim.EXPANSION`'s assumed 3 + 7. Nothing in
this file re-measures that; `lineup-math/README.md` §*Sept '26 expansion* is the basis.

**Incoming: two 2027 2nds.** From `FetchTrades` `picksObtained` — one is **The Don's own**
(no `originalOwner`), one originates from **King Christopher of Bavaria** (`originalOwner`,
`traded: true`). ⚠️ **The `slot` values in that record (2.03, 2.11) are placeholders keyed to
the *2026* order** — `FetchLeagueDraftBoard?season=2027` returns `{}`, and the '27 order is
set by the '26-27 finish. Price them by **originating team** off `team-projections.md`
(King Christopher is projected 10th in '26-27, The Don 6th), method in `evaluating-picks`
§*Future picks*. Do not read a slot off the trade record.

## Post-execution — measured, not projected

Same basis as above: 28 real bodies padded to 38, Bagley removed, Mark Williams added at
his own projected shape (rate 27.5, `GP proj` 60, BASE **1307**, centre, AGE 24.6,
`LATE` **✗ 3 of 4 under 60** — 43/19/44/60).

| | pre | post |
|---|---:|---:|
| `REPL` guard / forward / centre | 18.0 / 16.1 / 17.8 | **18.3 / 15.7 / 18.6** |
| `K` guard / forward / centre | 782 / 779 / 781 | 781 / 778 / 781 |
| median `BASE` (28 rows) | 991 | **1,228.5** |
| median `Delta w` (28 rows) | +0.410 | **+0.434** |

⚠️ **No per-player post `Delta w` is published here, and the pre table is not a substitute.**
Forward `R` falls 0.4 and centre `R` rises 0.8, so **every centre loses and the top of the
table reorders** — but the top pair moves inside 0.1 wins, which `team-eval` calls a tie. To
price anything post-execution, **re-run `sim.py players` on the re-fetched roster file**; a
scaled pre figure is not a measurement. The one exception, because it is the piece we are
buying: **Mark Williams is +0.36 to us against +0.59 to The Don** — market value, not wins, and
the whole depth penalty in one row.

**Bucket effects.** `my-team-situation` owns the grid and it must be recut on the post rows
(BASE above, `Delta w` from the re-run). On the post `BASE` median alone, **Myles Turner
(1162), Fred VanVleet (1295) and Mark Williams (1307) all sit within 10% of 1,228.5**, so all
three are **unbucketed** whatever their `Delta w` — decide on other grounds, not on the cell.
