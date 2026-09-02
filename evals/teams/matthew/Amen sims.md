# Amen Thompson shapes — sim record (Pharaoh Mattankhamun-Ra)

Every Amen-out shape priced against Matthew, run **2026-08-12**. Column meanings: `Eval Definitions`, `Delta w.md`, `Bracket value.md`. Roster and pick values: `Matthew's Team.md`, `evals/teams/my-team/My Team.md`.

**Method.** All 12 roster files re-fetched 2026-08-12 18:47 (the draw for `ΔP(title)` reads all 12). Our 28 real bodies padded to 38. `Δw` is one joint `engine.run(swap(...), cal=DELTA_W_CAL)` per shape over 19 matchups, 200 trials × 8 seed blocks, against `wins(after, before)`. `ΔP(title)` here is `P(title|seed)` via `bracket.roster_title`, band **1–2** unless stated — not the eval column (`Eval Definitions §ΔP(title)`). **No figure here is a sum of per-player rows.** `ΔBASE` is board arithmetic, not sim.

**Baseline** (before any pending deal): `P(title)` band 1–2 **56.5%** (sd 0.6) · 3–4 37.1% · 5–8 31.8%. `REPL` guard/forward/center **18.7 / 17.0 / 19.9**. 1 win = **597** PF ±14%.

## The shapes

| | We send | We receive |
| --- | --- | --- |
| **S1** | Amen + Edey | Scottie + Keegan + his 3.05 |
| **S2** | Amen + Duren | Scottie + Keegan + Sharpe |
| **S3** | Amen + Suggs | Scottie + Vassell |
| **S4** | Amen + Edey | Scottie + Ausar |
| **S5** | Amen | Ausar + Keegan + Sharpe + Vassell + **5th piece** |

S6 was S1 without the pick; identical player side, so one run serves both.

## Against the current roster

| Shape | ΔBASE | Δw | ΔP(title) 1–2 | 3–4 | 5–8 |
| --- | ---: | ---: | ---: | ---: | ---: |
| S1 | +867 | +0.034 (.011) | +1.22 (.38) | +1.31 | −0.01 |
| S2 | +491 | +0.779 (.012) | +5.95 (.48) | +7.72 | +6.71 |
| S3 | +1097 | +0.286 (.010) | **−4.20** (.31) | −2.26 | −2.44 |
| S4 | +596 | +0.142 (.012) | +1.79 (.38) | +2.20 | +1.41 |
| S5 (Clowney) | +787 | +0.937 (.014) | +9.93 (.47) | +10.88 | +10.46 |

S1 sits **under the 0.1-win floor** — win-neutral, not a win gain.

**Row sums were wrong by 3–4× on exactly these shapes.** Additive rows read S5 +0.25 and S2 +0.45 against joint +0.937 and +0.779; S1's title read −1.8pp from the single-piece comparison against joint +1.22pp. Receiving more bodies than we send is where the stack breaks down.

## Executed today, at the 28-man cap

S2 and S5 hand us more bodies than we send. The rows above displace pad slots (`FA3`–`FA6`), which only exists once rosters reach 38. Executed today each extra body forces a real cut, and `ΔBASE` below charges every cut as value forfeited.

| Variant | ΔBASE | Δw | ΔP(title) 1–2 |
| --- | ---: | ---: | ---: |
| S2, pads | +491 | +0.779 | +5.95 (.48) |
| S2, cut Chaney | +491 | +0.691 (.018) | +5.83 (.85) |
| S5, pads | +787 | +0.937 | +9.93 (.47) |
| S5, cut Chaney/Matković/Holmes/Bona | +292 | +0.833 (.017) | +8.36 (.74) |
| S5, cut Melton/Ellis/Huff/Matković | −214 | +0.719 (.019) | +8.37 (.40) |

## If Duren goes to Hlina first

`Pending Trades.md` owns the Duren ↔ Jalen Williams deal. Priced on our roster as it stands:

| | ΔBASE | Δw | ΔP(title) 1–2 |
| --- | ---: | ---: | ---: |
| Duren → Williams | +1,024 | +0.724 (.006) | +0.17 (.50) |
| + our '26 2nd | +379 | +0.724 | +0.17 |
| + Keon Ellis | +775 | +0.582 (.009) | **−2.22** (.66) |
| + Melton | +681 | +0.654 (.012) | −0.34 (.46) |

**Sweeten with a pick, never a body.** A pick moves no body, so `Δw` and `ΔP(title)` are the straight-swap row. Ellis costs 249 BASE and 2.2pp of title.

