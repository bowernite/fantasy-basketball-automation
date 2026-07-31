# SGA-the-Great (Jon, `KIMJONIL`, 161015) — live negotiation, strategy + memory

**Derived 2026-07-30.** Per-owner memory per `trades` §*Sequencing with one owner*. Valuations
are `jon.md` (same date) and `../my-team/my-team.md`; **re-run, never quote** once either
moves.

**Target selection here is `GET` × `TVAL`** (`trades` step 4 / §*Pricing their side* 4), off the
current `jon.md`. **`Δw theirs` selects nothing** — it prices only what they give up
inside a concrete deal (`team-eval` §`WINS`). The negotiation record below is unchanged.

| | |
|---|---|
| Basis | **post-execution** of trade 483809 — verified on the wire today: Mark Williams on us, Bagley a free agent, The Don down to 27 without him |
| Ours, padded 38 | `REPL` guard **18.31** (16 pure / 5 slots) · forward **15.66** (8 / 5) · centre **18.59** (9 / 3) |
| Theirs, padded 38 | `REPL` guard **12.04** (14 / 5) · forward **11.30** (13 / 5) · centre **14.24** (8 / 3) |
| Verdict params | `κ` **940** (sim layer, quartiles 630–1312) · `δ` 0.875 · H 3 · `Σδ` 2.641 · `M` **1.0** — so **2,482 BASE per win**, band 1,664–3,465 |
| Body counts | `maxRosterSize` **28**. Us **28 (full)** · them **27 (one open)** |
| Wire, 2026-07-30 | **0 pending trades league-wide.** `FetchTradeBlock` carries **nothing of theirs** — only King Christopher (Fox) and Pascals (six names). Their interest in Maluach is from the text thread, not the wire |

⚠️ **`M` moved 0.9 → 1.0** to match the redone `jon.md` and `../my-team/my-team.md`, which
take `M` = 1.0 across all three seasons off `team-projections.md`'s 2nd/2nd/4th. **Every verdict
below is ~11% higher than the previous version's for that reason alone. No sign flips**, and no
ordering moved.

Every win figure below is **sim-measured** on 3 × 200 trials with common random numbers, on the
post-483809 basis. `sd` is across seed blocks — **treat gaps under ~0.1 wins as ties**.
Verdict = `ΔBASE + 2,482 × +wins`.

**Sourced vs modelled.** Board ranks, BASE, `FPts/G`, `GP`, `AGE`, `ELIG`, body counts and the
wire facts are **sourced**. Every `+wins`, `ΔBASE`, `REPL`, `κ` and verdict is **modelled**.
Never present the two as bracketing a range.

## Why Maluach is the right thing to sell, and 483809 made it more so

He is a **pure centre, projected 16.0, against our centre `REPL` of 18.59** — sub-replacement,
on the group where we are **9 pure bodies deep for 3 slots**. Acquiring Mark Williams (another
pure C) pushed centre `R` from 17.8 to **18.59**, so the trade you just made **lowered** Maluach's
value to us. He is BASE **559** and `Δw` **−0.14**: `my-team-situation`'s *Upgrade, don't shop*
cell, where he is the most valuable piece by 2×.

**`TVAL` sharpens this, it does not change it.** `../my-team/my-team.md` prices him at `TVAL`
**−348** against BASE **559** — the widest inversion on our roster. BASE says the market will
pay for him; `TVAL` says we get nothing back from rostering him. That gap *is* the trade.

⚠️ **He is not free and must not be shipped as a sweetener.** 559 BASE and a 19-year-old
starting centre. The move is a **swap for production**, not a sale.

**The edge is that his value to them is pedigree and ours is production.** `trades` §*What other
owners price on*: sell **young + modest current rate; anything whose value is name or pedigree.**
Maluach is that profile exactly — 19.9, a 2025 lottery pick, starting in Phoenix, a good summer
league, and a **rookie-year rate of 8.2 FPts/G**. A rebuilder pricing on age and pedigree can
rate him several times what the boards do. That gap is the whole deal.

