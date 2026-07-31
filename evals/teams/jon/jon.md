# SGA-the-Great (Jon, `KIMJONIL`, 161015) — dynasty values

**Derived 2026-07-30.** Re-derive from scratch; do not copy this header (`team-eval`).

**BASE** is blended points-format board rank and nothing else — no adjustment by us for
injury, role, situation or contract. **WINS** is what a player banks **for a specific
roster**, so it is reported twice below and the two are not interchangeable. **`TVAL`** is
BASE-unit worth **to us**, on **our** `κ` and **our** horizon — computed for a **shortlist
only**, which is what `team-eval` §`TVAL` asks of a counterparty eval.

This is a **counterparty** eval, so the player table **sorts on BASE**, never on `Δw theirs`
(`team-eval` §Output). Gettability is `trades`'s **`GET`** — recent `FPts/G` + `AGE` + their
situation + light BASE — and is never inferred from any of our own value columns.

| | |
|---|---|
| Blend | 40% Dizzle Points · 35% Hashtag Points · 25% Hashtag crowd. Dynatyze not blended |
| Board depths | Dizzle **450** (< `D`, so absence renormalises) · Hashtag Points **772** · crowd **764** |
| Board stamps | Dizzle **10 Jul 2026** · Hashtag Points **2 Jul 2026** · crowd **29 Jul 2026** |
| Curve | `D = teams x roster_size = 456` · `a = sqrt(D) = 21.354` · `V(r) = 9999*(a+1)/(D-1)*(D-r)/(a+r)`, 0 at or past `D` |
| `roster_size` | **38 — the announced post-Sept size**, not today's 28. Flagged per `team-eval` |
| `REPL` basis | **`sim.basis(path)` — both rosters padded to 38 bodies**, the only basis on which `WINS` compares across teams |
| `REPL` theirs | guard **12.0** · forward **11.3** · centre **14.2** (`K` **778** all three) |
| `REPL` ours | guard **18.3** / `K` 781 · forward **15.7** / 778 · centre **18.6** / 781 — **post-483809**, re-measured today |
| Horizon | `delta = 0.875`, H = 3 seasons, `Sum delta = 2.641` |
| `kappa` theirs | **924** sim layer (n=17, quartiles **523–1308**) · 379 formula layer (n=24, 212–468) |
| `kappa` **ours** — the one `TVAL` uses | **940** sim layer, quartiles **630–1312** (`../my-team/my-team.md` §`kappa`) |
| `TVAL` | `kappa_ours x Sum delta x M_t x Delta w ours`, `Delta w ours` **sim-measured on our padded-38 roster**. `M_t` = **1.0** all three seasons — we project 2nd/2nd/4th (`team-projections.md`), i.e. top seed throughout. So the multiplier is a flat **940 x 2.641 = 2,482** per win, band **1,664–3,465** |
| Record | **7-12, 10th by record, 11th of 12 by PF** (22,657.5) — `FetchLeagueStandings?season=2025` |
| Live bodies | **27** (`FetchLeagueRosters`), against `maxRosterSize` 28 |

## ⚠️ Both roster files were hand-reconciled — read this before quoting a body

`FetchRoster?season=` is a snapshot as of the season's last lineup period, so it trails the
live roster in **composition**, not only in count. Diffed against `FetchLeagueRosters`:

- **Theirs:** the snapshot carried **Brandon Williams** and was missing **Josh Minott**.
  Minott was added from `players-2025-26.json` at his sourced '25-26 line (16.087 rate, 49
  GP, SF/PF) and Brandon Williams removed. 27 bodies either way.
- **Ours:** trade **483809 has executed** (`FetchTrades?filter=TRADES_COMPLETED`,
  `approvedOn` 2026-07-29T21:10Z; **0 pending trades league-wide**, and Mark Williams is on
  our live roster per `FetchLeagueRosters`). The
  snapshot still carried **Marvin Bagley** and lacked **Mark Williams**; same fix (27.483
  rate, 60 GP, C). The resulting `REPL` reproduces `../my-team/my-team.md` §*Post-execution*
  exactly — 18.3 / 15.7 / 18.6 — which is the check that the reconciliation is right.

**Re-run `fetch_data.py roster 161015 161025` and re-apply both fixes before quoting any
`WINS` figure from this file.** Do not assume a fresh fetch is clean.

✅ **Both fixes are baked into the working-tree JSON as of 2026-07-30** — the files carry 27
and 28 bodies with Minott/Mark Williams present and Brandon Williams/Bagley absent, and
`sim.basis('roster-161025-2025-26.json')` re-prints 18.3 / 15.7 / 18.6. Every `Delta w ours`
in §*Shortlist* was measured on that basis. This is the state to preserve, not to re-fetch.

