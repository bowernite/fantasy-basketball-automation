# Findings — TL;DR

Every number a trade decision reads, and the caveats that flip a sign. **`findings.md` is the full file — the error bars, the derivations, the unordered pairs and the re-cut warnings. Open it only when a call turns on one of those, or when you need a table not here. It should be rare** `method.md` owns the basis; `README.md` owns the commands.

**Re-run rather than quote.** Measured 2026-08-03 (§*Bracket weeks* 2026-08-08), then 28 bodies padded to 38. Roster is now 32 post-overlay (`Pending Trades.md`) — figures below are pre-overlay.

# PF → wins

**1 win ≈ 600 PF, ±14% (518–679).** Quote the band. Weekly mean 1,361 sd 261; margin mean +34 sd 236. ⚠️ Weekly scores are correlated (ρ 0.64) — adding sds in quadrature gives 993 PF/win and is wrong.

| +PF/season | +250 | +500 | +1,000 | +2,000 | +3,000 |
|---|---:|---:|---:|---:|---:|
| +wins/20 | +0.42 | +0.83 | +1.64 | +3.16 | +4.50 |

**Ceiling: a single 1-for-1 tops out near +3.1 wins, and only for the best player alive; a programme of three reaches +3.2.** Anything pitched above that is wrong. Variance is third-order.

# Consolidation is not the lever

**Body count is the price.** Same star coming back, N-for-1: **+3.11 → +2.03 → +0.73 → +0.10 → −1.16** at N = 1/2/3/4/5. The 5-for-1 is a clear loss *with the best player in the league incoming*.

- **Splitting a consolidation into separate 1-for-1s is worth 1.2× at N=2 and >4× at N=3** at equal BASE paid out.
- **Cheapest wins are at the bottom.** Three sub-replacement bodies → three 26-rate bodies @76 GP = **+1.63**, roughly matching a 1-for-1 for a 45 (+1.76) at **5–8× less BASE on the incoming side** (~592 against 3,000–5,000). ⚠️ The remaining sub-replacement group tops out near 500 BASE for any three, so the multiple is larger and the deal *harder* to make.
- **GP is as important as rate.** A 55 @40 GP bought 3-for-1 is **−1.14**; a 40 @78 GP bought 1-for-1 is **+1.63**.
- **The price is structural, not a backfill effect.** There is **no backfill at all before the September auction** — the pool is locked and we are 28/28. Backfill grade moves break-evens ≤4.3 rate points and flips no sign.
- ⚠️ Suggs/Coby/Turner/Poeltl/Reid are the study's **filler**, held fixed so body count is the only variable — not a bucket, not a send list. Buckets: `evals/teams/my-team/My Team.md`.

# Break-evens

Incoming rate for an N-for-1 to be PF-neutral. **The row you pick decides the sign** — match his GP and position. Full grid + refund bracket: `findings.md`.

| roster · incoming shape | 2-for-1 | 3-for-1 | 4-for-1 | 5-for-1 |
|---|---:|---:|---:|---:|
| **38** · 68 GP forward | 37.6 | 51.4 | 59.6 | 73.3 |
| **38** · 65 GP center | 41.0 | 56.4 | 64.0 | 79.0 |
| **38** · 78 GP forward | 35.0 | 46.9 | 54.0 | 65.3 |
| **28** · 68 GP forward | 37.6 | 53.4 | 63.0 | 79.3 |
| **28** · 65 GP center | 41.8 | 59.4 | 68.2 | 86.2 |
| **28** · 78 GP forward | 34.4 | 48.2 | 56.6 | 70.2 |

Only two roster sizes exist: **28 today, 38 from Sept '26.** **Cap at 3-for-1, and only out of genuine dregs** — a rate-12.9 + 29.2 + 18.2 trio breaks even at **30.6**, which the 61–96 board band supplies; one out of the filler five is not purchasable at any price.

# Is the incoming rate even purchasable?

| board rank | 1-12 | 13-24 | 25-36 | 37-60 | 61-96 | 97-150 | 151-250 | 251-456 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| median FPts/G | 47.8 | 39.0 | 38.1 | 35.7 | 30.7 | 27.5 | 22.8 | 15.7 |

