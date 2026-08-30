# Team projections — where each team finishes, and where its picks land

Evaluated **2026-08-29**. Keyed to who **produces** a pick, not who holds it. Slots written `1.01`–`1.12`.

| Column | Source |
| --- | --- |
| **'26-27** | `sim.team_levels()` projected season PF rank — all 12 roster files, padded to 38, same engine. Re-run before treating as live. **PF order is the finish prior** (draft uses record rank; H2H can move a team ± a few). |
| **P(title)** | `sim.py title` — same 12 files, seed simulated, twelve sum to 1. This year only. Re-run before treating as live. |
| **'27-28 · '28-29** | Judgment on age / window — young cores climb, star-age cliffs fall. ±2–3 ranks of noise. No multi-year sim exists. |
| **Sept slots** | Top-4 finish → `13 − rank` exact. Bottom-8 → lottery **prior** band only (`league-info`). |

## Master table — projected finish → pick slot

| Team | '26-27 | Sept '27 | '27-28 | Sept '28 | '28-29 | Sept '29 |
| --- | --- | --- | --- | --- | --- | --- |
| Bathroom club (us) | **2** | **1.11** | **2** | **1.11** | **4** | **1.09** |
| Yao Ming Dynasty | **5** | 1.05–1.11 (prior) | **3** | **1.10** | **7** | 1.03–1.10 (prior) |
| Jesus Christ and Disciples | **3** | **1.10** | **7** | 1.03–1.10 (prior) | **9** | 1.02–1.09 (prior) |
| Pascals of Pangea | **4** | **1.09** | **8** | 1.03–1.09 (prior) | **11** | 1.01–1.08 (prior) |
| Matthew the Apostle | **1** | **1.12** | **1** | **1.12** | **3** | **1.10** |
| King Christopher of Bavaria | **10** | 1.02–1.09 (prior) | **12** | 1.01–1.07 (prior) | **12** | 1.01–1.07 (prior) |
| The Gutes of Gotland | **7** | 1.03–1.10 (prior) | **10** | 1.02–1.09 (prior) | **8** | 1.03–1.09 (prior) |
| Mongol Khans | **8** | 1.03–1.09 (prior) | **6** | 1.05–1.11 (prior) | **5** | 1.04–1.10 (prior) |
| The Don | **6** | 1.05–1.11 (prior) | **4** | **1.09** | **2** | **1.11** |
| SGA-the-Great | **12** | 1.01–1.07 (prior) | **9** | 1.02–1.09 (prior) | **6** | 1.05–1.11 (prior) |
| The Han Dybantsy | **9** | 1.02–1.09 (prior) | **11** | 1.01–1.08 (prior) | **10** | 1.02–1.09 (prior) |
| Pharaoh Mattankhamun-Ra | **11** | 1.01–1.08 (prior) | **5** | 1.05–1.11 (prior) | **1** | **1.12** |

## Year-1 sim (PF)

Measured 2026-08-29, overlay on disk, `sim.team_levels()`:

| rank | team | PF |
| ---: | --- | ---: |
| 1 | Matthew the Apostle | **31,450** |
| 2 | Bathroom club (us) | 31,414 |
| 3 | Jesus Christ and his Disciples | 30,568 |
| 4 | Pascals of Pangea | 30,450 |
| 5 | Yao Ming Dynasty | 30,223 |
| 6 | The Don | 30,017 |
| 7 | The Gutes of Gotland | 29,029 |
| 8 | Mongol Khans Freak Militia | 27,795 |
| 9 | The Han Dybantsy | 27,615 |
| 10 | King Christopher of Bavaria | 26,985 |
| 11 | Pharaoh Mattankhamun-Ra | 25,641 |
| 12 | Shai Gilgeous-Alexander the Great | 25,494 |

## Title odds (this year)

`sims/team-projections.json` → `sim.py title`, 2026-08-29. Unconditional `P(title)` — regular season, then the bracket. Not the PF-rank finish prior above.

| Team | P(title) |
| --- | ---: |
| Bathroom club (us) | **32.5%** |
| Matthew the Apostle | 29.4% |
| Jesus Christ and Disciples | 12.7% |
| Pascals of Pangea | 10.5% |
| The Don | 7.8% |
| Yao Ming Dynasty | 5.0% |
| The Gutes of Gotland | 1.9% |
| The Han Dybantsy | 0.1% |
| King Christopher of Bavaria | 0.1% |
| Mongol Khans | 0.0% |
| Pharaoh Mattankhamun-Ra | 0.0% |
| SGA-the-Great | 0.0% |

## Years 2–3 (judgment)

| Arc | Teams | Read |
| --- | --- | --- |
| **Climb** | Matthew · Pharaoh · The Don · Mongol · SGA | Young cores (μ age top-12 ≈ 23–25). Pharaoh / Don / Matthew own the late window; Mongol and SGA step up as depth arrives. |
| **Hold then fade** | Bathroom · Yao | Contending now. Bathroom's Kawhi/Butler/Kyrie age out by '28-29; Yao rides Jokic through '27-28 then slips. |
| **Cliff** | Jesus · Pascals · King Christopher | Star age (Embiid/KAT; Harden/Siakam; LeBron/KD/Curry). King Christopher's year-1 PF is a last gasp. |
| **Flat** | Gutes · Han | Mid/bottom without a clear climb or cliff. |

# Notes

- Draft / lottery rules: `league-info`. Slot pricing: `eval-pick`.
- Team eval pick tables that still cite the 2026-07-29 ranks are stale until re-modelled off this file.