⚠️ **`WINS` is not comparable across rosters of different size, and `REPL` tracks size
before shape.** Everything below is on the padded-38 basis for both teams.

## Their bar is the lowest measured in this repo — a fact about transfer, not a target list

`REPL` theirs against ours, by group:

| group | theirs | ours | our bar is higher by |
|---|---:|---:|---:|
| guard | 12.0 | 18.3 | **+6.3** |
| forward | 11.3 | 15.7 | **+4.4** |
| centre | 14.2 | 18.6 | **+4.4** |

For comparison, The Don sits at 12.4 / 13.6 / 14.0 and Pharaoh at 11.9 / 12.5 / 11.8
(`../mitch/mitch.md`, `../matthew/matthew.md`). **Their forward bar of 11.3 is the lowest
figure in any eval in this repo.** Their tightest group is **centre** — 5 bodies pure to it
for 3 slots; crowding a group lifts its `R`.

Consequences, and the third one is the boundary on the first two:

1. **Every player they own reads ~0.3–0.5 wins more valuable on their roster than on ours.**
   That gap *is* `team-eval`'s depth penalty. `W theirs` is not a price we can pay.
2. **The gap is smallest on forwards and centres (+4.4) and worst on guards (+6.3)** — so a
   guard of a given rate transfers to us worse than a forward or centre of the same rate.
   That is a **tiebreak between two otherwise-equal candidates**, sized at roughly the same
   place `lineup-math/README.md` §*Positional premium* puts it (+13% on a rate-25 body,
   ~+0.09 wins), and it is already **inside** every `Delta w ours` measured below. Do not
   also apply it on top.
3. ⚠️ **A low `REPL` says their assets are replaceable *to them*. It does not say they are
   cheap to buy, and it selects nothing.** Gettability is `GET` (`trades`); worth to us is
   `TVAL`. **Never target, sort or shortlist off `Delta w theirs` or off this table**
   (`team-eval` §`WINS`). The previous version of this file derived "do not buy their guards"
   from exactly that conflation — a rule which, applied literally, would have excluded the
   only asset on the roster worth a conversation.
4. **Acquisitions price on `Delta w ours`; what they give up prices on `Delta w theirs`.**
   Never the reverse.

⚠️ **The sign is per group and per roster.** King Christopher's *forward* bar sits above ours
(`../my-team/my-team.md` §`WINS`). Run `sim.replacement` on a counterparty's padded file before
assuming a direction.

## `kappa` — the two layers diverge much harder here than on our own roster

| layer | `kappa` theirs | quartiles | n | ours |
|---|---:|---|---:|---:|
| **sim** — use against a `sim.py players` `Delta w` | **924** | 523–1308 | 17 | 940 |
| formula first cut | 379 | 212–468 | 24 | 631 |

The **sim layer lands within 2% of ours**, but the **formula layer is 40% below** it. That is
not a fact about the market — it is their low `REPL` inflating the formula's `w` term, which
divides into BASE. The formula layer is the one that breaks across rosters with very
different bars; the sim layer is the one to quote. **Calibrate on the layer of the `Delta w`
you are multiplying** (`team-eval` §`kappa`), and quote the band, never the point.

**Sourced vs modelled.** Board ranks, `FPts/G`, `GP`, `AGE`, `ELIG` are sourced. `GP proj`,
both `WINS` columns, `Delta w` (theirs **and** ours), `REPL`, `K`, `kappa`, **`TVAL`**,
`LATE` and every 2027 pick figure are modelled. **`GET` is judgment** — a coarse
high/mid/low, never a value, never summed, never in a verdict (`trades`). A sourced price
and a modelled figure never bracket a range.

## Players

Sorted by **BASE**, descending — the sort a counterparty eval takes (`team-eval` §Output),
because sort order reads as buy priority and BASE is the only column here that is a price.
`FPts/G` and `GP` are last season **actual**, reporting only; `GP proj` is `sim.project_gp`
as `our_roster` rounds it — the integer the sim ran. No row needed a projected rate: every
one of the 27 played in '25-26.

- **`W theirs` / `W ours`** = `(rate - REPL) x GP proj / K`, per slot group (`ELIG` mapping:
  `{C}` centre · subset of `{PG,SG}` guard · anything else **forward**), on their `REPL` and
  on ours. A **first cut**, and a working column — never a decision column, never a target.
- **`Delta w theirs`** = wins lost if he were swapped for a replacement-level 11.3-rate,
  68-GP forward **on their roster**, averaged over 3 x 200 trials. That is the counterfactual.
  It prices only what they give up inside a concrete deal.
