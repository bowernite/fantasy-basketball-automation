# Team projections — where each team finishes, and where its picks land

Evaluated **2026-09-28** (year-1 PF and title odds re-run after Hlina's 2.09 ↔ LaRavia + Drummond, 485845, assumed through; projections from the 9/28 refresh, boards 9/12; Sharpe `gp=0` and Williams `gp=10` overrides on our roster). Keyed to who **produces** a pick, not who holds it. Slots written `1.01`–`1.12`.

| Column | Source |
| --- | --- |
| **'26-27** | `sim.py horizon` '26-27 block (`sim.team_levels()` projected season PF rank) — all 12 roster files, padded to 38, same engine. Re-run before treating as live. **PF order is the finish prior** (draft uses record rank; H2H can move a team ± a few). |
| **P(title)** | `sim.py title` — same 12 files, seed simulated, twelve sum to 1. This year only. Re-run before treating as live. |
| **'27-28 · '28-29** | Judgment on age / window — young cores climb, star-age cliffs fall. ±2–3 ranks of noise. No multi-year sim exists. |
| **Sept slots** | Top-4 finish → `13 − rank` exact. Bottom-8 → lottery **prior** band only (`league-info`). |

Rosters include the Matthew, Henry, Josh and Chris (Fox, 9/28) deals, plus both Hlina deals assumed through (`Pending Trades.md`). The 2.09 deal costs Hlina ~0.7 W and ~5 pts of P(title) (joint sim); with the 9/28 projection refresh he drops 2nd → 5th on PF, 9 PF behind Josh (a tie).

## Master table — projected finish → pick slot

| Team         | '26-27 | Sept '27          | '27-28 | Sept '28          | '28-29 | Sept '29          |
| ------------ | ------ | ----------------- | ------ | ----------------- | ------ | ----------------- |
| Brett (us)   | **1**  | **1.12**          | **2**  | **1.11**          | **4**  | **1.09**          |
| Michael      | 2      | 1.11              | 8      | 1.03–1.09 (prior) | 11     | 1.01–1.08 (prior) |
| Brian        | 3      | 1.10              | 3      | 1.10              | 7      | 1.03–1.10 (prior) |
| Josh         | 4      | 1.09              | 7      | 1.03–1.10 (prior) | 9      | 1.02–1.09 (prior) |
| Hlina        | 5      | 1.05–1.11 (prior) | 1      | 1.12              | 3      | 1.10              |
| Mitch        | 6      | 1.05–1.11 (prior) | 4      | 1.09              | 2      | 1.11              |
| Joe          | 7      | 1.03–1.10 (prior) | 10     | 1.02–1.09 (prior) | 8      | 1.03–1.09 (prior) |
| Todd         | 8      | 1.03–1.09 (prior) | 11     | 1.01–1.08 (prior) | 10     | 1.02–1.09 (prior) |
| Henry        | 9      | 1.02–1.09 (prior) | 6      | 1.05–1.11 (prior) | 5      | 1.04–1.10 (prior) |
| Chris        | 10     | 1.02–1.09 (prior) | 12     | 1.01–1.07 (prior) | 12     | 1.01–1.07 (prior) |
| Matthew      | 11     | 1.01–1.08 (prior) | 5      | 1.05–1.11 (prior) | 1      | 1.12              |
| Jon          | 12     | 1.01–1.07 (prior) | 9      | 1.02–1.09 (prior) | 6      | 1.05–1.11 (prior) |

## Year-1 sim

Measured 2026-09-28. PF from `sim.py horizon` ('26-27); wins from `sim.py title` (19 matchups, 20k seasons). Table sorted by PF; wins can diverge ± a rank (Brian **12.8 W** at #3 PF, ahead of Michael **12.5** at #2; Josh and Hlina level at **11.8**).

| rank | team | PF | wins |
| ---: | --- | ---: | ---: |
| 1 | Brett (us) | **32,138** | **16.2** |
| 2 | Michael | 30,677 | 12.5 |
| 3 | Brian | 30,211 | 12.8 |
| 4 | Josh | 30,141 | 11.8 |
| 5 | Hlina | 30,132 | 11.8 |
| 6 | Mitch | 29,770 | 10.8 |
| 7 | Joe | 29,073 | 10.1 |
| 8 | Todd | 27,682 | 7.4 |
| 9 | Henry | 27,087 | 6.6 |
| 10 | Chris | 26,181 | 5.3 |
| 11 | Matthew | 25,853 | 4.8 |
| 12 | Jon | 25,584 | 4.0 |

## Title odds (this year)

`sim.py title`, 2026-09-28. Unconditional `P(title)` — regular season, then the bracket. Not the PF-rank finish prior above.

| Team | P(title) |
| --- | ---: |
| Brett (us) | **56.1%** |
| Michael | 12.8% |
| Josh | 7.8% |
| Mitch | 7.2% |
| Hlina | 7.1% |
| Brian | 6.1% |
| Joe | 2.7% |
| Todd | 0.1% |
| Henry | 0.0% |
| Chris | 0.0% |
| Matthew | 0.0% |
| Jon | 0.0% |

## Years 2–3 (judgment)

| Arc                | Teams                                  | Read                                                                                                                                                                                  |
| ------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Climb**          | Hlina · Matthew · Mitch · Henry · Jon  | Young cores (μ age top-12 ≈ 23–25). Matthew / Mitch / Hlina own the late window; Henry and Jon step up as depth arrives.                                                               |
| **Hold then fade** | Brett · Brian                          | Contending now. Brett's Butler/Kyrie age out by '28-29; Fox (29, from Chris 9/28) holds the guard line through '27-28. Brian rides Jokic through '27-28 then slips.                      |
| **Cliff**          | Josh · Michael · Chris                 | Star age (Embiid/KAT; Harden/Siakam; LeBron/KD/Curry). Josh gave up Bridges/Gordon/Collins for Kawhi+Turner — short-term bump, long-term age cliff steepens. Chris sold Fox for Middleton + two '27 2nds (9/28): year-1 PF 26,181 and the cliff steepens. |
| **Flat**           | Joe · Todd                             | Mid/bottom without a clear climb or cliff.                                                                                                                                            |

# Notes

- Draft / lottery rules: `league-info`. Slot pricing: `eval-pick`.
- Team eval pick tables that still cite the 2026-07-29 ranks are stale until re-modelled off this file.
