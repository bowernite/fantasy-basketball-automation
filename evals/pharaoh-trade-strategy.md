# Pharaoh Mattankhamun-Ra (Matthew) — live negotiation, strategy + memory

**Derived 2026-07-30.** Per-owner memory per `trades` §*Sequencing with one owner*. Valuations
are `pharaoh-mattankhamun-ra.md` (same date) and `bathroom-club.md`; **re-run, never quote**
once either moves.

| | |
|---|---|
| Basis | **post-execution** of trade 483809 (Bagley out, Mark Williams in) — still pending at derivation, executes 2026-07-31T00:00:00Z |
| Ours, padded | 38 bodies · `REPL` guard **18.3** · forward **15.7** · centre **18.6** — reproduces `bathroom-club.md` §*Post-execution* exactly |
| Theirs, padded | 38 bodies · `REPL` guard **11.9** · forward **12.5** · centre **11.8** · `K` 777 |
| Verdict params | `κ` **940** (sim layer, quartiles 630–1312) · `δ` 0.875 · H 3 · `Σδ` 2.641 · `M` **0.9** |
| Body counts | `maxRosterSize` **28**. Us **28 (full)** · him **26 (two open)** |
| Wire | Nothing on `FetchTradeBlock`; no Pharaoh rows on page 1 of `FetchLeagueTransactions`. Inference only — his own words are the better source |

`M = 0.9` is slightly conservative: `team-projections.md` has us **2nd / 2nd / 4th** across the
window. His **5th / 3rd / 1st** matches his stated MO word for word, so take the MO at face value.

**Sourced vs modelled.** Board ranks, BASE, `FPts/G`, `GP`, `AGE`, `ELIG`, body counts, roster
limits are **sourced**. Every `+wins`, `Δw`, `GP proj`, `REPL`, `κ` and the verdict column are
**modelled**. Never present the two as bracketing a range.

## The asymmetry the whole trade lives in

On **his** roster Barnes, Amen and Giddey are indistinguishable — formula layer on his `REPL`,
and the gaps are inside the formula's own 22–33% error:

| on his roster | rate | GP proj | group | `W theirs` |
|---|---:|---:|---|---:|
| Scottie Barnes | 40.5 | 68 | forward | **2.45** |
| Amen Thompson | 39.3 | 68 | forward | **2.35** |
| Josh Giddey | 42.2 | 59 | guard | **2.30** |

So "I probably like Barnes a little more than Amen" is **correct from his seat**, and cheap for
him to act on. On **ours** they are not close, because our guard bar is 2.6 points above our
forward bar (18.3 vs 15.7, a 12-guard glut) and `GP` is the dominant input:

| deal (sim, 3 × 200 trials, post basis) | ΔPF | **+wins** | sd | **ΔBASE** | verdict |
|---|---:|---:|---:|---:|---:|
| **Amen → Barnes** — the shape he floated | +19 | **+0.03** | 0.003 | +1336 | +1408 |
| **Giddey → Barnes** | +297 | **+0.50** | 0.019 | +2559 | +3671 |
| Giddey → Jalen Johnson | +598 | +1.00 | 0.014 | +2854 | +5083 |
| Giddey + Chaney → Barnes + K. George | +746 | **+1.25** | 0.025 | +4218 | +7009 |
| Amen + Chaney → Barnes + Ausar Thompson | +525 | +0.88 | 0.025 | +3043 | +5008 |
| Amen + Chaney → Barnes + K. George | +503 | +0.84 | 0.034 | +2995 | +4878 |
| Amen + Chaney → Jalen Johnson + Queta | +590 | +0.99 | 0.027 | +2178 | +4383 |

**Giddey → Barnes dominates Amen → Barnes on both layers** — +0.47 wins and +1223 BASE better,
for the *same incoming player*. Amen and Barnes are both forwards at 68 projected GP separated
by 1.2 rate points; that trade is lateral by construction.

## Why Amen → Barnes is a walk-away even though it clears the inequality

`ΔBASE + κ Σδ M Δw = 1336 + 940 × 2.641 × 0.9 × 0.03 = +1408`, and `κ*` is **negative**, so no
point in the 630–1312 band flips the sign. It clears.

It is still a walk-away, on two other `trades` clauses:

1. **"Net is a fraction of a win *and* the price touches a real asset."** +0.03 wins, and Amen is
   ***Core*** — BASE 5360 against the post median 1228.5, `Δw` **+1.97** against +0.434.
2. **The counterfactual.** Not "nothing" — it is Giddey → Barnes, strictly better on both layers.