- **`TVAL`** = BASE-unit worth to us, on the shortlist only (§*Shortlist*). `—` = not
  computed, **not** zero.
- **σ** = gap to the next row **in the `Delta w theirs` ordering**, in sigma of that gap —
  carried over unchanged, so on this BASE-sorted table it does **not** describe the row below.
  Read it only against the unordered-pairs list under the table. `-` = off that board.

| Player | dizP | htP | crd | **BASE** | **TVAL** | FPts/G | GP | GP proj | W theirs | W ours | Δw theirs | σ | **LATE** | AGE | ELIG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| Shai Gilgeous-Alexander | 2 | 2 | 4 | **9352** | **5844** | 48.5 | 68 | 64 | +3.00 | +2.47 | +2.62 | 39.8 | ✓ 1 of 5 under 60 | 28.1 | PG/SG |
| Alperen Şengün | 14 | 11 | 18 | **6188** | **4171** | 43.6 | 72 | 65 | +2.46 | +2.08 | +2.19 | 217.7 | ✓✓ none under 60 in 5 | 24.0 | C |
| Kel'el Ware | 66 | 67 | 74 | **2126** | **938** | 28.1 | 77 | 66 | +1.18 | +0.80 | +0.78 | 5.3 | – 2 rotation seasons | 22.3 | C |
| Ace Bailey | 90 | 105 | 53 | **1789** | **—** | 23.8 | 72 | 63 | +1.01 | +0.66 | +0.68 | 4.4 | – 1 rotation season | 20.0 | PF/SF |
| Jeremiah Fears | 111 | 106 | 89 | **1393** | **—** | 24.8 | 82 | 67 | +1.10 | +0.56 | +0.74 | 6.7 | – 1 rotation season | 19.8 | PG/SG |
| Cason Wallace | 130 | 133 | 110 | **1107** | **—** | 21.7 | 77 | 63 | +0.78 | +0.27 | +0.33 | 3.4 | ✓✓ none under 60 in 3 | 22.7 | PG/SG |
| Maxime Raynaud | 151 | 131 | 116 | **1019** | **—** | 24.9 | 74 | 64 | +0.88 | +0.52 | +0.48 | 7.4 | – 1 rotation season | 23.3 | C |
| Peyton Watson | 104 | 114 | 465 | **986** | **—** | 26.5 | 54 | 57 | +1.06 | +0.60 | +0.62 | 9.7 | – 2 rotation seasons | 23.9 | PG/SG |
| Day'Ron Sharpe | 124 | 141 | 464 | **782** | **12** | 23.6 | 62 | 59 | +0.71 | +0.38 | +0.22 | 2.4 | ✗ 2 of 4 under 60 | 24.7 | C |
| Jaylen Wells | 231 | 150 | 160 | **683** | **541** | 20.4 | 69 | 60 | +0.70 | +0.37 | +0.28 | 3.8 | – 2 rotation seasons | 22.9 | PF/SF |
| Daniss Jenkins | 202 | 168 | 260 | **571** | **—** | 19.1 | 72 | 60 | +0.55 | +0.06 | +0.13 | 6.0 | – 1 rotation season | 25.0 | PG/SG |
| Danny Wolf | 200 | 253 | 212 | **483** | **—** | 19.1 | 57 | 55 | +0.55 | +0.24 | -0.02 | 7.1 | – 1 rotation season | 22.2 | PF/SF |
| Justin Champagnie | 272 | 256 | 184 | **410** | **323** | 20.9 | 69 | 60 | +0.74 | +0.40 | +0.38 | 2.7 | – 2 rotation seasons | 25.1 | SF/SG |
| Terrence Shannon | - | 180 | 509 | **393** | **—** | 8.5 | 44 | 45 | -0.16 | -0.42 | -0.16 | 1.2 | – 0 rotation seasons | 26.0 | SF/SG |
| Taylor Hendricks | 246 | 233 | 286 | **373** | **—** | 16.2 | 59 | 54 | +0.34 | +0.03 | -0.01 | 1.3 | ✗ 3 of 3 under 60 | 22.7 | PF/SF |
| Nolan Traore | 225 | 258 | 345 | **343** | **—** | 16.8 | 56 | 54 | +0.33 | -0.11 | -0.10 | 3.2 | – 1 rotation season | 20.2 | PG/SG |
| Josh Minott | 210 | 255 | 654 | **334** | **—** | 16.1 | 49 | 51 | +0.31 | +0.03 | -0.17 | 3.4 | – 1 rotation season | 23.7 | SF/PF |
| Tristan da Silva | 239 | 307 | 268 | **322** | **45** | 19.0 | 77 | 62 | +0.61 | +0.26 | +0.17 | 6.1 | – 1 rotation season | 25.2 | PF/SF |
| Miles McBride | 256 | 252 | 488 | **270** | **—** | 21.4 | 41 | 50 | +0.60 | +0.20 | +0.23 | 0.7 | – 2 rotation seasons | 25.9 | PG/SG |
| Yves Missi | 312 | 260 | 357 | **237** | **—** | 19.0 | 66 | 58 | +0.36 | +0.03 | +0.05 | 3.1 | – 2 rotation seasons | 22.2 | C |
| Ryan Dunn | 311 | 251 | 404 | **230** | **—** | 16.0 | 70 | 58 | +0.35 | +0.02 | +0.00 | 1.4 | – 1 rotation season | 23.6 | PF/SF |
| Moses Moody | 265 | 304 | 395 | **229** | **—** | 22.2 | 60 | 57 | +0.75 | +0.28 | +0.34 | 0.7 | ✓✓ none under 60 in 3 | 24.2 | PG/SG |
| Jaylin Williams | 318 | 245 | 687 | **216** | **—** | 18.9 | 65 | 58 | +0.56 | +0.24 | +0.20 | 2.3 | ✗ 2 of 3 under 60 | 24.1 | PF/SF |
| Jase Richardson | 267 | 344 | 415 | **193** | **—** | 8.1 | 54 | 49 | -0.25 | -0.64 | -0.20 | 0.2 | – 0 rotation seasons | 20.8 | PG/SG |
| Tyrese Proctor | 368 | 479 | 213 | **172** | **—** | 9.7 | 50 | 48 | -0.14 | -0.53 | -0.21 | 4.6 | – 0 rotation seasons | 22.3 | PG/SG |
| Jaden Ivey | 401 | 427 | 222 | **155** | **—** | 15.7 | 37 | 46 | +0.26 | +0.00 | -0.29 | — | ✗ 2 of 4 under 60 | 24.5 | PG/SG/SF |
| Tristan Vukcevic | 361 | 396 | 309 | **128** | **—** | 15.5 | 49 | 50 | +0.27 | -0.01 | -0.08 | 1.7 | ✗ 3 of 3 under 60 | 23.4 | PF/SF |