⚠️ **They are crowded at centre too** — 8 pure for 3 slots — and asked for a ninth. They are
collecting young talent, not solving a lineup. Do not expect slot logic to move them.

## Their seat — a rebuilder, so their verdict is close to pure `ΔBASE`

7-12, 10th by record, 11th of 12 by PF; `team-projections.md` projects **12th** in '26-27. `M` ≈ 0
over our window, so **wins cost them almost nothing they care about** and BASE is what they
negotiate on.

## Their side, priced twice — `GET` and `TVAL`

`trades` §*Pricing their side* 4: every asset gets **`TVAL`** (worth to us) and **`GET`** (what
they will take), and we **buy where `GET` is low and `TVAL` is high**. Both columns are
`jon.md` §*Shortlist* and §*What this means for us* — quoted, not recomputed. `GET` is
judgment: coarse, never summed, never in a verdict.

Sorted on BASE, the counterparty sort. `costs them` is this file's own measurement of what each
piece costs them in wins — real, largely irrelevant to a rebuilder, and it **selects nothing**.
It is **not** the `Δw theirs` column in `jon.md`; that one runs on a different
counterfactual and the two must not be mixed in one argument.

| their asset | BASE | `TVAL` | gap | `GET` | costs them | read |
|---|---:|---:|---:|---|---:|---|
| Shai Gilgeous-Alexander | **9352** | **5844** | −3508 | high, **but available** | — | pay-up-or-walk; `κ*` **1504** > Q3 |
| Alperen Şengün | **6188** | **4171** | −2017 | high, **not available** | — | don't chase; `κ*` 1395 > Q3 |
| Kel'el Ware | **2126** | **938** | −1188 | high | −0.87 | **the trap** — `κ*` 2130, a pass at market |
| Ace Bailey | **1789** | — | — | high, young riser | −0.81 | refused at any price, per the eval |
| Jeremiah Fears | **1393** | — | — | high, young riser | −0.84 | as above |
| Cason Wallace | **1107** | — | — | mid | — | guard; lands in our glut |
| Maxime Raynaud | **1019** | — | — | high, young riser | −0.60 | as above |
| Peyton Watson | **986** | — | — | high, young riser | — | as above |
| Day'Ron Sharpe | **782** | **12** | −770 | low–mid | −0.32 | body only |
| Jaylen Wells | **683** | **541** | −142 | **mid** | −0.39 | **undecided** — flips at `κ` **1186**, inside band |
| Danny Wolf | **483** | — | — | high, young riser | −0.09 | refused |
| Justin Champagnie | **410** | **323** | −87 | **low** | — | **undecided** — flips at `κ` **1194**, inside band |
| Tristan da Silva | **322** | **45** | −277 | **low** | −0.29 | body, not an upgrade |

`—` in `TVAL` means **not computed, not zero**: `jon.md`'s shortlist excludes their
young risers on `GET` (a rebuilder refuses them at any price) and their sub-700 pure guards on
fit (our glut). `—` in `costs them` means this file never measured that row.

**Every priced name on their roster has `TVAL` < BASE. Nothing here is underpriced at market** —
and that is the single most important thing this file has to reconcile.

⚠️ **It does not mean "don't trade with them."** `TVAL` < BASE is a *market-price* test: it says
paying 9,352 of BASE for SGA, or 2,126 for Ware, is a bad use of that BASE. **This channel is not
a market purchase.** We are paying **559 of BASE and a `TVAL` of −348**, so every return in the
ladder clears by a wide margin. The two statements are consistent: *buy nothing here at list,
and sell Maluach into it anyway.*

