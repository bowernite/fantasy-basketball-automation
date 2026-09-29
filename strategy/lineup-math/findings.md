# Findings

Every number a trade decision reads, and the caveats that flip a sign. `method.md` owns the basis; `README.md` owns the commands. Formula `Δw` is the league curve (`league-curve.md`), not `(rate − R) × GP ÷ K`.

**Re-run rather than quote.** Measured 2026-09-29 on the post-draft rosters (ours 38 real bodies, nothing padded), F/C flex slot.

# PF → wins

**1 win ≈ 597 PF, ±14% (518–679).** Quote the band. Real weekly mean 1,361 sd 261; margin mean +34 sd 236. ⚠️ Weekly scores are correlated (ρ 0.64) — adding sds in quadrature gives 993 PF/win and is wrong.

| +PF/season | +250 | +500 | +1,000 | +2,000 | +3,000 |
|---|---:|---:|---:|---:|---:|
| +wins/19 | +0.40 | +0.79 | +1.56 | +3.00 | +4.28 |

**Ceiling: a single 1-for-1 tops out near +2.9 wins, and only for the best player alive; a programme of three reaches +3.3.** Anything pitched above that is wrong. Variance is third-order.

# Consolidation is not the lever

**Body count still costs, but less on a full, deep roster.** Same star coming back, N-for-1: **+2.85 → +2.29 → +2.26 → +2.04 → +1.40** at N = 1/2/3/4/5.

- **Splitting a consolidation into separate 1-for-1s is worth 1.6× at N=2 and 2.9× at N=3** (two / three 1-for-1s → 42s against a 2- / 3-for-1 → 50).
- **The bottom is no longer the cheap win.** Our three lowest bodies → three 26-rate bodies @76 GP = **+0.43**, a third of a 1-for-1 for a 45 (+1.31).
- **GP is as important as rate.** A 55 @40 GP bought 3-for-1 is **+0.51**; a 40 @78 GP bought 1-for-1 is **+1.09**.
- **Backfill grade barely moves a break-even** — ≤1.3 rate points across the 6/40 → 14/55 bracket — and flips no sign.
- ⚠️ Suggs/Coby/Mark Williams/Poeltl/Reid are the study's **filler**, held fixed so body count is the only variable — not a bucket, not a send list. Buckets: `strategy/teams/my-team/Ours.team.md`.

# Break-evens

Incoming rate for an N-for-1 to be PF-neutral, on our 38. **The row you pick decides the sign** — match his GP and position.

| incoming shape | 2-for-1 | 3-for-1 | 4-for-1 | 5-for-1 |
|---|---:|---:|---:|---:|
| 68 GP forward | 35.6 | 35.9 | 38.7 | 47.2 |
| 65 GP center | 36.0 | 36.4 | 39.2 | 47.8 |
| 78 GP forward | 34.3 | 34.6 | 36.9 | 44.3 |

**Three dregs (Melton, Simons, Ellis) break even at 34.1**, which the 37–60 board band supplies. The filler 5-for-1 needs a top-12 rate.

# Is the incoming rate even purchasable?

| board rank | 1-12 | 13-24 | 25-36 | 37-60 | 61-96 | 97-150 | 151-250 | 251-456 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| median FPts/G | 47.8 | 39.0 | 38.1 | 35.7 | 30.7 | 27.5 | 22.8 | 15.7 |

**Only 8 players cleared 45 FPts/G at 30+ GP last season — 3 cleared 50, one cleared 60.** The board discounts age and the format pays rate, but **nothing here measures an age curve — quote no aging term and no horizon.**

# Replacement level

`R` on our 38 = **24.9** (forward), **22.6** thinned to 28. Per slot group: guard **26.1** · forward **24.9** · center **24.8**; `K` 825–843. With the F/C flex, center and forward replacement coincide; guard sits 1.2 above.

⚠️ **The league-curve formula `Δw` over-predicts sim 1-for-1s (`Δw (season)`) by a median +113%** (worst +347%) on our roster, and is least trustworthy on low-rate/low-GP players. It also misorders the top 5. **Trade decisions lean on `Δw (season)`**; always publish formula `Δw` beside it (`Eval Definitions §Δw (season)`).

Value in rate is **linear above ~30** (~52 PF per rate point on a 68-GP body); below 30 it is convex.

# GP is the dominant input — and one season of it is enough

```
GP_map = 25.7 + 0.368 × last season's GP + 0.432 × min(last season's FPts/G, 30)
GPp    = mean(Hashtag, FanScout) when both hit; the one feed if only one; GP_map if neither
```

Applied by `our_roster` to **both sides of any trade**, so a counterparty's injured star cannot be priced at his worst season while ours ride forward.