⚠️ **State no order below ~2σ, in the `Delta w theirs` ordering** (not this one). Unordered
there: **Moody/Wallace 0.7σ · McBride/Sharpe 0.7σ · Richardson/Proctor 0.2σ · Shannon/Minott
1.2σ · Hendricks/Wolf 1.3σ · Dunn/Hendricks 1.4σ · Vukcevic/Traore 1.7σ.** Below Raynaud that
ordering is close to one undifferentiated block: twenty players spanning **+0.38 to −0.29**,
a range of 0.67 wins.

⚠️ **BASE separates this roster where nothing else does.** The three names above 2,000 and the
twenty below 700 are two different conversations, and the BASE sort is the one that says so —
the `Delta w theirs` sort put Champagnie (410) 8th and Wallace (1,107) 10th, which is a
statement about *their* depth, not about price.

⚠️ **`W theirs` reorders this table and cannot be trusted to.** It puts **Danny Wolf at
+0.55** against the sim's **−0.02** and **Josh Minott at +0.31** against **−0.17** — both
*sign flips*, both the documented failure mode (`(rate - REPL) x GP` charges the replacement
body only at the departing player's own `GP`, so a 51-GP body is never charged for the 68
games the replacement plays). Every low-`GP` row here is inflated. **Sort with `Delta w`.**

⚠️ **A negative `Delta w` does not mean worse than an empty slot.** It is a producer metric,
unreliable at and below replacement; sub-replacement players still pay as light-night bodies.
Read the sign as "not a starter" — and on this roster that is eight of twenty-seven.

⚠️ **`W ours` is a formula figure on our `REPL`, not a sim measurement** — and on this roster
it is not merely 1.5x off, it is off in the **wrong direction**. Every shortlisted player
below measures *lower* on the sim than the formula predicts (Sharpe +0.38 → **+0.005**, da
Silva +0.26 → **+0.018**, Wells +0.37 → **+0.218**), because `(rate - REPL) x GP` charges the
replacement body only at the departing player's own `GP` while the sim charges a full 68-GP
replacement. **Never price an acquisition off `W ours`.**

### Shortlist — the seven names given a `TVAL` read, and why these seven