⚠️ **The `GET` column runs almost exactly opposite to the ladder's verdict column**, because the
verdict is dominated by ΔBASE and their BASE sits in the players a rebuilder refuses to move. So
**the ladder below is a value ordering, not a likelihood ordering** — read the two columns
together and expect to land near the bottom of it.

## The ladder — every return for Maluach, measured

Verdicts recomputed at **`M` = 1.0** (2,482/win). `GET` is `jon.md`'s, and it is the
column that says which of these we can actually get.

| Maluach → | +wins | sd | ΔBASE | **verdict** | `GET` |
|---|---:|---:|---:|---:|---|
| **Kel'el Ware** | +0.59 | 0.027 | **+1567** | **+3031** | high — *the trap* |
| **Ace Bailey** | **+0.69** | 0.030 | +1230 | **+2943** | high — young riser |
| Jeremiah Fears | +0.52 | 0.029 | +834 | +2125 | high — young riser |
| Cason Wallace | +0.44 | 0.035 | +548 | +1640 | mid — guard |
| Peyton Watson | +0.46 | 0.023 | +427 | +1569 | high — young riser |
| Maxime Raynaud | +0.45 | 0.032 | +460 | +1557 | high — young riser |
| **Jaylen Wells** | +0.43 | 0.041 | +124 | **+1191** | **mid** |
| Day'Ron Sharpe | +0.21 | 0.040 | +223 | +744 | low–mid |
| **Justin Champagnie** | +0.34 | 0.043 | −149 | **+702** | **low** |
| Tristan da Silva | +0.23 | 0.038 | −237 | +334 | **low** |
| Danny Wolf | +0.14 | 0.023 | −76 | +271 | high — young riser |
| Josh Minott | +0.03 | 0.012 | −225 | **−151** | low |

**Champagnie is new** — measured today on the same basis (+0.343 ± 0.043, 3 × 200 trials, CRN),
and the run reproduces every pre-existing row above to the printed digit, which is the check that
he is comparable. He was absent from the old ladder because the old targeting sorted on
`Δw theirs`, which buried him. **He is the only `GET`-low forward on the board with a real
`TVAL`** (323 vs BASE 410, `κ*` 1194 — undecided on this method, per the eval).

**Ware and Bailey are a tie, not a ranking** — 126 BASE apart, and the wins `sd` alone is worth
~74 BASE at 2,482. Bailey is **337 BASE cheaper and +0.10 wins better**; Ware carries more market
value. Bailey out-wins him despite a **4.3-point lower rate** purely because he is a forward:
that is our thin group (8 pure / 5 slots) against centre's crowd (9 / 3).

⚠️ **The top of this ladder just got much less likely, and that is the real methodology change.**
`jon.md` reads Ware as `GET` **high** + `TVAL` low — "the trap", and *he* knows what he
has — and puts Bailey, Fears, Raynaud, Watson and Wolf on the young-riser list a rebuilder
**refuses at any price**. Their verdicts are still correct; their availability is the problem.
Ask anyway (a 19-year-old lottery centre is the one currency a rebuilder trades a young riser
for) but **plan to land at Wells / Champagnie / a late second**, which is where `GET` is mid-to-low.

⚠️ **"Do not buy their guards" is retired.** The old blanket rule came from reading the +6.3
`REPL` gap as a prohibition; `jon.md` §*Their bar* now says that gap is **already inside
every `Δw ours`** and is a **tiebreak, not a veto** — read literally it excluded SGA, the one
name on their roster worth a conversation. **Fears, Wallace and Watson stay ranked where the sim
puts them.** The live reason to prefer forwards back is our guard glut plus the ~+13% positional
premium (~0.09 wins) — enough to break a tie, not enough to move a row.

⚠️ **Never take a pick back for him alone.** Their 2.10 is 640 BASE and pays **zero year-1 wins**
(`evaluating-picks`); Maluach → their 2.10 is roughly BASE-flat and **wins-negative**. We are
contending. Picks come to us only as ballast on top of a body.

## Two-body shapes, and the cap

