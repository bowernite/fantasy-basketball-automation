# Trade targets

**Derived 2026-07-30.** A **shortlist of names** and nothing else — every rule this file used to
state is owned elsewhere, and names are the part that goes stale. Re-derive before acting.

Rules live in: `trades` (buy/sell profile, negotiation) · `team-eval` (body count, consolidation
cap, durability, the non-factor list) · `my-team-situation` (which of ours are *Core* vs
surplus — **that cell is the gate; no list here overrides it, in either direction**) ·
`evals/lineup-math/README.md` (every win figure, ladder and break-even — **re-run, never
quote**) · `evals/team-projections.md` (counterparty situation, whose future picks are worth
anything) · `evals/bathroom-club.md` (our own BASE and `Δw`).

⚠️ **Provenance:** every **owner** below was re-verified against `FetchLeagueRosters` on
**2026-07-30**. The **`FPts`/`GP`/`Age` columns were not** — they are the 2026-07-29
`FetchRoster` pull carried forward. Re-pull before quoting one, and never feed the `GP` column
into `WINS` (it is last-season actual; `sim.py gp` projects).

⚠️ **Pending trade 483809 executes 2026-07-31T00:00:00Z** (`FetchTrades`): our 1.09 out, Mark
Williams in, **Marvin Bagley released** — so Bagley is not a send body below, and every bucket
call moves with the post-execution medians (`bathroom-club.md` §*Post-execution*).

## Tier 1 — bottom-of-roster upgrades, and do these first

The cheapest wins measured, and a fraction of the dynasty cost of a top-end 1-for-1 — **read the
multiple off `lineup-math/README.md` §*Consolidation is not the lever*, never from here.** But it
buys **this season's slot-nights**, not a lasting edge: the September auction supplies part of
the same gain for nothing, and breadth stops differentiating once every team fills from the same
pool (`trades` → *Deal shape*).

**Send from** `my-team-situation`'s *Upgrade, don't shop* cell — on both median sets that is
Khaman Maluach · DaRon Holmes · Khris Middleton · Karlo Matković · Sion James · Keon Ellis ·
Adem Bona · Chaney Johnson (BASE and `Δw` per row: `bathroom-club.md`). The move is a **swap,
not a sale.** ⚠️ They are not all worthless: only **Chaney Johnson** is BASE 0, and **Maluach at
559 is the most valuable piece in the group by 2×** — a 19-year-old starting centre the expert
board has at 154. Never ship him as a sweetener.

**Get:** 22-29 FPts/G at **≥72 GP**, cheap.

| Target | Owner | FPts | GP | Age |
|---|---|---:|---:|---:|
| Mikal Bridges | King Christopher | 28.8 | **82** | 29 |
| Neemias Queta | Pharaoh | 28.0 | 76 | 27 |
| Collin Gillespie | Jesus Christ | 27.7 | 80 | 27 |
| Naji Marshall | King Christopher | 26.6 | 74 | 28 |
| Toumani Camara | Matthew the Apostle | 26.4 | **82** | 26 |
| Wendell Carter | Yao Ming | 26.3 | 78 | 27 |
| Cam Spencer | Yao Ming | 24.2 | 72 | 26 |
| Precious Achiuwa | Pascals | 24.0 | 73 | 26 |
| Quentin Grimes | Gutes | 23.6 | 75 | 26 |
| Keldon Johnson | Gutes | 23.0 | **82** | 26 |
| Sandro Mamukelashvili | Pascals | 22.9 | 80 | 27 |
| Royce O'Neale | Yao Ming | 22.7 | 78 | 33 |

Queta is the standout: 28.0 FPts/G against a Hashtag crowd rank of **707**
(`pharaoh-mattankhamun-ra.md`) — production the crowd prices at nothing. His `Δw theirs` is
**+1.15**, so his owner is not giving him away at his board price (`trades` → *Flag board-cheap
but lineup-load-bearing*).

⚠️ **Deandre Ayton (26.7, 72 GP) is the one rate here to discount** — demoted to backup C, so
the 26.7 is a stale role. That is a `WINS`-layer rate correction for a **verifiably changed
role**, which `team-eval` permits; it is not an injury adjustment.

## Tier 2 — 1-for-1 rate upgrades, sending from *Prime sell*