**Only 8 players cleared 45 FPts/G at 30+ GP last season — 3 cleared 50, one cleared 60.** So the 4- and 5-for-1 break-evens are **structurally unavailable at any price**, independently of the win table. The board discounts age and the format pays rate (LeBron 152nd at 39.9), but **nothing here measures an age curve — quote no aging term and no horizon.**

# Valuation formula

**`(rate − R) × GP ÷ K` = wins per 20 matchups, for a 1-for-1 only.** `R` = **17.1** at 38 bodies, **15.1** at 28. Per slot group on the padded 38: guard **18.8** · forward **17.1** · center **19.9**; `K` ≈ 780 for all three. A single `R` is 2.9 rate points wrong end to end.

⚠️ **A diagnostic on the sim, not a valuation layer.** Against sim 1-for-1s it over-predicts by a **median +51%** (worst +178%), or **+38% / +138%** with per-position `R`, and is least trustworthy on low-rate/low-GP players. The error is an **offset, not a scale** — no multiplier converts formula to sim, and per-position `R` still does not fix the top-5 order. **Decide with `sim.py players`** (`Eval Definitions §Δw`).

Value in rate is **linear above ~30** (~52 PF per rate point on a 68-GP body); the convexity below 30 is what makes the formula unusable down there.

# GP is the dominant input — and one season of it is enough

```
GP = 25.7 + 0.368 × last season's GP + 0.432 × min(last season's FPts/G, 30)
```

Applied by `our_roster` to **both sides of any trade**, so a counterparty's injured star cannot be priced at his worst season while ours ride forward.

- **One season beats a flat prior; more history does not add; age never helps** — keep age out of GP, and no report here measures an age curve.
- **The whole exercise is worth ~4% of the error.** GP is a defensible input, not a precise one: **never argue a trade on a few games of GP.**
- ⚠️ **Over-shrunk** (sd 9.8 against a true 20.5, Spearman 0.35): an iron-man reads too low, a fragile starter too high. **Censored** — a whole missed season is absent from the pool, so every figure is expected GP *given he plays at all*.
- ⚠️ **Weakest on a fragment season**, where the fragment is the model's only evidence. Flag those rows; don't patch them. External GP feeds do not fix any of this.
- Persistence is low: everyone converges to **~59–62 GP**.

# Durability

**No format-derived injury adjustment.** With foreknowledge the format is exactly proportional (GP-elasticity 1). Onset-corrected cost across the whole 38-man roster: **−0.12 / −0.30 / −0.48 wins** at 10 / 25 / 40% of blocks absent; **≤2% of a player's value**, flat in GP. **Burstiness is EV-neutral over a season** — but not over a bracket window (§*Bracket weeks*).

# The slot-fill curve

At 38 bodies a 7-game night still fills only **8.88 of 9** slots, and 9.00 does not arrive until **11 games**. **107 of 1,179 slot-nights unfilled (9.0%)**, and the constraint is concentrated: **14 nights (11%) carry 68% of the loss, 32 nights (24%) carry 89%.**

- **Heavy night: only rate matters.** **Light night** (≤5 NBA games, **32** of 131 scored, 14 at ≤3): nearly everyone available starts, so it is **presence, not rate**.
- **Surplus is therefore the middle of the roster** — not the top, not the tail.
- Positions rarely bind: 1.8% of slot-nights lost to no legal slot against 7.3% to no body at all.
- ⚠️ **No "season loss = N PF" figure is defensible** — the same slots price at 900–1,800 PF depending on an assumed price. Quote the share columns.

# Positional premium — a fact about *our* roster, not the format

Added body of identical rate, versus that rate as a guard:

| rate | 25 | 35 | 45 |
|---|---:|---:|---:|
| forward vs guard | **+12%** | +11% | +7% |
| center vs guard | **−16%** | −7% | −5% |

~**+0.08 wins** on a marginal body — worth pricing, not worth building around, and it shrinks as rate rises. **Center is a discount, not a wash.** ⚠️ Purely a function of our current shape (15 pure guards for ≤5 slots, 9 pure centers for 3, on the padded 38); it disappears when that changes.

# Light-night coverage — what steering the auction buys