Williams is a seeding upgrade, not a bracket one — his W22+W23 is 175 against Duren's 175, which is why title reads flat.

**What it does to us.** `REPL` center 19.9 → **18.4**, so Edey gains: `Δw` +0.44 → **+0.54**, `ΔP(title)` 4.99 → **5.98pp**. Amen barely moves (+1.79 → +1.74, 15.63 → 14.99pp), so Williams does not make him redundant. Mark Williams +0.29 → +0.37; Giddey +1.27 → +1.32; Naz, Turner, Kawhi flat.

Re-priced against the post-Williams roster, **every Edey shape dies**:

| Shape | ΔBASE | Δw | ΔP(title) 1–2 |
| --- | ---: | ---: | ---: |
| S5 today | +292 | +0.879 (.021) | +9.03 (.94) |
| S5 post-Sept | +787 | +0.957 (.013) | +10.84 (.34) |
| S1 | +867 | **−0.075** (.012) | +1.06 (.25) |
| S4 | +596 | +0.032 (.009) | +1.62 (.36) |
| S3 | +1097 | +0.181 (.011) | −3.98 (.36) |

## What Duren is for

Duren has two mutually exclusive uses. Both measured cumulatively against the same post-Henry baseline (`Pending Trades.md` §Henry: Hunter in, Chaney cut), at post-Sept execution so neither forfeits a body.

| Portfolio | ΔBASE | Δw | ΔP(title) 1–2 |
| --- | ---: | ---: | ---: |
| **A — Hlina + S5** | **+1,811** | **+1.629** (.016) | **+9.94** (.55) |
| B — S2 alone | +491 | +0.752 (.018) | +5.59 (.43) |

A still leads at +1,166 BASE if Hlina takes the '26 2nd. **S2 is dominated on all three columns**: bundling Amen and Duren into one package costs ~0.9 wins against selling them separately. S5 and the Hlina deal never touch the same piece.

S5 is also insensitive to whether either pending deal lands — both together move it ~0.05 wins and ~0.3pp — so it needs no sequencing.

## Which four to cut, and who the 5th piece is

Both on the post-Henry + post-Hlina baseline. Chaney is spent on the Henry deal, so the cut pool is one shorter.

| S5 cut set | ΔBASE | Δw | ΔP(title) 1–2 |
| --- | ---: | ---: | ---: |
| **post-Sept, none** | **+787** | **+0.888** | +9.60 (.67) |
| Matković/Holmes/Bona/Melton | −51 | +0.813 | +9.42 (.62) |
| Matković/Holmes/Melton/Ellis | −93 | +0.870 | +7.86 (.65) |
| Matković/Holmes/Bona/Huff | +4 | +0.640 | +9.65 (.71) |
| Matković/Holmes/Bona/Middleton | +173 | +0.601 | +7.81 (.72) |

Middleton is the worst cut available — the only body in that pool with positive `Δw`.

| S5 5th piece | ΔBASE | Δw | ΔP(title) 1–2 |
| --- | ---: | ---: | ---: |
| **Tari Eason** | +1,376 | **+1.229** (.016) | **+10.19** (.68) |
| Noah Clowney | +787 | +0.888 (.017) | +9.60 (.67) |
| Khaman Maluach | +784 | +0.825 (.018) | +8.33 (.70) |
| Thomas Sorber | +765 | +0.749 (.016) | +6.86 (.69) |

Eason wins every column. Neither center helps despite Duren leaving — `REPL` center only reaches 18.6. Eason alone breaks the ≤1k lopsidedness cap, so pair him with our own '27 2nd (540, BASE-only): **+836 / +1.229 / +10.19pp**, and the '26 2nd stays free for Hlina.

## Sensitivities — both favour the shape

Assumed inputs, not measurements. Neither flips a call; both make the published figures a floor.

**Auction budget concentration.** Filling three auction slots instead of seven with the same money should grade those bodies higher. Per rate point of upgrade: ~+0.05 wins, ~+0.25pp.

| Upgrade on kept slots | Eason `Δw` / `ΔP` | Clowney `Δw` / `ΔP` |
| --- | ---: | ---: |
| none | +1.229 / +10.19 | +0.888 / +9.60 |
| +2 | +1.323 / +10.69 | +0.984 / +10.07 |
| +4 | +1.433 / +11.26 | +1.096 / +10.60 |
| +6 | +1.567 / +11.94 | +1.229 / +11.26 |