**No send list here, by design.** Who we shop is `my-team-situation`'s ***Prime sell*** cell on
`bathroom-club.md`'s post-execution medians — and that is a **re-run, not a lookup**: the file
publishes the two post medians but no per-player post `Δw`, and tells you not to read them off
the pre table. Re-fetch the roster, re-run `sim.py players`, recut the cell, *then* find the seat
that prices him highest (`trades` → *Shopping one of ours*).

**Get, in order of fit.** Size every one with `sim.py players` / `sim.swap` before offering; a
remembered win figure is what `trades` step 6 exists to prevent.

| Target | Owner | FPts | GP | Age | Note |
|---|---|---:|---:|---:|---|
| **Kevin Durant** | King Christopher | 39.8 | **78** | 37 | best profile in the league for us — iron man, maximally age-discounted, owner is falling off a cliff |
| **Julius Randle** | Yao Ming | 37.2 | **79** | 31 | same shape, cheaper |
| **Karl-Anthony Towns** | Jesus Christ | 41.4 | 75 | 30 | owner has *no* pipeline and needs youth — natural fit |
| **Jamal Murray** | Jesus Christ | 42.4 | 75 | 29 | same |
| James Harden | Pascals | 41.8 | 70 | 36 | great profile; champions are the hardest counterparty |
| Bam Adebayo | Gutes | 39.8 | 73 | 29 | usage drops with Giannis in Miami |
| Pascal Siakam | Pascals | 38.5 | 62 | 32 | GP is borderline |

⚠️ Durant and Harden are both `LATE` `✗` on age alone. `team-eval` caps that at a **tiebreak** —
never a discount, never a column, no aging term in the verdict.

⚠️ **King Christopher's *forward* `REPL` sits 0.8 above ours** — 16.9 against our 16.1, both
padded to 38 (`bathroom-club.md` §`WINS`). His is a forward glut, ours a guard glut, so his
forwards are worth **more** to us than to him: Durant is **+2.04 `W ours`** against **+1.97
`W theirs`**. His **centre** bar is 4.0 *below* ours, where the same reasoning reverses. Per
group and per roster — run `sim.replacement` on his padded file before pricing either side.

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

## Price with care — the GP column is one season, not a projection

⚠️ **These are not "do not buy" names.** Pricing them off their worst year while carrying our own
injured at regressed GP (`sim.PROJECTED_RATE` / `project_gp` — Edey 11→43, Butler 38→53, Kyrie
0→57) refuses exactly the players the boards have already marked down, which is where the buying
is. Regress both sides identically — `our_roster` does it structurally on whichever file is
loaded — and remember the boards **already charged** for the injuries (`team-eval` → *Durability*).

| Name | Owner | rate | '25-26 GP | Read |
|---|---|---:|---:|---|
| Giannis Antetokounmpo | Mongol | 48.9 | 36 | The best single asset available to us at a regressed GP, and the market's top-3 price is not obviously wrong. What is true is only that **nobody clears a 4-or-5-body price**, Jokić included. Negotiate the shape, don't refuse the player. |
| Domantas Sabonis | Pascals | 37.2 | 19 | 19 GP is a meniscus and `team-projections.md` has him returning. The most under-priced name here. |
| Lauri Markkanen | Pascals | 40.5 | 42 | Regress and re-price. A declared block is neither a discount nor a warning. |
| Donte DiVincenzo | King Christopher | 26.3 | **82** | Torn Achilles — a `GP` projection input the boards already charge for, **not** a hard pass. Project the GP, then price him. |
| Stephen Curry | King Christopher | 39.4 | 43 | **The one real pass, and on age not on GP** — 38, so the low GP is a trend rather than one bad year. A `LATE` call, and `LATE` is a tiebreak: it argues for not *initiating*, not for refusing at any price. |

Do **not** cite `team-projections.md` as independent confirmation on any of these — it reads the
same `GP` column, so agreeing with it is one number counted twice.

## Do not buy

- Anyone's **future firsts** except SGA-the-Great's, King Christopher's and Han's
  (`team-projections.md`). Ours land ~1.10 every year — spend them here.
- Anyone at a **4-for-1 or worse.** The binding constraint, and it does not depend on who the
  player is.