`team-eval` §`TVAL`: a counterparty gets a **shortlist**, not a whole table. Selected on
`GET` (`trades` — recent `FPts/G` + `AGE` + their situation + light BASE) crossed with our
actual needs (`my-team-situation`: bottom-of-roster bodies first, forwards over guards), then
filtered to names with **real BASE**. Excluded, and the reason: their **young risers**
(Bailey 20.0, Fears 19.8, Traore 20.2, Richardson 20.8, Raynaud 23.3, Watson 23.9, Missi
22.2, Wolf 22.2) are what a rebuilder refuses at any price — `GET` high, availability nil.
Their **pure guards under 700 BASE** (Jenkins, McBride, Moody, Proctor, Ivey) are gettable
but land in our guard glut. Wallace is a guard at 1,107.

`Delta w ours` is **sim-measured on our padded-38 roster** — `sim.swap(sim.basis(
'roster-161025-2025-26.json'), ["FA6"], [him])` then `sim.player_wins`, 3 x 200 trials. The
counterfactual is therefore **"he replaces a bottom auction body"**, not "he replaces a named
player of ours" — the same counterfactual `kappa` is calibrated on, and the reason no
swap-out had to be assumed. His rate is his sourced '25-26 line and his GP is `project_gp`,
identical to the `GP proj` column.

`TVAL = 940 x 2.641 x 1.0 x Delta w ours`. **No productive-window truncation applies**: the
oldest name here is 25.2 and SGA is 28.1→31.1 across the window.

| Player | `GET` | **BASE** | `Delta w ours` | ± | **TVAL** | band (630–1312) | gap | `kappa*` |
|---|---|---:|---:|---:|---:|---|---:|---:|
| Shai Gilgeous-Alexander | **high**, but *available* | **9352** | +2.354 | .009 | **5844** | 3917–8157 | **−3508** | 1504 |
| Alperen Şengün | **high**, and not available | **6188** | +1.680 | .008 | **4171** | 2795–5821 | **−2017** | 1395 |
| Kel'el Ware | high | **2126** | +0.378 | .003 | **938** | 629–1310 | **−1188** | 2130 |
| Day'Ron Sharpe | low–mid | **782** | +0.005 | .002 | **12** | 8–17 | **−770** | 59220 |
| Jaylen Wells | mid | **683** | +0.218 | .006 | **541** | 363–755 | **−142** | **1186** |
| Justin Champagnie | **low** | **410** | +0.130 | .004 | **323** | 216–450 | **−87** | **1194** |
| Tristan da Silva | **low** | **322** | +0.018 | .003 | **45** | 30–62 | **−277** | 6774 |

**Every one of the seven prices `TVAL` < BASE. Nothing on this roster is underpriced for us.**

- **Two rows sit inside `kappa`'s band and are therefore undecided on this method** — Wells
  flips at `kappa` = **1,186** and Champagnie at **1,194**, both inside 630–1312. Report the
  flip point and decide on other grounds (`team-eval` §`kappa`); do **not** report a sign the
  band does not support.
- **The five others clear the band.** SGA's `kappa*` of 1,504 and Şengün's 1,395 both sit
  above Q3 = 1,312, so the negative sign holds — but only just, and the SGA figure is one
  `kappa` re-derivation away from being a coin flip.
- ⚠️ **`TVAL` is flat inside the window and therefore systematically underrates this
  roster** (`team-eval` §`TVAL`). Median age here is **23.6**; Ware, Wells and Bailey are all
  measured on last season's rate held constant for three seasons, with no improvement curve
  by design. **A low `TVAL` on a 22-year-old is not a sell signal and not evidence he is
  overpriced** — it is the method declining to forecast. The gap columns above are honest for
  SGA (28) and Champagnie/da Silva (25) and soft for everyone under 24.

### `LATE` — how this column was scored

Legend, causes and thresholds: **`team-eval` §`LATE`**. Same rule as `../my-team/my-team.md`,
`../mitch/mitch.md` and `../matthew/matthew.md`, so the column is comparable across all four.

Scored on the two causes this repo can evidence: **`AGE`**, and **chronic absence** off pool
`GP` for '21–'25 (`players-2025-26.json`), counting only **rotation seasons** — a pool season
at rate ≥ 15, below which `GP` measures role rather than health.

**Nobody on this roster is 34+, and nobody missed a whole season.** So no `✗` here is
age-driven; all five are absence-driven.

| | count | who |
|---|---:|---|
| `✓✓` | 3 | Şengün · Wallace · Moody |
| `✓` | 1 | SGA |
| `✗` | 5 | Sharpe · Jaylin Williams · Hendricks · Vukcevic · Ivey |
| `–` | **18** | under 3 rotation seasons |

⚠️ **18 of 27 unknown is the honest answer, not a gap** — this is a very young roster (median
age **23.6**), and most of it simply has no track record to read. `LATE` is a
**contenders-only tiebreak** and it is nearly information-free on this team; do not lean on it.