- **One season beats a flat prior; more history does not add; age never helps** — keep age out of GP, and no report here measures an age curve.
- **The whole exercise is worth ~4% of the error.** GP is a defensible input, not a precise one: **never argue a trade on a few games of GP.**
- ⚠️ **Over-shrunk**: an iron-man reads too low, a fragile starter too high. **Censored** — a whole missed season is absent from the pool, so every figure is expected GP *given he plays at all*.
- ⚠️ **Weakest on a fragment season**, where the fragment is the model's only evidence. Flag those rows; don't patch them. Map is fallback when neither feed hits (`Eval Definitions §Durability`).
- Persistence is low: everyone converges to **~59–62 GP**.

# Durability

**No format-derived injury adjustment.** With foreknowledge the format is close to proportional. Onset-corrected cost across the whole 38-man roster: **−0.11 / −0.27 / −0.42 wins** at 10 / 25 / 40% of blocks absent; **≤3.5% of a player's value**, flat in GP. **Burstiness is EV-neutral over a season** — but not over a bracket window (§*Bracket weeks*).

# The slot-fill curve

At 38 bodies a 7-game night fills **8.97 of 9** slots, and 9.00 arrives at **9 games**. **45 of 1,098 slot-nights unfilled (4.1%)**, and the constraint is concentrated: **8 nights (≤3 games) carry 67% of the loss, 23 nights (≤5 games) carry 96%.**

- **Heavy night: only rate matters.** **Light night** (≤5 NBA games, **23** of 122 scored, 8 at ≤3): nearly everyone available starts, so it is **presence, not rate**.
- **Surplus is therefore the middle of the roster** — not the top, not the tail.
- Positions rarely bind: 1.2% of slot-nights lost to no legal slot against 2.9% to no body at all.
- ⚠️ **No "season loss = N PF" figure is defensible** — the same slots price very differently depending on an assumed price. Quote the share columns.

# Positional premium — a fact about *our* roster, not the format

Added body of identical rate, versus that rate as a guard:

| rate | 25 | 35 | 45 |
|---|---:|---:|---:|
| forward vs guard | −5% | **+21%** | +10% |
| center vs guard | −1% | **+23%** | +10% |

**Forward and center price alike; guard is the discount.** ⚠️ Purely a function of our current shape (16 pure guards for ≤5 slots, 7 pure centers for 4, 11 pure forwards for 5); it moves when that changes.

# Light-night coverage

No current measurement: the `schedules` report was built for the Sept '26 auction and is archived. The rule in `Format edges.md` stands; re-measure before quoting a size.

# Bracket weeks — what a game is worth once the bracket starts

| band | rounds | P(title) | by seed | one bracket game × one regular game |
|---|---:|---:|---:|---:|
| 1–2 | 2 | 0.595 | 0.561–0.629 | **14.1** |
| 3–4 | 3 | 0.433 | 0.386–0.480 | **10.8** |
| 5–8 | 4 | 0.304 | 0.216–0.338 | **7.8** |

We project **1st of 12** on season PF (32,166), so **band 1–2 applies to us** for the seed-conditional read. Per-player `P(title|seed)` tops out at **+11.1 percentage points** (Cade Cunningham, band 1–2). The eval column is unconditional `ΔP(title)` (`sim.player_title` on our roster file). `sim.py playoffs` is seed-held, not that column.

- ⚠️ **It scales with `P(title)`, so it is a fact about the roster loaded, not the format** — a rebuilding team reads far lower. **Re-run per roster**, and never sum, net or convert `ΔP(title)` against `Δw (season)` (`Eval Definitions §ΔP(title)`).
- ⚠️ **A band is a seed range and the draw splits it** (6 and 7 sit on the 2-seed's side, 5 and 8 on the 1-seed's). A call that turns on the spread needs the seed.
- **A bracket week is not four games for everybody.** W22+W23 runs **8 games for 11 teams and 6 for 5** — a third of a bracket week between otherwise identical bodies, and nothing in a season rate says so.

# Title odds — the season simulated end to end

`sim.py title`, 2026-09-29. §*Bracket weeks* prices a round **given** a seed; this earns it first, so **`P(title)` is unconditional and the twelve teams sum to 1.** Per-player `ΔP(title)` is this same run (`Eval Definitions §ΔP(title)`).

| | us | Michael | Josh | Brian | rest |
|---|---:|---:|---:|---:|---:|
| **P(title)** | **0.555** | 0.132 | 0.093 | 0.074 | ≤0.069 |
| expected wins of 19 | 16.2 | 12.8 | 11.8 | 13.2 | |

- **We take the 1-seed in 85% of seasons** and make the bracket in ~100%.
- **Having to earn the seed costs us 0.4 points** against being handed the 1-seed (0.559 → 0.555).
- ⚠️ **Never summed, netted or converted against `Δw (season)`** (`Eval Definitions §ΔP(title)`).
- ⚠️ **Matchups are decided on the wire's spread (0.1005)** — availability is all that moves in the engine. Calibration: simulated standings spread 4.29 against the wire's 4.17.
- ⚠️ **The slate is this year's** — 19 pairings, seats not re-dealt. Period 20 is R1 and still a generated full slate; 21–23 have dates only.
