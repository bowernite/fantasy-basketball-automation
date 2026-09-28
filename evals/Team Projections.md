# Team projections — where each team finishes, and where its picks land

Evaluated **2026-09-28** (year-1 PF and title odds re-run after Chris's Fox trade, 485835; projections + boards from the 9/12 refresh; Sharpe `gp=0` and Williams `gp=10` overrides on our roster). Keyed to who **produces** a pick, not who holds it. Slots written `1.01`–`1.12`.

| Column | Source |
| --- | --- |
| **'26-27** | `sim.py horizon` '26-27 block (`sim.team_levels()` projected season PF rank) — all 12 roster files, padded to 38, same engine. Re-run before treating as live. **PF order is the finish prior** (draft uses record rank; H2H can move a team ± a few). |
| **P(title)** | `sim.py title` — same 12 files, seed simulated, twelve sum to 1. This year only. Re-run before treating as live. |
| **'27-28 · '28-29** | Judgment on age / window — young cores climb, star-age cliffs fall. ±2–3 ranks of noise. No multi-year sim exists. |
| **Sept slots** | Top-4 finish → `13 − rank` exact. Bottom-8 → lottery **prior** band only (`league-info`). |

Rosters include the Matthew, Henry, Josh and Chris (Fox, 9/28) deals, plus Hlina's assumed through (`Pending Trades.md`). The Fox trade moved no '26-27 rank: we stay 1st, Chris stays 10th.

## Master table — projected finish → pick slot

| Team         | '26-27 | Sept '27          | '27-28 | Sept '28          | '28-29 | Sept '29          |
| ------------ | ------ | ----------------- | ------ | ----------------- | ------ | ----------------- |
| Brett (us)   | **1**  | **1.12**          | **2**  | **1.11**          | **4**  | **1.09**          |
| Hlina        | 2      | 1.11              | 1      | 1.12              | 3      | 1.10              |
| Michael      | 3      | 1.10              | 8      | 1.03–1.09 (prior) | 11     | 1.01–1.08 (prior) |
| Josh         | 4      | 1.09              | 7      | 1.03–1.10 (prior) | 9      | 1.02–1.09 (prior) |
| Brian        | 5      | 1.05–1.11 (prior) | 3      | 1.10              | 7      | 1.03–1.10 (prior) |
| Mitch        | 6      | 1.05–1.11 (prior) | 4      | 1.09              | 2      | 1.11              |
| Joe          | 7      | 1.03–1.10 (prior) | 10     | 1.02–1.09 (prior) | 8      | 1.03–1.09 (prior) |
| Henry        | 8      | 1.03–1.09 (prior) | 6      | 1.05–1.11 (prior) | 5      | 1.04–1.10 (prior) |
| Todd         | 9      | 1.02–1.09 (prior) | 11     | 1.01–1.08 (prior) | 10     | 1.02–1.09 (prior) |
| Chris        | 10     | 1.02–1.09 (prior) | 12     | 1.01–1.07 (prior) | 12     | 1.01–1.07 (prior) |
| Matthew      | 11     | 1.01–1.08 (prior) | 5      | 1.05–1.11 (prior) | 1      | 1.12              |
| Jon          | 12     | 1.01–1.07 (prior) | 9      | 1.02–1.09 (prior) | 6      | 1.05–1.11 (prior) |

## Year-1 sim

Measured 2026-09-28. PF from `sim.py horizon` ('26-27); wins from `sim.py title` (19 matchups, 20k seasons). Table sorted by PF; wins can diverge ± a rank (Brian **12.5 W** at #5 PF, ahead of Josh **11.9** at #4 and level with Hlina).

| rank | team | PF | wins |
| ---: | --- | ---: | ---: |
| 1 | Brett (us) | **31,816** | **15.6** |
| 2 | Hlina | 30,667 | 12.5 |
| 3 | Michael | 30,551 | 12.3 |
| 4 | Josh | 30,231 | 11.9 |
| 5 | Brian | 30,157 | 12.5 |
| 6 | Mitch | 29,893 | 10.9 |
| 7 | Joe | 29,029 | 9.9 |
| 8 | Henry | 27,833 | 7.7 |
| 9 | Todd | 27,582 | 7.3 |
| 10 | Chris | 26,284 | 5.4 |
| 11 | Matthew | 25,581 | 4.3 |
| 12 | Jon | 25,455 | 3.7 |

## Title odds (this year)

`sim.py title`, 2026-09-28. Unconditional `P(title)` — regular season, then the bracket. Not the PF-rank finish prior above.

| Team | P(title) |
| --- | ---: |
| Brett (us) | **50.4%** |
| Hlina | 13.9% |
| Michael | 11.3% |
| Josh | 8.4% |
| Mitch | 7.8% |
| Brian | 5.6% |
| Joe | 2.3% |
| Henry | 0.1% |
| Todd | 0.1% |
| Chris | 0.0% |
| Matthew | 0.0% |
| Jon | 0.0% |

## Years 2–3 (judgment)

| Arc                | Teams                                  | Read                                                                                                                                                                                  |
| ------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Climb**          | Hlina · Matthew · Mitch · Henry · Jon  | Young cores (μ age top-12 ≈ 23–25). Matthew / Mitch / Hlina own the late window; Henry and Jon step up as depth arrives.                                                               |
| **Hold then fade** | Brett · Brian                          | Contending now. Brett's Butler/Kyrie age out by '28-29; Fox (29, from Chris 9/28) holds the guard line through '27-28. Brian rides Jokic through '27-28 then slips.                      |
| **Cliff**          | Josh · Michael · Chris                 | Star age (Embiid/KAT; Harden/Siakam; LeBron/KD/Curry). Josh gave up Bridges/Gordon/Collins for Kawhi+Turner — short-term bump, long-term age cliff steepens. Chris sold Fox for Middleton + two '27 2nds (9/28): year-1 PF drops to 26,284 and the cliff steepens. |
| **Flat**           | Joe · Todd                             | Mid/bottom without a clear climb or cliff.                                                                                                                                            |

# Notes

- Draft / lottery rules: `league-info`. Slot pricing: `eval-pick`.
- Team eval pick tables that still cite the 2026-07-29 ranks are stale until re-modelled off this file.