⚠️ **"NBA team habitually out of it late" is not scored** — no in-repo source, and `team-eval`
gives team-incentive risk no dynasty weight. Check by hand if a call turns on it.

⚠️ **A screen, not a verdict.** It is blind to *when* in the season games were missed, which
is the thing `LATE` actually names.

## Shape

**Two stars and a cliff, and the cliff is severe.**

- SGA (9,352) + Şengün (6,188) = **15,540 of 30,484 total roster BASE — 51% in two players.**
- Third-best BASE is Kel'el Ware at **2,126**. Only **3 rows clear 2,000**; only **7** clear
  1,000. Twenty of twenty-seven sit under 700.
- Top-9 by rate: **266.0 FPts/G** against our **348.0** — an **82-point** gap over nine
  nightly slots, and their third-best rate is 28.1 against our seventh-best of 33.7.
- Pure bodies per slot group: **guard 10 · forward 9 · centre 5**. Nine starting slots.

This is `team-projections.md`'s read, independently reproduced: fourteen players in the
16–25 FPts band is not a substitute for a third 30+ producer when nine slots must be filled
nightly. **They do not have a bottom-of-roster problem — they have a top-of-roster problem**,
which is the opposite of ours.

## Picks — Sept '26 draft (set by the '25-26 finish, which is final)

Read off `FetchLeagueDraftBoard?season=2026` — real slots, not placeholders. Priced off the
Dizzle dynasty Points board's **slot-prefixed rookie rows** (`evaluating-picks` §4), looked up
by **overall ordinal** `(R-1)*12 + S`, never by the label.

**`VALUE` is Dizzle alone, not the 50/50 pick blend** — the crowd `/keeper` board carries a
live class-normalising notice (`../../board-snapshots/boards-2026-07-29.md`), which §4 says drops it.

| Pick | source | ordinal | chart slot | board rank | **VALUE** | would take | chart midpoint |
|---|---|---:|---|---:|---:|---|---:|
| **1.02** | own | 2 | 1.02 | 15 | **5959** | AJ Dybantsa | 5179 |
| 1.11 | King Christopher (465873) | 11 | 1.11 | 101 | **1425** | Aday Mara | 1267 |
| 2.02 | own | 14 | 1.14 | 125 | **1111** | Hannes Steinbach | 1009 |
| 2.04 | Mongol (465618) | 16 | 1.16 | 144 | **927** | Dailyn Swain | 802 |
| 2.08 | Yao Ming (477499) | 20 | 1.20 | 162 | **788** | Nate Ament | 645 |
| 2.10 | Jesus Christ (465874) | 22 | 1.22 | 186 | **640** | Tarris Reed Jr. | 645 |
| | | | | | **10,850** | | |

**Their own 3rd is gone** (→ Jesus Christ, 465874), so this is the whole Sept-'26 holding:
**two firsts and four seconds, no third.**

⚠️ `team-projections.md` §*SGA-the-Great* says "**five 2nds**" — that is a miscount. The board
says **four**, plus the acquired 1.11. Fix it there when that file is next touched.

**The prefix and the chart agree in direction and disagree in size** — the prefix runs 10–22%
above the chart midpoint on five of six slots and the flat-band artefact is live: chart slots
1.20 and 1.22 both price at midpoint 185 while the prefix separates them 162/186. Prefer the
prefix (`evaluating-picks` §4).

**10,850 of pick BASE against 30,484 of player BASE.** Their draft capital is **26% of their
total asset base** — by far the highest ratio in any eval in this repo.

## Picks — Sept '27 draft (set by the '26-27 finish) — **all modelled**

No board prices these. Slots are projected from the **originating** team's '26-27 rank
(`team-projections.md`), then run through the **current class's** slot→value lookup — which
prices *this* class, not that one (`evaluating-picks` §*A chart prices ONE class*). **Never
read a `slot` off a trade record** — those are placeholders keyed to the 2026 order.

A bolded rank is the modal projection; the range is the rank range. Every bottom-8 slot is a
**prior only** — the lottery reorders inside it.

| Pick | originating | '26-27 rank (range) | modal slot | ordinal | **VALUE (modal)** | range |
|---|---|---|---|---:|---:|---|
| **own 2027 1st** | SGA-the-Great | **12** (9–12) | 1.01 (prior) | 1 | **6757** | 4075–6757 |
| Yao's 2027 1st | Yao Ming (477499) | **8** (4–10) | 1.05 (prior) | 5 | **2795** | 1524–5623 |
| Mongol's 2027 2nd | Mongol (465618) | **9** (4–11) | 2.04 (prior) | 16 | **927** | 645–1111 |
| Pharaoh's 2027 2nd | Pharaoh (477499) | **5** (2–8) | 2.08 (prior) | 20 | **788** | 634–918 |
| King Chris's 2027 3rd | King Christopher (452349) | **10** (4–11) | 3.03 (prior) | 27 | **420** | 357–453 |
| Mongol's 2027 3rd | Mongol (465618) | **9** (4–11) | 3.04 (prior) | 28 | **416** | 357–453 |
| | | | | | **12,103** | |