And he has said he wants a **sweetener on top of Amen**. That is us paying a real asset for a
lateral wins move. **Never Amen for Barnes straight, and never Amen + anything for Barnes alone.**

## Ladder

Smallest good swap first, separate 1-for-1s, each separately refusable (`trades`).

1. **Open — two asks, expect one:** Giddey for Jalen Johnson; if genuinely out, Giddey for Barnes
   straight. "Pretty much untouchable" is not untouchable, and the ask is free.
2. **Anchor version:** Giddey + Chaney Johnson for Barnes + Kyshawn George (+1.25 w / +4218). A
   1-for-2 sending our 4th-best asset for his 3rd-best plus a mid-tier is a legitimate *shape* —
   lopsided in value, not in shape, which is the rule.
3. **Target:** Giddey → Barnes. +0.50 w / +2559 BASE.
4. **Closing concession, only if Giddey is refused outright:** Amen for Barnes **plus a second
   real piece** — Ausar Thompson (+0.88) or Kyshawn George (+0.84). Both fine.
5. **Walk:** Amen for Barnes straight, or Amen + anything for Barnes alone.

We already opened with our better piece, which `trades` says not to do. The recovery is that
**he supplied the objection himself** — no shooting progress, and usage possibly inflated by the
VanVleet injury. Agreeing with him is how we reprice Amen without arguing method.

### In his frame — age and `FPts/G`, both on the roster page he reads

- Giddey **23.8** / **42.2** · Amen **23.5** / 39.3 · Barnes **25.0** / 40.5.
- Giddey is the highest rate of the three and 1.2 years younger than Barnes. Do **not** claim he
  is younger than Amen — he is fractionally older.
- His two stated doubts about Amen are shooting and VanVleet-dependent usage. Giddey answers both
  and is not on Houston.
- Story to give a fringe-now/contending-later owner: *the piece for when the window opens.*

## The separate small swap — Queta, and it is not a package

Queta is the most BASE-efficient production available to us anywhere: **28.0 FPts/G at BASE 547**,
crowd rank **707**. `trade-targets.md` Tier 1 already flagged him as the standout.

| | +wins | ΔBASE | note |
|---|---:|---:|---|
| Matković → Queta | **+0.61** | **+426** | most efficient for us; he will never take a 25-yo 14.2-rate body |
| 3.09 + cut Chaney → Queta | +0.60 | +190 | **the realistic version** |
| 2.09 + cut Chaney → Queta | +0.60 | −98 | if 3.09 is refused |
| Maluach → Queta | +0.72 | −12 | the version *he* wants — see below, do not offer it yet |

**Pitch:** he told us he is peaking in a couple more years. Queta is **27 — his oldest player**,
and `team-projections.md` independently says he is the *only* decline risk anywhere in that
roster's window. Same public roster page, his own stated frame.