**No '26 rookie picks** (2.09 to Hlina, 3.09 to Henry), modelling `RK0`/`RK1`/`RK2` down to 11/9/7: Eason **+1.324 / +11.02pp**, Clowney **+0.982 / +10.51pp** — higher than the standard pad, because a thinner surrounding roster makes each real body worth more.

# Matthew's counter — 2026-08-13

We sent S5+Eason+our '27 2nd. He countered **Amen (no 2nd) → Keegan + Sharpe + Vassell + Eason + Kuminga**, keeping Ausar. Live objection in the morning texts is **five viable bodies**, not brothers — Sharpe and Murray are "the main 2"; additions are fungible.

Joint run 2026-08-13, current roster (Henry/Hlina not on it), post-Sept pads, same method as above. Picks BASE-only, not in the sim.

| Shape | We receive | ΔBASE | Δw | ΔP(title) 1–2 |
| --- | --- | ---: | ---: | ---: |
| **HIS** (his offer) | Keegan Sharpe Vassell Eason Kuminga | **+242** | **+0.980** (.026) | **+5.74** |
| AUS | Ausar Keegan Sharpe Vassell Eason | +1,376 | +1.309 | +10.76 |
| AUS_KUM | Ausar Keegan Sharpe Vassell Kuminga | +768 | +1.073 | +8.78 |
| AUS_VAS | Ausar Keegan Sharpe Eason Kuminga | +738 | +0.914 | +10.10 |
| AUS_KEEG | Ausar Sharpe Vassell Eason Kuminga | +418 | +1.074 | +5.77 |
| AUS_SHAR | Ausar Keegan Vassell Eason Kuminga | +723 | +0.758 | +3.45 |
| FOUR | Keegan Sharpe Vassell Eason | −307 | +0.750 | +6.18 |
| **FOUR_AUS** | Ausar Keegan Sharpe Vassell | **+219** | **+0.844** | **+8.63** |
| FOUR_AUS_EAS | Ausar Keegan Sharpe Eason | +189 | +0.694 | +10.25 |
| DICK | Keegan Sharpe Vassell Eason Dick | −75 | +1.146 | +7.85 |
| CLOW | Keegan Sharpe Vassell Eason Clowney | +261 | +0.845 | +6.97 |
| THREE_AUS | Ausar Keegan Sharpe | −968 | +0.182 | +6.32 |

AUS on this roster vs the 08-12 post-Henry/Hlina S5-Eason row: +1.309 / +10.76 against +1.229 / +10.19. Same call.

**Sharpe is load-bearing** — AUS_SHAR is the only 5-pack that craters title. Keegan ≈ Ausar on title (AUS_KEEG ≈ HIS), so if Ausar stays, Keegan has to stay too. Dick `rot1` — that +1.146 is an upper bound.

**Kuminga is a real 5th.** `fa` blanks the eval `W` cells so we don't print LAC's games as his; `team_nights` still runs him on `SIM_TM` (LAC) for both `Δw` and `ΔP(title)` — same as every unsigned body. LAC is in the 8-game W22+W23 group, not the 6-game one, so HIS title is not a hollow-schedule artifact. Incoming row is +0.14 / +1.2pp. FOUR vs HIS title (+6.18 vs +5.74) is not "Kuminga has no bracket"; don't drop him for an empty slot.

# The '27 2nd (own 2.12, ≤540)

Pick is BASE-only. Same player side, 2nd on vs off — no new joint run.

| Player side | 2nd off | 2nd on | Δw / ΔP 1–2 (either) |
| --- | ---: | ---: | --- |
| HIS | **+242** | −298 | +0.98 / +5.7 |
| AUS (original) | +1,376 | **+836** | +1.31 / +10.8 |
| AUS_KUM | +768 | **+228** | +1.07 / +8.8 |
| AUS_VAS | +738 | +198 | +0.91 / +10.1 |
| FOUR_AUS | **+219** | −321 | +0.84 / +8.6 |
| FOUR | −307 | −847 | +0.75 / +6.2 |

Use the 2nd to buy Ausar. Gifting it onto HIS is −298 BASE for the same wins. FOUR_AUS+2nd pays the pick and loses a body.

# Post-Henry (Cam + Hunter in, Johnson + Holmes out) — 2026-08-13

In-memory swap on the current 38-pad, same method. Picks BASE-only. REPL moves **18.7/17.0/19.9 → 21.1/18.0/21.2**; baseline PF 30,231 → **30,785**. Incoming Amen-out deltas compress; ranking among live shapes does not flip.

