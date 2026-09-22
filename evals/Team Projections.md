# Team projections — where each team finishes, and where its picks land

Evaluated **2026-09-12** (projections + boards refresh; Sharpe `gp=0` and Williams `gp=10` overrides on our assumed-through roster). Keyed to who **produces** a pick, not who holds it. Slots written `1.01`–`1.12`.

| Column | Source |
| --- | --- |
| **'26-27** | `sim.team_levels()` projected season PF rank — all 12 roster files, padded to 38, same engine. Re-run before treating as live. **PF order is the finish prior** (draft uses record rank; H2H can move a team ± a few). |
| **P(title)** | `sim.py title` — same 12 files, seed simulated, twelve sum to 1. This year only. Re-run before treating as live. |
| **'27-28 · '28-29** | Judgment on age / window — young cores climb, star-age cliffs fall. ±2–3 ranks of noise. No multi-year sim exists. |
| **Sept slots** | Top-4 finish → `13 − rank` exact. Bottom-8 → lottery **prior** band only (`league-info`). |

Assumed-through overlays on disk (`Pending Trades.md`): Matthew package, Henry Hunter, **Josh Kawhi + Turner ↔ Bridges + Gordon + Collins**, **Hlina Duren ↔ Green + Camara + Smith**.

## Master table — projected finish → pick slot

| Team                        | '26-27 | Sept '27          | '27-28 | Sept '28          | '28-29 | Sept '29          |
| --------------------------- | ------ | ----------------- | ------ | ----------------- | ------ | ----------------- |
| Bathroom club (us)          | **1**  | **1.12**          | **2**  | **1.11**          | **4**  | **1.09**          |
| Matthew the Apostle         | 2      | 1.11              | 1      | 1.12              | 3      | 1.10              |
| Pascals of Pangea           | 3      | 1.10              | 8      | 1.03–1.09 (prior) | 11     | 1.01–1.08 (prior) |
| Jesus Christ and Disciples  | 4      | 1.09              | 7      | 1.03–1.10 (prior) | 9      | 1.02–1.09 (prior) |
| Yao Ming Dynasty            | 5      | 1.05–1.11 (prior) | 3      | 1.10              | 7      | 1.03–1.10 (prior) |
| The Don                     | 6      | 1.05–1.11 (prior) | 4      | 1.09              | 2      | 1.11              |
| The Gutes of Gotland        | 7      | 1.03–1.10 (prior) | 10     | 1.02–1.09 (prior) | 8      | 1.03–1.09 (prior) |
| Mongol Khans                | 8      | 1.03–1.09 (prior) | 6      | 1.05–1.11 (prior) | 5      | 1.04–1.10 (prior) |
| The Han Dybantsy            | 9      | 1.02–1.09 (prior) | 11     | 1.01–1.08 (prior) | 10     | 1.02–1.09 (prior) |
| King Christopher of Bavaria | 10     | 1.02–1.09 (prior) | 12     | 1.01–1.07 (prior) | 12     | 1.01–1.07 (prior) |
| Pharaoh Mattankhamun-Ra     | 11     | 1.01–1.08 (prior) | 5      | 1.05–1.11 (prior) | 1      | 1.12              |
| SGA-the-Great               | 12     | 1.01–1.07 (prior) | 9      | 1.02–1.09 (prior) | 6      | 1.05–1.11 (prior) |

## Year-1 sim

Measured 2026-09-12, overlay on disk. PF from `sim.team_levels()`; record from `sim.py title` (19 matchups, 20k seasons, wins rounded). Sleeper/GP refresh; Sharpe `gp=0` and Williams `gp=10` on our roster. Table sorted by PF; record can diverge ± a rank (Yao **13–6** at #5 PF, ahead of Jesus **12–7** at #4).

| rank | team | PF | record |
| ---: | --- | ---: | ---: |
| 1 | Bathroom club (us) | **31,366** | **15–4** |
| 2 | Matthew the Apostle | 30,956 | 13–6 |
| 3 | Pascals of Pangea | 30,552 | 12–7 |
| 4 | Jesus Christ and his Disciples | 30,246 | 12–7 |
| 5 | Yao Ming Dynasty | 30,152 | 13–6 |
| 6 | The Don | 30,017 | 11–8 |
| 7 | The Gutes of Gotland | 29,029 | 10–9 |
| 8 | Mongol Khans Freak Militia | 27,870 | 8–11 |
| 9 | The Han Dybantsy | 27,581 | 7–12 |
| 10 | King Christopher of Bavaria | 26,985 | 7–12 |
| 11 | Pharaoh Mattankhamun-Ra | 25,581 | 4–15 |
| 12 | Shai Gilgeous-Alexander the Great | 25,454 | 4–15 |

## Title odds (this year)

`sim.py title`, 2026-09-12. Unconditional `P(title)` — regular season, then the bracket. Not the PF-rank finish prior above. All assumed-through overlays on disk (Matthew, Josh, Hlina).

| Team | P(title) |
| --- | ---: |
| Bathroom club (us) | **43.1%** |
| Matthew the Apostle | 18.9% |
| Pascals of Pangea | 11.5% |
| The Don | 9.4% |
| Jesus Christ and Disciples | 8.6% |
| Yao Ming Dynasty | 6.0% |
| The Gutes of Gotland | 2.3% |
| Mongol Khans | 0.2% |
| The Han Dybantsy | 0.1% |
| King Christopher of Bavaria | 0.0% |
| Pharaoh Mattankhamun-Ra | 0.0% |
| SGA-the-Great | 0.0% |

## Years 2–3 (judgment)

| Arc                | Teams                                      | Read                                                                                                                                                                                                      |
| ------------------ | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Climb**          | Matthew · Pharaoh · The Don · Mongol · SGA | Young cores (μ age top-12 ≈ 23–25). Pharaoh / Don / Matthew own the late window; Mongol and SGA step up as depth arrives.                                                                                 |
| **Hold then fade** | Bathroom · Yao                             | Contending now. Bathroom's Kawhi/Butler/Kyrie age out by '28-29; Josh overlay trades Kawhi for Bridges/Gordon/Collins depth this year. Yao rides Jokic through '27-28 then slips.                         |
| **Cliff**          | Jesus · Pascals · King Christopher         | Star age (Embiid/KAT; Harden/Siakam; LeBron/KD/Curry). Josh gave up Bridges/Gordon/Collins for Kawhi+Turner — short-term bump, long-term age cliff steepens. King Christopher's year-1 PF is a last gasp. |
| **Flat**           | Gutes · Han                                | Mid/bottom without a clear climb or cliff.                                                                                                                                                                |

# Notes

- Draft / lottery rules: `league-info`. Slot pricing: `eval-pick`.
- Team eval pick tables that still cite the 2026-07-29 ranks are stale until re-modelled off this file.
