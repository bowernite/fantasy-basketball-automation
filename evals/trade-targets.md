# Trade targets

**Derived 2026-07-30.** A **shortlist of names** and nothing else — every rule this file used to
state is owned elsewhere, and names are the part that goes stale. Re-derive before acting.

## Recut 2026-07-30 — `GET` low + `TVAL` high

Targets now come from **`GET` low + `TVAL` high** (`trades` step 4: "`GET` low + `TVAL` high
is the target list"), not from `Δw theirs` or a counterparty's low `REPL`. Per player below:
`TVAL` is freshly sim-measured — the candidate added to **our** current roster
(`roster-161025-2025-26.json`, 28 bodies post-483809-execution, Mark Williams in) in place of
the bottom filler body (`sim.swap`, replacing Sion James), then `sim.player_wins` against our
own **forward `R` = 15.66** (post-execution, `teams/my-team/my-team.md` §*Post-execution*), 3×200
trials, `GP proj` off `sim.project_gp` on the player's own pool history. `TVAL = 940 × 2.641 ×
1.0 × Δw ours` — same `κ`, `Σδ`, `M` as `teams/my-team/my-team.md` (`M`=1.0 flat: we project top-4 all
three seasons). `GET` is judgment, not computed — recent `FPts/G` + `AGE` + their situation
(`team-projections.md`) + light BASE, per `trades`.

⚠️ **Exception, left untouched:** the **Neemias Queta / Pharaoh** row in Tier 1 and anything
about **SGA-the-Great** are **pending re-derivation in the Pharaoh/SGA thread** — a different,
concurrent session owns `teams/matthew/matthew.md`, `teams/matthew/matthew-trade-strategy.md`,
`teams/jon/jon.md` and `teams/jon/jon-trade-strategy.md`. Do not recompute those here; they're flagged
inline below and still read under the old `Δw theirs` rule until that thread lands.

Rules live in: `trades` (buy/sell profile, negotiation) · `team-eval` (body count, consolidation
cap, durability, the non-factor list) · `my-team-situation` (which of ours are *Core* vs
surplus — **that cell is the gate; no list here overrides it, in either direction**) ·
`evals/lineup-math/README.md` (every win figure, ladder and break-even — **re-run, never
quote**) · `evals/team-projections.md` (counterparty situation, whose future picks are worth
anything) · `evals/teams/my-team/my-team.md` (our own BASE and `Δw`).

⚠️ **Provenance:** every **owner** below was re-verified against `FetchLeagueRosters` on
**2026-07-30**. The **`FPts`/`GP`/`Age` columns were not** — they are the 2026-07-29
`FetchRoster` pull carried forward. Re-pull before quoting one, and never feed the `GP` column
into `WINS` (it is last-season actual; `sim.py gp` projects).

⚠️ **Pending trade 483809 executes 2026-07-31T00:00:00Z** (`FetchTrades`): our 1.09 out, Mark
Williams in, **Marvin Bagley released** — so Bagley is not a send body below, and every bucket
call moves with the post-execution medians (`teams/my-team/my-team.md` §*Post-execution*).

## Tier 1 — bottom-of-roster upgrades, and do these first

The cheapest wins measured, and a fraction of the dynasty cost of a top-end 1-for-1 — **read the
multiple off `lineup-math/README.md` §*Consolidation is not the lever*, never from here.** But it
buys **this season's slot-nights**, not a lasting edge: the September auction supplies part of
the same gain for nothing, and breadth stops differentiating once every team fills from the same
pool (`trades` → *Deal shape*).

**Send from** `my-team-situation`'s *Upgrade, don't shop* cell — on both median sets that is
Khaman Maluach · DaRon Holmes · Khris Middleton · Karlo Matković · Sion James · Keon Ellis ·
Adem Bona · Chaney Johnson (BASE and `Δw` per row: `teams/my-team/my-team.md`). The move is a **swap,
not a sale.** ⚠️ They are not all worthless: only **Chaney Johnson** is BASE 0, and **Maluach at
559 is the most valuable piece in the group by 2×** — a 19-year-old starting centre the expert
board has at 154. Never ship him as a sweetener.

**Get:** 22-29 FPts/G at **≥72 GP**, cheap.

| Target | Owner | FPts | GP | Age | **TVAL** | `GET` |
|---|---|---:|---:|---:|---:|---|
| Mikal Bridges | King Christopher | 28.8 | **82** | 29 | **2211** | medium — cliff-team seller, but stars "still price on last year's numbers" |
| Neemias Queta ⚠️ | Pharaoh | 28.0 | 76 | 27 | *pending re-derivation in the Pharaoh/SGA thread — do not recompute here* | *pending* |
| Collin Gillespie | Jesus Christ | 27.7 | 80 | 27 | **1372** | medium — contender with no pipeline, but he's a rotation piece not a core name |
| Naji Marshall | King Christopher | 26.6 | 74 | 28 | **1509** | low-medium — same cliff-team read as Bridges, less name recognition to anchor on |
| Toumani Camara | Matthew the Apostle | 26.4 | **82** | 26 | **1584** | medium — deep fringe roster (20 players 20+ FPts/G), spare complementary depth |
| Wendell Carter | Yao Ming | 26.3 | 78 | 27 | **1529** | low-medium — aging mid-tier pile around Jokić, no long-term fit for them |
| Cam Spencer | Yao Ming | 24.2 | 72 | 26 | **776** | low-medium — same Yao Ming retool-around-Jokić logic |
| Precious Achiuwa | Pascals | 24.0 | 73 | 26 | **1039** | medium-high — defending champs, "hardest team to pry anything loose from" |
| Quentin Grimes | Gutes | 23.6 | 75 | 26 | **704** | medium — injury-battered fringe roster, some retool pressure |
| Keldon Johnson | Gutes | 23.0 | **82** | 26 | **1067** | medium — same Gutes read |
| Sandro Mamukelashvili | Pascals | 22.9 | 80 | 27 | **924** | medium-high — same champs-hold-everything read as Achiuwa |
| Royce O'Neale | Yao Ming | 22.7 | 78 | 33 | **856** | low — 33, oldest name on this tier, least reason for a rebuilding-around-Jokić team to keep him |

⚠️ **Neemias Queta / Pharaoh** — the paragraph this file used to carry here (crowd rank
707, `Δw theirs` +1.15) is **pending re-derivation in the Pharaoh/SGA thread — do not
recompute here.** Left exactly as it was, under the old rule, until that thread lands.

**Read:** every `TVAL` here is real but modest (704-2211) — this tier is correctly priced as
bottom-of-roster bodies, not stars, and none of it moves the needle alone (§*Tier 1* header).
`GET` splits roughly by counterparty situation, not by player quality: **Yao Ming and Gutes
are the more willing sellers** (aging/injury-battered rosters retooling around one or two
real pieces), **King Christopher sells but anchors high** (cliff already arrived, market
hasn't repriced), and **Pascals holds everything** (defending champs) even at this modest a
tier — so the honest cheap gets skew toward Yao Ming (Carter, Spencer, O'Neale) and Gutes
(Grimes, Johnson) over Pascals (Achiuwa, Mamukelashvili), whose `TVAL` reads similarly but
whose owner is the least likely seller on this list.

⚠️ **Deandre Ayton (26.7, 72 GP) is the one rate here to discount** — demoted to backup C, so
the 26.7 is a stale role. That is a `WINS`-layer rate correction for a **verifiably changed
role**, which `team-eval` permits; it is not an injury adjustment.

## Tier 2 — 1-for-1 rate upgrades, sending from *Prime sell*

**No send list here, by design.** Who we shop is `my-team-situation`'s ***Prime sell*** cell on
`teams/my-team/my-team.md`'s post-execution medians — and that is a **re-run, not a lookup**: the file
publishes the two post medians but no per-player post `Δw`, and tells you not to read them off
the pre table. Re-fetch the roster, re-run `sim.py players`, recut the cell, *then* find the seat
that prices him highest (`trades` → *Shopping one of ours*).

**Get, in order of fit.** Size every one with `sim.py players` / `sim.swap` before offering; a
remembered win figure is what `trades` step 6 exists to prevent.

| Target | Owner | FPts | GP | Age | **TVAL** | `GET` | Note |
|---|---|---:|---:|---:|---:|---|---|
| **Kevin Durant** | King Christopher | 39.8 | **78** | 37 | **4398** | medium — cliff already here, but stars still price on last year's numbers | best profile in the league for us — iron man, maximally age-discounted, owner is falling off a cliff |
| **Julius Randle** | Yao Ming | 37.2 | **79** | 31 | **3942** | low-medium — aging mid-tier pile with no long-term fit around Jokić | same shape, cheaper |
| **Karl-Anthony Towns** | Jesus Christ | 41.4 | 75 | 30 | **4680** | high — contending now (14-5), no pipeline means they need him more, not less, until the cliff actually arrives | owner has *no* pipeline and needs youth — natural fit for a future ask, not a present sale |
| **Jamal Murray** | Jesus Christ | 42.4 | 75 | 29 | **4311** | high — same read as KAT, contending core piece | same |
| James Harden | Pascals | 41.8 | 70 | 36 | **4037** | high — defending champs, "hardest team to pry anything loose from" | great profile; champions are the hardest counterparty |
| Bam Adebayo | Gutes | 39.8 | 73 | 29 | **4330** | medium — usage drops with Giannis in Miami, and the roster's aging/injury-battered shape argues for some retool pressure | usage drops with Giannis in Miami |
| Pascal Siakam | Pascals | 38.5 | 62 | 32 | **3722** | high — same champs-hold-everything read | GP is borderline |

⚠️ Durant and Harden are both `LATE` `✗` on age alone. `team-eval` caps that at a **tiebreak** —
never a discount, never a column, no aging term in the verdict.

⚠️ **King Christopher's *forward* `REPL` sits 0.8 above ours** — 16.9 against our 16.1, both
padded to 38 (`teams/my-team/my-team.md` §`WINS`). His is a forward glut, ours a guard glut, so his
forwards are worth **more** to us than to him: Durant is **+2.04 `W ours`** against **+1.97
`W theirs`**. His **centre** bar is 4.0 *below* ours, where the same reasoning reverses. Per
group and per roster — run `sim.replacement` on his padded file before pricing either side.

**`GET` low + `TVAL` high, applied:** every name here clears a real `TVAL` (3722-4680), but
only **Durant and Randle** pair that with a `GET` that isn't pinned to "won't sell" — both
sit on rosters actively falling or retooling (King Christopher's cliff, Yao Ming's aging pile
around Jokić). **KAT, Murray, Harden and Siakam are `GET`-high** despite comparable or better
`TVAL` — Jesus Christ is contending now and Pascals just won the title, so per `trades`
("`GET` high + `TVAL` high means pay up or walk — not a mispricing") those three-to-four names
are correctly priced high, not mispriced. This **reverses** the old file's flat "in order of
fit" read, which put KAT/Murray at the top on `Δw theirs` proximity alone with no read on
whether either owner would actually sell.

## Tier 3 — Jokić, and only at the right shape

Nikola Jokić (65.2 FPts/G, 65 GP, 31, Yao Ming) is the **only player in the league over 60
FPts/G**; 8 cleared 45 at 30+ GP and 3 cleared 50 (`lineup-math/README.md` §*Is the incoming
rate even purchasable?*). **Read the price ladder off that file's §*Consolidation is not the
lever*, every time.** What holds without a number:

- **Cap at 3-for-1, genuine dregs only** (`team-eval`). Never 4 or 5 bodies, for anyone.
- Read him against the **65-GP centre** break-even row, not the 68-GP forward row — the README
  says reading the wrong row inverts the sign of his 5-for-1.
- Yao Ming is the right counterparty in principle — projected 8th-9th and falling, no young 40+
  tail, and Jokić's health is their entire floor (`team-projections.md`).

**`TVAL`, one player added straight to our roster (not the N-for-1 shape):** `Δw ours`
**+3.47** (63.2 rate, 63 GP proj, swapped for Sion James on our padded-38 basis) →
**`TVAL` = 8611** — comfortably the highest single figure in this file, which is the whole
case for treating him as worth pursuing at all despite the price. **`GET` is near-zero** —
`team-projections.md` calls his health "their entire floor," so the read is unchanged from
the old file: not gettable at a normal shape, only at the rich 3-for-1 the ladder above
prices, and even then only because nothing else in Yao Ming's pipeline gives them a reason to
hold at all costs the way Pascals holds its champions.

## Price with care — the GP column is one season, not a projection

⚠️ **These are not "do not buy" names.** Pricing them off their worst year while carrying our own
injured at regressed GP (`sim.PROJECTED_RATE` / `project_gp` — Edey 11→43, Butler 38→53, Kyrie
0→57) refuses exactly the players the boards have already marked down, which is where the buying
is. Regress both sides identically — `our_roster` does it structurally on whichever file is
loaded — and remember the boards **already charged** for the injuries (`team-eval` → *Durability*).

| Name | Owner | rate | '25-26 GP | **TVAL** | `GET` | Read |
|---|---|---:|---:|---:|---|---|
| Giannis Antetokounmpo | Mongol | 48.9 | 36 | **4783** (65 GP proj, well above his 36 actual — the whole point of this section) | medium — "the single most mispriced asset in the league," roster has a real path up elsewhere (Knueppel/Filipowski/Rollins blockers removed), so Giannis isn't obviously the piece Mongol builds around | The best single asset available to us at a regressed GP, and the market's top-3 price is not obviously wrong. What is true is only that **nobody clears a 4-or-5-body price**, Jokić included. Negotiate the shape, don't refuse the player. |
| Domantas Sabonis | Pascals | 37.2 | 19 | **2404** (46 GP proj, regressed off the meniscus) | high — defending champs, same hold-everything read as the rest of their Tier 2 names | 19 GP is a meniscus and `team-projections.md` has him returning. The most under-priced name here relative to his 19-GP `FPts` sort. |
| Lauri Markkanen | Pascals | 40.5 | 42 | **3563** (54 GP proj) | high — same Pascals read | Regress and re-price. A declared block is neither a discount nor a warning. |
| Donte DiVincenzo | King Christopher | 26.3 | **82** | **1146** (67 GP proj, regressed for the Achilles) | medium — cliff-team seller, but a fresh Achilles tear plus their still-high anchoring makes this a slower sell than Bridges/Marshall | Torn Achilles — a `GP` projection input the boards already charge for, **not** a hard pass. Project the GP, then price him. |
| Stephen Curry | King Christopher | 39.4 | 43 | **2966** (55 GP proj) | low-medium on `GET`, but this is the one name on the list where `LATE` argues against initiating regardless | **The one real pass, and on age not on GP** — 38, so the low GP is a trend rather than one bad year. A `LATE` call, and `LATE` is a tiebreak: it argues for not *initiating*, not for refusing at any price. |

Do **not** cite `team-projections.md` as independent confirmation on any of these — it reads the
same `GP` column, so agreeing with it is one number counted twice.

## Do not buy

- Anyone's **future firsts** except SGA-the-Great's, King Christopher's and Han's
  (`team-projections.md`). Ours land ~1.10 every year — spend them here.
- Anyone at a **4-for-1 or worse.** The binding constraint, and it does not depend on who the
  player is.