We are **28/28**, so any 1-for-2 in our favour needs **one release** — Chaney Johnson, BASE 0,
`Δw` −0.10. Not free (he still pays as a light-night body) but the cheapest drop we have.

| shape | +wins | ΔBASE | verdict | `GET` on the ask |
|---|---:|---:|---:|---|
| Maluach → Bailey + Raynaud (cut Chaney) | **+1.03** | +2249 | **+4806** | both young risers — near-nil |
| Maluach → Ware + Wells (cut Chaney) | +0.92 | +2250 | +4533 | Ware high — unlikely |
| Maluach → Bailey + Sharpe (cut Chaney) | +0.80 | +2012 | +3998 | Bailey high — unlikely |
| Maluach → Raynaud + their 2.10 | +0.45 | +1100 | +2217 | Raynaud high — unlikely |
| **Maluach → Wells + their 2.08** | +0.43 | +912 | **+1979** | **mid + cap-driven — the live one** |
| **Maluach → Wells + their 2.10** | +0.43 | +764 | **+1831** | **mid + cap-driven — the live one** |
| **Maluach → Champagnie + their 2.08** | +0.34 | +639 | **+1490** | **low + cap-driven — the fallback** |
| Maluach → Champagnie + their 2.10 | +0.34 | +491 | +1342 | low + cap-driven |

**The bolding moved.** The old file bolded the three highest verdicts; under `GET` those are the
shapes he refuses. The **Wells- and Champagnie-plus-a-late-second** shapes are the ones where both
pieces are things he has a reason to move — Wells is `GET` mid, Champagnie `GET` low, and their
**2.08/2.10 are the assets `jon.md` says they have a structural, cap-driven reason to
sell** (27 bodies + 6 picks = 33 against a 38 cap, so their last seconds convert into bodies they
have no room for). Picks add **zero year-1 wins**, so they move ΔBASE only — which is exactly why
they are the right thing to stack on a small body ask.

## The pick conflict — resolve it here, not mid-negotiation

`../matthew/matthew-trade-strategy.md` earmarks **both 2.09 and 3.09** as the Giddey → Barnes sweetener
("ceiling is both picks"). They cannot also sweeten this channel. Simmed jointly — **one roster
state, wins do not add across legs**:

| programme | +wins | ΔBASE | verdict |
|---|---:|---:|---:|
| Giddey + 3.09 → Barnes (Pharaoh leg alone) | +0.50 | +2202 | +3443 |
| … + Maluach → Bailey *(no pick spent here)* | **+1.10** | **+3432** | **+6162** |
| … + Maluach + 2.09 → Ware *(both picks spent)* | +1.11 | +3124 | +5879 |
| … + Maluach → Wells | +0.88 | +2326 | +4510 |

**Spending 2.09 here buys +0.01 wins and costs 308 BASE.** So: **run this channel pick-free.**
Keep 3.09 for Barnes and hold 2.09 in reserve. Attach 2.09 only if Barnes is dead *and* it is
the difference between Ware and a Wells-tier return.

⚠️ **The conclusion survives the method change, but check the Pharaoh leg before quoting it.**
`../matthew/matthew-trade-strategy.md` is being re-derived on the same `GET`/`TVAL` change, so the
Giddey → Barnes row may move. Nothing in *this* file's decision turns on its size — the reason to
run pick-free is the +0.01-wins-for-308-BASE margin, which is internal to the two Maluach rows.

## SGA — the second channel, and why it does not open at market

`jon.md` §*What this means for us* read 1: **SGA is the only genuinely actionable asset
on their roster, and at market he is a bad buy for us.** `Δw ours` is now **measured, not guessed:
+2.354 ± 0.009**, so `TVAL` = **5,844** against BASE **9,352** — paying list is BASE-negative by
**~3,500**, flip point `κ*` = **1,504**, above our Q3 of **1,312**. The band supports the sign,
but only just; the eval itself says it is one `κ` re-derivation from a coin flip.