Steering the seven September auction bodies on schedule is worth **+0.095 ± 0.015 wins**, against not caring. ⚠️ That sits **at** the ~0.1-win floor, so the upside does not carry the rule — **the downside does**: the same seven stacked on one schedule is **−0.602**, and ignoring schedule is itself a lottery (20 random draws span −0.33 to −0.02, sd 0.098).

- **A free acquisition-time tiebreak and nothing more** — it only orders bodies already tied on `(rate − R) × GP`. **Never pay a pick, a body or a wide rate gap for a schedule.**
- **Threshold ~2.1 rate points at auction grade (8–14 FPts)**, sliding to **~1.05 at rate 40**. Quote the row matching the body; never carry 2.1 onto a real producer.
- **What pays is distinct light nights *covered*, never a body's own count.** It **saturates at six picks** (32 of 32 nights); cumulative +0.016 / +0.079 / +0.108 / +0.176 / +0.206 / **+0.222** / +0.212 at k=1..7 — the seventh buys nothing. Steer all six; four is where the attention pays.
- Deepest light-night schedules: **LAC · OKC (12)**, then HOU/LAL/SA/UTAH (10); shallowest **BKN · CHI · POR (3)**. Total games barely vary — this buys light nights, not games.
- ⚠️ Measured on the '25-26 calendar against our current 22-team spread, where our other 31 bodies already reach 31 of the 32 nights. **Re-cut; never carry forward.**

# Bracket weeks — what a game is worth once the bracket starts

| band | rounds | P(title) | by seed | one bracket game × one regular game |
|---|---:|---:|---:|---:|
| 1–2 | 2 | 0.569 | 0.523–0.616 | **16.1** |
| 3–4 | 3 | 0.378 | 0.310–0.446 | **11.3** |
| 5–8 | 4 | 0.323 | 0.284–0.359 | **8.8** |

We project **1st of 12** on season PF (30,231), so **band 1–2 applies to us**. Per-player `ΔP(title)` tops out at **+15.6 percentage points** (Amen Thompson, band 1–2).

- ⚠️ **It scales with `P(title)`, so it is a fact about the roster loaded, not the format** — a rebuilding team reads **0.0–1.3×**. **Re-run per roster**, and never sum, net or convert `ΔP(title)` against `Δw` (`Eval Definitions §ΔP(title)`).
- ⚠️ **A band is a seed range and the draw splits it** (6 and 7 sit on the 2-seed's side, 5 and 8 on the 1-seed's). A call that turns on the spread needs the seed.
- **A bracket week is not four games for everybody.** W22+W23 runs **8 games for 11 teams and 6 for 5** — a third of a bracket week between otherwise identical bodies, and nothing in a season rate says so.

# Title odds — the season simulated end to end

`sim.py title`, 2026-08-13. §*Bracket weeks* prices a round **given** a seed; this earns it first, so **`P(title)` is unconditional and the twelve teams sum to 1.**

| | us | Yao | Jesus | Pascals | rest |
|---|---:|---:|---:|---:|---:|
| **P(title)** | **0.652** | 0.176 | 0.116 | 0.029 | ≤0.012 |
| expected wins of 19 | 16.2 | 14.0 | 13.0 | 11.5 | |

- **We take the 1-seed in 81% of seasons** and make the bracket in ~100%.
- **Having to earn the seed costs us 5.8 points** against being handed the 1-seed (0.710 → 0.652), and pays every team below.
- ⚠️ **A third currency.** Never summed, netted or converted against `Δw` or banded `ΔP(title)` — it carries the seeding channel those two exist to keep apart (`Eval Definitions §ΔP(title)`).
- ⚠️ **Matchups are decided on the wire's spread (0.1005), not the engine's own draws (0.040)** — availability is all that moves in the engine. Calibration: simulated standings spread 4.36 against the wire's 4.17.
- ⚠️ **The 19-period schedule is last season's shape, re-dealt every season.** Next season's does not exist yet.

# Sept '26 expansion

- Filling 28 → 38 with auction-grade bodies: **+1,219 PF (+2.04 wins), free** — more than most consolidation trades, and the cheapest wins available.
- **Breadth stops differentiating** once every team refills from the same auction; hoarding filler now buys nothing durable.
- **A traded-away body cannot be replaced** before then: a 3-for-1 today leaves 36 players and 2 dead slots.