**Their own 2027 2nd is gone** (→ King Christopher, 465873) and their own 2027 3rd is gone
(→ Yao Ming, 477499). Their own **2027 1st is unencumbered**, as is everything of theirs in
2028 — no 2028 pick of theirs has ever moved.

⚠️ **The Pharaoh 2027 2nd attribution is an inference, not a read.** In three-team trade
477499 that pick arrives with **no `originalOwner`**, and Pharaoh is the only party whose
outgoing assets are otherwise unaccounted for. `originalOwner` is inconsistently populated
for a sender's own pick (`team-projections.md` caveat 1), so absence is not a reliable
signal — **confirm with the owner before trading on this row.** It is 788 of a 12,103
holding, so nothing above turns on it.

⚠️ **Sourced upper bound on their own 2027 1st, and it is far below the modelled figure.**
Dynatyze's `2027 Early 1st` sits at rank **41** → **3,270**; `2027 Mid 1st` at rank 72 →
**2,021** (`../../board-snapshots/boards-2026-07-29.md`, 2026-07-29 snapshot — **re-fetch via `dynatyze` before
citing**). Against the modelled **6,757**. Do **not** present these as bracketing a range —
one is sourced and generic, one is derived off *this* class, whose 1.01 is Cameron Boozer at
board rank 11. **The 6,757 is the value of a 2026 1.01, borrowed.** A 2027 1.01 is worth what
the 2027 class turns out to be worth, and no one knows that yet. Treat 3,270 as the
market-anchored figure and 6,757 as the ceiling if the class is strong.

`team-projections.md` is right that **their own future 1sts are the most valuable in the
league over this window** — better than Han's, because Han bounces back and they don't.

## The roster cap collides with the pick haul

`maxRosterSize` goes to **38** in Sept '26 and the 10 new slots fill with 3 rookie picks +
a 7-man FA auction (`league-info`).

**They have 6 picks, not 3.** 27 live bodies + 6 rookies = **33**, leaving room for only
**5** of a 7-man auction before they hit 38. And that assumes they make all six picks.

- `sim.EXPANSION` assumes 3 picks + 7 auction bodies, so **the padding under every `Delta w`
  above is the standard fill, not their actual one.** The direction of the error: their real
  fill is *better* than the pad at the top (a 1.02 rookie beats an auction body) and the same
  at the bottom. Small, and it cuts against their players reading too cheap, not too dear.
- **Practical consequence for us: they are a natural seller of late picks**, because their
  last two or three Sept-'26 seconds convert into bodies they have no room for. That is the
  cheapest thing on this roster to buy, and the one they have a structural reason to move.

## What this means for us

We are **contending** (`my-team-situation`); they are the league's clearest rebuilder. That
asymmetry is correct on both sides — `team-eval` says a contender paying up for
old/durable/productive and a rebuilder refusing him are *both* right. Do not expect to buy
their youth cheap; expect to buy their *veterans* and their *surplus* cheap.

**1. SGA is the only genuinely actionable asset here — and at market he is a bad buy for us,
measured.** `team-projections.md` flags their incentive directly: trading SGA (28) or Şengün
(24) deepens the tank and improves their '28/'29 1sts. `GET` on him is **high** — 48.5
FPts/G, the pedigree, and every owner in the league prices that — but high `GET` plus a
rebuilder's own reason to sell is *availability*, not cheapness (`trades`: `GET` high +
`TVAL` high means pay up or walk).

**`Delta w ours` is now measured, not guessed: +2.354 ± 0.009**, so `TVAL` = **5,844** against
BASE **9,352**. Paying market is BASE-negative by **~3,500**, and the flip point `kappa*` =
**1,504** sits above our Q3 of 1,312, so the band supports that sign. He is worth opening on
**only at a real discount to 9,352** — roughly, we need to pay under ~6,000 of BASE for it to
clear, which on this roster's own pick table is about a 1.02 plus a mid second, not a haul.
⚠️ The 5,844 replaces the illustrative 6,200 in the previous version of this file, which used
a placeholder `Delta w` of +2.5; **quote 5,844, not 6,200.**