⚠️ **Quote 5,844, not 6,200.** The 6,200 in earlier notes was illustrative, off a placeholder
`Δw` of +2.5.

⚠️ **Şengün is not a channel.** `TVAL` **4,171** against BASE **6,188**, `κ*` 1,395, `GET` as high
as it goes, 24.0 years old and `✓✓` on `LATE` — a rebuilder keeps exactly this player, and even at
market we should decline. Both reads agree, which is the only place on this roster they do. **Do
not chase him and do not spend an ask on him.**

**What the discount has to look like.** The eval's threshold is that we need to be paying under
roughly **6,000 of BASE**. Measured shapes, same basis, 3 × 200 CRN trials:

| shape | +wins | sd | BASE out | ΔBASE | verdict |
|---|---:|---:|---:|---:|---:|
| Garland + Maluach → SGA | +1.52 | 0.010 | 3,840 | +5512 | +9280 |
| Edey + Coby + Maluach → SGA | +1.23 | 0.031 | 4,410 | +4942 | +7995 |
| Garland + Coby → SGA | +1.10 | 0.021 | 4,681 | +4671 | +7401 |
| Garland + Coby + Maluach → SGA | +1.03 | 0.010 | 5,240 | +4112 | +6669 |
| Giddey + Maluach → SGA | +0.89 | 0.022 | 4,696 | +4656 | +6875 |
| *Cade + Maluach → SGA* | +0.46 | 0.026 | 8,722 | +630 | +1771 |
| *Cade → SGA (straight)* | +0.56 | 0.005 | 8,163 | +1189 | +2572 |