| Shape | ΔBASE | Δw pre → post | ΔP 1–2 pre → post |
| --- | ---: | --- | --- |
| **HIS** | +242 | +0.98 → **+0.80** | +5.7 → **+4.2** |
| **FOUR_AUS** | +219 | +0.84 → **+0.68** | +8.6 → **+5.9** |
| FOUR_AUS_EAS | +189 | +0.69 → **+0.53** | +10.3 → **+8.4** |
| AUS | +1,376 | +1.31 → **+1.13** | +10.8 → **+8.7** |
| AUS_KUM | +768 | +1.07 → **+0.88** | +8.8 → **+6.4** |
| AUS_VAS | +738 | +0.91 → **+0.73** | +10.1 → **+8.4** |
| FOUR | −307 | +0.75 → **+0.60** | +6.2 → **+4.4** |

2nd-on BASE is the same haircut as above (own '27 2.12 ≤540). 2.09 is spent on Henry; it is not the Matthew 2nd.

# Fifth piece, post-Henry — 2026-08-13

Each shape's **absolute** `ΔBASE` is a band (5-for-1, `BASE.md` §*Summing across a package*). **Against HIS it is not** — every row below differs from HIS by one or two bodies, and a like-for-like body swap is pick-free and body-neutral, so it keeps its point value. Swept over the full `a` range, every margin is sign-stable.

| Shape | 5 bodies in | ΔBASE vs HIS | Δw | ΔP(title) 1–2 |
| --- | --- | ---: | ---: | ---: |
| HIS (his offer) | Keegan Sharpe Vassell Eason **Kuminga** | — | +0.801 (.032) | +4.16 |
| **DICK** | Keegan Sharpe Vassell Eason **Dick** | **−317** (−548…−177) | **+0.966** (.031) | **+6.68** |
| BLACK | Keegan Sharpe Vassell Eason **Black** | +38 | +0.709 | +6.05 |
| CLOW | Keegan Sharpe Vassell Eason **Clowney** | +19 | +0.713 | +5.99 |
| AUS_VAS | **Ausar** Keegan Sharpe Eason Kuminga | **+496** (+310…+714) | +0.725 | +8.41 |
| **DICK_AUS** | **Ausar** Keegan Sharpe Eason **Dick** | **+179** | +0.906 | **+10.30** |

**DICK is a purchase, not a freebie** — it buys +0.17 wins and +2.5pp of title for **~317 BASE**. Cheap against Amen's 5,360 and the right side of the contending rule, but say the price. It is easy for him to accept precisely because he keeps the better board asset: Kuminga 549, Dick 232.

⚠️ **Dick's edge is a projection call.** `rot1`, and his 23 rate is 2.3× last season's 10; Kuminga's 24 sits against 22. All three boards rank Kuminga ahead. If the role does not land we paid 317 for nothing — ask cheaply, do not chase it.

**DICK_AUS dominates HIS on all three** (+179 BASE, +0.11 wins, +6.1pp title) and dominates AUS_VAS outright. It is the shape to name if Ausar ever reopens; do not spend a third ask on him unprompted.

**AUS_VAS needs no 2nd.** Player-side it is +496 BASE over HIS, well inside any lopsidedness worry; attaching the '27 2nd (≤540) hands that back for nothing.

Black and Clowney are within ~40 BASE of HIS and lose to Dick on both sim columns; drop them.

# Where it lands

**Assumed through 2026-08-13 as HIS** (Amen → Keegan, Sharpe, Vassell, Eason, Kuminga). Record: `Pending Trades.md`. Do not re-open Ausar / DICK / a 2nd.

**Body count at expansion:** +4 net → 32 bodies. We hold 2.09 (3.09 is Henry's). Make 2.09, then auction 5 of the 7 FA slots.

# Caveats

- `Δw` carries the ±14% on PF-per-win. `ΔP(title)` is band 1–2 and belongs to this roster, not the format — never netted against `Δw`.
- Flags: Edey `frag`/`rot2`, Keegan `frag`, Clowney `rot2`, Dick `rot1` — `Δw` is an upper bound on those rows. Williams and Duren carry none. Kuminga is `fa`.
- He proposed the 5-for-1 himself, so 21 bodies before the auction is a pain he has already accepted on HIS.
- Hlina is projected 1st in '27-28, so Duren arms a rising competitor's window.
- Re-run rather than quote: every figure is a property of the roster it was run on, and any executed trade moves both `R` and the draw.