⚠️ **A this-season buy, not a dynasty edge.** The September auction supplies part of the same gain
for free (+2.14 wins to fill to 38) and breadth stops differentiating once every team fills from
the same pool (`lineup-math/README.md` §*Sept '26 expansion*). Buy it for slot-nights, not as a moat.

⚠️ Queta's `Δw theirs` is **+1.15** — his 4th-best by wins. Board-cheap but **lineup-load-bearing**,
so he is not gettable at his board price. Name that tension before anchoring low.

## Maluach — two bidders, so he is not a Pharaoh sweetener

SGA-the-Great (KIMJONIL) has expressed interest. What Maluach can buy, on our roster:

| | +wins | ΔBASE |
|---|---:|---:|
| **→ Kel'el Ware (SGA)** | **+0.73** | **+1567** |
| → Queta (Pharaoh) | +0.72 | −12 |
| → Jeremiah Fears (SGA) | +0.56 | +834 |
| → Maxime Raynaud (SGA) | +0.51 | +460 |
| → Peyton Watson (SGA) | +0.55 | +427 |
| → Day'Ron Sharpe (SGA) | +0.41 | +223 |

Ware and Queta are a **tie in wins** — 0.01 apart, inside the ~0.1 band — but Ware is **+1579
BASE**. So Maluach's best use is the SGA channel, and Queta should be bought with a **pick**,
which costs ~350–650 BASE and **zero year-1 wins** — the cheapest currency we have.

**Therefore: do not attach Maluach to any Pharaoh deal until the SGA channel resolves, and do not
tell Pharaoh he is available.** `trade-targets.md`'s "never ship him as a sweetener" holds; two
bidders is the reason to run an actual process.

⚠️ **SGA-the-Great is un-eval'd.** BASE above is off the committed boards and the wins are simmed
on *our* roster, but there is no `sim.replacement` run on their padded file, so **what Ware costs
from their seat is unknown.** They are a five-centre roster buying a sixth on pedigree, which is
why the ask is worth making. That eval is the next job if you want to run that channel.

## The programme, simulated jointly

Wins do not add across legs, so these are one roster state, not a sum:

| | +wins | ΔBASE |
|---|---:|---:|
| Giddey→Barnes + (2.09/Chaney)→Queta | **+1.03** | +2461 |
| … + Maluach→Raynaud (SGA leg) | **+1.41** | +2921 |
| … with K. George instead of Queta | **+1.68** | +4033 |

Well inside the **~+4 wins** ceiling a whole *programme* can reach (`lineup-math/README.md`
§*PF → wins*). Nothing here is transformational and it should not be pitched as such.

## Legality and sequencing

- We are **28/28**. A 1-for-1 needs no release. Any 2-for-1 in our favour costs us **one drop** —
  Chaney Johnson (BASE 0, `Δw` −0.09). Not free: he still pays as a light-night body.
- He is **26/28**, so he can absorb two net bodies, or take Chaney *in* the trade and need no
  release either side.
- **Separate 1-for-1s, never one package.** Barnes first; raise Queta as its own conversation
  later. Don't stack unanswered asks.
- **Withhold:** board ranks, that we blend, that we simulate, any win figure, our ordering of his
  assets, and **why** we want Queta.
- **Reveal freely:** `seasonAverage`, ages, standings, rosters — shared and checkable.

## Caveats that cut against this file

- **Giddey → Barnes sells the board-divergent asset and buys the consensus.** Giddey is
  24/28 expert against **44 crowd**; Barnes is 12/10/12 on all three. If the experts are right
  about Giddey we are selling low. The **+0.50 wins is independent of the boards** (rate, GP,
  slot group only) — the BASE half is buying consensus, not an edge.
- **`LATE` favours Barnes** — ✓✓ none under 60 in 5, against Giddey's ✓ 2 of 5. A contender
  tiebreak that happens to run with the conclusion, so it is worth nothing as evidence.
- **Decomposition of the +0.50**, each leg holding everything else at Giddey's (synthetics all on
  one schedule, so the handicap cancels): **position only +0.33 · GP only +0.43 · rate only
  +0.01**. They overlap rather than add — the slot-fill curve is concave and games and
  forward-eligibility partly substitute. So it is a **positional trade with a GP kicker**, and the
  rate is worth nothing.
- **GP sensitivity, and it never turns negative.** Barnes held at Giddey's 59 GP → **+0.20**; at
  63 (what their 5-season means imply) → **+0.33**; at 68 (adopted) → +0.50; at 54 → +0.03, and
  that is below his 5-season minimum of 60. **Read +0.33 as the honest centre**, not +0.50.
- **This is the worst pair in the league for a one-season `GP` read.** Giddey 54/76/80/70/54
  (mean 66.8) against Barnes 74/77/60/65/80 (mean 71.2) — a `gp1` gap of **26 games** against a
  `gp5` gap of **4.4**, and we compared them at the widest point in both histories. `project_gp`
  regresses it to 9.6 and puts Giddey at the pool mean, so the model calls him **average**, not
  fragile. `lineup-math` adopted `gp1` because `gp5` was *not better* (P 0.14), not because it was
  better — that is a weaker warrant than usual here. **No fragility discount either way**
  (`team-eval` §*Durability*); `LATE` is not in the win figure at all.
- **The +0.33 positional gain is a fact about our roster, not about basketball** — 12 pure PG/SG
  against ~5 guard-eligible slots. `lineup-math` §*Positional premium* says it disappears as the
  shape changes. Shipping Giddey leaves 11, so it persists with diminishing returns, and the Sept
  expansion to 38 can move it.
- Giddey is ***Core*** too (BASE 4137, `Δw` +1.44). Shipping him is only licensed because both
  terms of the verdict are positive — not because the cell is crowded.

## Memory — log every exchange here

**2026-07-30, opened by us.** Offered Amen for Jalen Johnson. He: *Jalen "pretty much
untouchable", Scottie available, "straight up I probably like Barnes a little more than Amen",
not going all in yet, playing for the playoffs, peaking in a couple more years.* Reasons given
against Amen: no shooting progress; doubts the usage holds; thinks Houston would have looked
different without the VanVleet injury. Reason for Barnes: "in the spot to be the main guy on
Toronto forever."

- **Refused:** Jalen Johnson (soft — "pretty much").
- **Offered:** Barnes.
- **Implied ask:** a sweetener on top of Amen for Barnes. Not paid.
- **Untouchable, ours, symmetrically:** Cade. Amen only at Barnes + a second real piece.