⚠️ **Every discount shape is one he refuses, and that is the whole problem.** The five that clear
6,000 of BASE are built on Garland (26.5), Coby (26.5), Edey (24.2) and Giddey (23.8) — win-now
vets a rebuilder trading a 28-year-old star has no use for. **The currency that gets a discount
and the currency he will accept do not intersect** anywhere except our own young core. So: **do
not open this channel with a package.** Sound out what he wants back for SGA first (`trades`:
we cannot state why he'd say yes until we know it), and let his answer, not our list, set the
shape.

⚠️ **Cade → SGA is flagged for human review, not recommended here.** It clears both tests on
paper — ΔBASE +1,189, `TVAL` +1,053 (5,844 vs Cade's 4,791), verdict +2,572 — and it is the one
shape whose `GET` runs *our* way, because a rebuilder actively prefers a 24.8-year-old to a
28.1-year-old. But Cade is ***Core*** in `my-team-situation`'s grid, `trades` says **don't shop
*Core***, and the whole call rests on a `κ*` the eval already calls fragile. **Do not put this on
the table without a human decision.**

## Ladder to run

Smallest good swap first, separate asks, each separately refusable (`trades`). Ordered by what
`GET` says is gettable, not by verdict — the verdict column is monotone in *their* BASE, which is
monotone in what a rebuilder refuses.

1. **Open — two asks, expect one:** Maluach for **Kel'el Ware**; if that is refused, Maluach for
   **Ace Bailey**. Both straight, no pick attached. Anchor is lopsided in *value*, not in shape —
   a clean 1-for-1 is what survives being wrong. ⚠️ **Expect both to fail now.** Ware is `GET`
   high and Bailey is on the refuse-at-any-price list. That is fine: they are the anchor, and
   their job is to make step 2 look moderate.
2. **Target, and the realistic landing zone — this step changed:** **Maluach → Jaylen Wells + one
   of their late Sept-'26 seconds (2.08 or 2.10).** +0.43 wins, +912 / +764 BASE, verdict
   **+1,979 / +1,831**. Wells is `GET` **mid** — the highest-BASE name on their roster that is not
   a star or a young riser — and the seconds are the one thing they have a **structural reason to
   move** (27 bodies + 6 picks = 33, room for only 5 of a 7-man auction before the 38 cap).
   *Previously this step asked for Raynaud + a second;* Raynaud is now on the eval's young-riser
   list, so he moves to a step-1-style anchor ask, not a landing zone.
3. **`GET`-low fallback:** **Maluach → Justin Champagnie + 2.08** (+0.34 / +639 / **+1490**).
   Champagnie is the cheapest thing to *ask* for on the whole roster — 25.1, no pedigree, 410
   BASE, `GET` **low** — and he is a forward, our thin group. `TVAL` 323 vs BASE 410 flips at
   `κ` 1,194, inside the band, so he is not an edge at market; **at Maluach's price he is
   comfortably positive anyway.**
4. **Acceptable floor:** Maluach → **Jaylen Wells** straight (+0.43 / +124 / **+1191**). Near
   BASE-neutral, so it is the version *he* is most likely to propose — and it is still good.
5. **Only if the above are dead:** Maluach + 2.09 → Ware (+0.59 / +922 / **+2386**), accepting the
   cost to the Barnes leg.
6. **Walk:** Maluach for Sharpe, Wolf, da Silva or Minott alone; Maluach for any pick alone;
   Maluach as a sweetener in a package built around someone else. **Şengün is not an ask.**

## In his frame — age and `FPts/G`, both on the roster page he reads

- **Sell Maluach as:** 19.9, tenth pick in the 2025 draft, starting centre in Phoenix, and the
  summer league is real and public. All true, all checkable. Brett already said it well.
- **Do not volunteer:** that he is sub-replacement for us, that we are nine deep at centre, that
  Mark Williams just made him redundant, or any board rank or win figure (`trades` §*Reveal /
  withhold*).
- **Ask in his units:** Ware is **22.3** and Raynaud **23.3** — *older* than Maluach in a
  rebuilder's frame, which is the argument that costs us nothing. Bailey at **20.0** with lottery
  pedigree is the one he will guard hardest; expect the Bailey ask to fail and use it to make the
  Ware ask look moderate. **The landing-zone names are the easiest sell of all**: Wells is
  **22.9 at 20.4 FPts/G** and Champagnie **25.1 at 20.9** — a 19-year-old lottery centre for a
  22-and-a-25-year-old role player is a story a rebuilder tells himself.
- **Story for a rebuilder:** *the piece for when the window opens.* He is 19 and you are two
  years out — the timelines match.
- **Never say** `TVAL`, that we score his assets at all, that we simulate, our ordering of his
  roster, or *why* we want a forward (`trades` §*Reveal / withhold*). Everything in the `GET` /
  `TVAL` tables above is internal. If he prices something wrong in our favour, **restate the deal
  in his units — don't correct him.**

⚠️ **His answer to "what's your MO" has not arrived** (last message Delivered, no reply). We
already know it from the wire — clearest rebuilder in the league — so the ladder does not depend
on it. What his answer *does* change: if he says **win-now**, Raynaud and Ware get harder and his
late seconds get cheaper; if he says **tank**, the seconds get harder and his 22-24 year-old
producers get cheaper. Read it before choosing between step 2 and step 3.

## Memory — log every exchange here

**2026-07-29, opened by us.** "Let's talk trade — anything you're looking for, or anyone you're
willing to part with for the right price?" He: *"lol that 1st round pick you just traded"* — i.e.
our **2026 1.09**, sent to The Don in 483809. Then: *"I would maybe be interested in Maluach."*

**2026-07-30, us.** *"He's been having a really good summer league, but he's available. What's
your MO in general? Trying to tank, win now, build for future?"* — **Delivered, no reply yet.**

- **Declared interest:** Khaman Maluach. Unprompted, and the only name he has raised.
- **Wants picks** — opened by naming a 1st. Ours land ~1.10 every year and are cheap currency,
  but see the pick-conflict section before spending one here.
- **Nothing refused yet. No ask made by us yet.**
- **Their untouchables, inferred:** Şengün (24.0, `✓✓`, exactly what a rebuilder keeps) and
  their own 2027/2028 1sts. SGA is genuinely available but is a separate, much larger
  conversation — `jon.md` §*What this means for us* read 1, and **`Δw` ours on SGA is
  still unmeasured.**

### Does the record above still hold under `GET`/`TVAL`? — added 2026-07-30, log unchanged

The log is verbatim and nothing in it was retracted. Three of the calls sitting on it move:

- **"`Δw` ours on SGA is still unmeasured" is now out of date** — it is **+2.354 ± 0.009**,
  `TVAL` **5,844** against BASE **9,352** (§*SGA — the second channel*). The conclusion the
  clause supported ("separate, much larger conversation") **still holds**, and is now
  quantified rather than deferred.
- **Şengün as an untouchable: confirmed twice over.** He was inferred untouchable from his
  profile; `TVAL` **4,171** vs BASE **6,188** now says we should decline him *even if he were
  available*. Both reads agree — stop tracking him as an ask.
- **"Wants picks" is still the most useful line in the log**, and it now reads differently. Our
  picks are cheap currency and their **2.08/2.10** are cheap to *them* for a cap reason, so the
  pick axis is live in **both** directions. The pick-conflict section still says run the Maluach
  channel pick-free from our side; it does not say refuse theirs.

Unchanged: his **declared interest in Maluach** — still the only name he has raised, still the
right thing to sell, and `TVAL` **−348** (`../my-team/my-team.md`) makes the case stronger than the
old file did, not weaker. Nothing has been refused, so no refusal needs re-reading.

## Caveats that cut against this file

- **Maluach's rate is `sim.PROJECTED_RATE`, hand-typed at 16.0** against a real rookie season of
  8.2. Every win figure here rests on it. If he is genuinely a 20+ starter this year, the whole
  ladder shifts against selling — and the summer league is a reason to think it might. `team-eval`
  permits the projection as a **role change**, but it is the softest input on the page.
- **His BASE of 559 is the least well-sourced on our roster** — **off the Dizzle board entirely**,
  154 expert, 340 crowd, so one board's weight is renormalised away. A 19-year-old's price is
  exactly what moves most between snapshots. Re-pull before closing.
- **Bailey vs Ware is inside the noise** and I have called it a tie. Do not let the ordering in
  the table above read as a finding.
- **Two-body shapes assume Chaney Johnson is the drop.** He is BASE 0 but not valueless — he pays
  as a light-night body, and at 38 in September a shipped body stops being replaceable
  (`league-info`). Price the drop, don't wave it through.
- **`M` = 1.0 is ours, not a fact.** `team-projections.md` has us 2nd / 2nd / 4th across the
  window, which is a top seed throughout — but 4th in year 3 is arguably bubble. At `M` = 0.9
  every verdict above falls ~11%; **no sign flips and no ordering moves**, including Minott's.
- **`GET` is judgment, not a measurement.** Every "he refuses this at any price" above is an
  inference from a rebuilder's profile plus `jon.md`'s read — **not** something Jon has
  said. The `FetchTradeBlock` carries nothing of theirs, so there is no declared intent to
  override it with. The asks in steps 1–3 are cheap to make; make them and let his answers
  replace the inference.
- **Champagnie's and Wells's `TVAL` both flip inside `κ`'s band** (1,194 and 1,186 against
  630–1312). At market they are undecided, and this file leans on them as landing zones only
  because *Maluach's* price makes the concrete deal clear regardless. If the ask ever becomes
  "Champagnie for something real of ours", **that argument does not carry over.**
- **The SGA discount table is measured but hypothetical.** None of those shapes has been floated,
  and the `GET` read says every clearing one is a shape he refuses. Treat the table as sizing the
  discount, not as a menu.