**2. Şengün is not gettable and should not be chased, and now the price says so too.** BASE
6,188, age **24.0**, `✓✓` on `LATE`, five rotation seasons with none under 60 — `GET` is as
high as it goes and a rebuilder keeps exactly this player. `TVAL` **4,171** against BASE
6,188 (`kappa*` 1,395, above Q3) says that even if he were gettable at market we should
decline. Both reads point the same way, which is the only place on this roster they do.

**3. Their guards are a tiebreak against us, not a prohibition — and the prohibition was
wrong.** The previous version of this file said *do not buy their guards*, derived from the
+6.3 `REPL` gap. That gap is real and measured, but it describes **transfer loss already
inside `Delta w ours`**, and it selects nothing (§*Their bar*). Read literally it excluded
SGA, the one name worth a conversation. The live reasons to prefer forwards back are our
**guard glut** (`my-team-situation` weakness 2) and the **+13% positional premium on a
marginal rate-25 body** (`lineup-math/README.md`) — a tiebreak between otherwise-equal
candidates, worth ~0.09 wins, and nothing that overrides a 2.35-win player.

**4. The cheap, gettable forwards do not clear, and two of them are genuinely undecided.**
`GET` is **low** on Champagnie (25.1) and da Silva (25.2) — the oldest useful bodies on a
rebuilder, no pedigree, both under 500 BASE — which is exactly the `GET`-low half of the
target test. But **da Silva measures +0.018 wins on our roster** (`TVAL` 45 vs BASE 322): our
forward bar is 15.7 and he supplies 19.0 at 62 GP, so he is a body, not an upgrade.
**Champagnie is the one honest near-miss** — `TVAL` 323 vs BASE 410, flipping at `kappa` =
1,194, inside the band. **Wells** (mid `GET`, 22.9) is the same picture at 541 vs 683,
flipping at 1,186. Neither is a mistake to acquire cheap; neither is an edge, and neither is
worth an ask that costs us a real asset. Their **2.08 and 2.10** remain the assets they have a
cap-driven reason to move, and they cost us nothing we need.

⚠️ **What this section cannot see.** Everything in points 3–4 is priced on a **flat** three-year
`Delta w`. Wells at 22.9 and Ware at 22.3 are precisely the profiles `TVAL` is documented to
underrate. If either takes a step, the `TVAL` reads above go stale before the BASE ones do —
this is the case for re-deriving after next season rather than for buying now.

**5. Their picks are the wrong currency for us.** Their own 2027 and 2028 1sts are the best
in the league, which is precisely why they will not sell them and why we — contending —
should not want them. `evaluating-picks`: a pick has no production dimension in year 1, and
for a contender trading a mid or late pick for a durable mid-tier producer wins on that axis
alone. **The trade direction that fits both teams is us sending a pick and taking back a
body**, not the reverse.

**6. Their real need is consolidation, and we are a poor supplier.** They need a third 30+
producer and have fourteen 16–25 bodies to pay with. Our surplus is also mid-tier
(`my-team-situation`), so a mid-for-mid swap does nothing for either side. **The only deal
shape with real gains from trade is one of their two stars for a package** — which, on the
measured figures, means **SGA at a discount and nothing else.**

**7. Ware is the trap.** BASE **2,126** makes him look like the accessible third piece, and he
is the one centre here whose rate (28.1) clears our bar of 18.6. But `GET` is **high** — 22.3,
ascending, on a rebuilder — and `TVAL` is **938**, a 1,188 gap with `kappa*` at 2,130, far
outside the band. He is the roster's clearest **`GET` high + `TVAL` low** row: the one
combination that is neither a target nor a pay-up, just a pass.

## Re-derive

```bash
cd evals/lineup-math
python3 fetch_data.py roster 161015 161025      # then re-apply the reconciliation above
python3 sim.py --roster roster-161015-2025-26.json replacement
python3 sim.py --roster roster-161015-2025-26.json players
python3 sim.py --roster roster-161015-2025-26.json gp
cd ../.. && python3 .claude/skills/evaluating-players/base.py \
  --roster evals/lineup-math/roster-161015-2025-26.json
```

`Delta w ours` / `TVAL` for a shortlisted name — a local computation on our roster, not a
fetch:

```python
import sim                                  # from evals/lineup-math
raw  = {p["n"]: p for p in sim._load("roster-161015-2025-26.json")}
ours = sim.basis("roster-161025-2025-26.json")     # 38 bodies; REPL 18.3 / 15.7 / 18.6
p = dict(raw["Jaylen Wells"])
p["gp"] = round(sim.project_gp(p["n"], gp=p["gp"], rate=p["avg"]))
sim.player_wins(sim.swap(ours, ["FA6"], [p]), [p["n"]])   # -> (Delta w, sd)
# TVAL = 940 * 2.641 * M_t * Delta w
```
