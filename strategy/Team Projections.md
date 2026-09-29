# Team projections — where each team finishes, and where its picks land

Evaluated **2026-09-29**, post-draft: rosters re-cut 9/29 (rookie draft, FA auction and every 9/26–9/28 trade on the wire), F/C flex, projections from the 9/29 refresh, Sharpe `gp=0` and Williams `gp=10` overrides. Keyed to who **produces** a pick, not who holds it. Slots written `1.01`–`1.12`; every round uses the same slot (`league-info` §Drafting).

| Column | Source |
| --- | --- |
| **'26-27** | `sim.py horizon` '26-27 block (`sim.team_levels()` projected season PF rank) — all 12 roster files, padded to 38, same engine. Re-run before treating as live. **PF order is the finish prior** (draft uses record rank; H2H can move a team ± a few). |
| **P(title)** | `sim.py title` — same 12 files, seed simulated, twelve sum to 1. This year only. Re-run before treating as live. |
| **'27-28 +** | Pending — `sim.py future` (see [Years 2+](#years-2)). |
| **Sept slots** | Top-4 finish → `13 − rank` exact. Bottom-8 → lottery **prior** band only (`league-info`). |

## Master table — projected finish → pick slot

| Team       | '26-27 | Sept '27          | '27-28 + |
| ---------- | ------ | ----------------- | -------- |
| Brett (us) | **1**  | **1.12**          | pending  |
| Michael    | 2      | 1.11              | pending  |
| Brian      | 3      | 1.10              | pending  |
| Josh       | 4      | 1.09              | pending  |
| Hlina      | 5      | 1.05–1.11 (prior) | pending  |
| Mitch      | 6      | 1.05–1.11 (prior) | pending  |
| Joe        | 7      | 1.03–1.10 (prior) | pending  |
| Todd       | 8      | 1.03–1.09 (prior) | pending  |
| Henry      | 9      | 1.02–1.09 (prior) | pending  |
| Chris      | 10     | 1.02–1.09 (prior) | pending  |
| Matthew    | 11     | 1.01–1.08 (prior) | pending  |
| Jon        | 12     | 1.01–1.07 (prior) | pending  |

Two coin flips on the slot map, both from wins diverging from PF:

- **Michael / Brian (1.11 vs 1.10):** Brian projects **13.2 W** at #3 PF, ahead of Michael's **12.8** at #2. Draft order follows record, so Brian at 1.11 is at least as likely.
- **Top-4 cut (Josh / Hlina):** Hlina sits 50 PF behind Josh (30,040 vs 30,090) at 11.7 W vs 11.8. Josh's 1.09 vs Hlina's lottery prior is a coin flip.

## Year-1 sim

Measured 2026-09-29. PF from `sim.py horizon` ('26-27); wins from `sim.py title` (19 matchups, 20k seasons). Sorted by PF.

| rank | team | PF | wins |
| ---: | --- | ---: | ---: |
| 1 | Brett (us) | **32,166** | **16.2** |
| 2 | Michael | 30,703 | 12.8 |
| 3 | Brian | 30,306 | 13.2 |
| 4 | Josh | 30,090 | 11.8 |
| 5 | Hlina | 30,040 | 11.7 |
| 6 | Mitch | 29,882 | 10.9 |
| 7 | Joe | 28,640 | 9.4 |
| 8 | Todd | 27,866 | 7.6 |
| 9 | Henry | 26,759 | 6.1 |
| 10 | Chris | 26,327 | 5.6 |
| 11 | Matthew | 26,096 | 5.1 |
| 12 | Jon | 25,357 | 3.6 |

## Title odds (this year)

`sim.py title`, 2026-09-29. Unconditional `P(title)` — regular season, then the bracket. Not the PF-rank finish prior above. Ours: 1-seed 85%, `P(title | 1-seed)` 56%.

| Team | P(title) |
| --- | ---: |
| Brett (us) | **55.5%** |
| Michael | 13.2% |
| Josh | 9.3% |
| Brian | 7.4% |
| Mitch | 6.9% |
| Hlina | 6.0% |
| Joe | 1.4% |
| Todd | 0.2% |
| Henry | 0.0% |
| Chris | 0.0% |
| Matthew | 0.0% |
| Jon | 0.0% |

## Years 2+

**Pending.** To be filled from `sim.py future` (forward-projected rosters, 4 rookies per team per year from '27) once that subcommand lands — run it per its own instructions. Until then there is no current multi-year read: the 9/28 judgment arcs predate the draft, the auction and the 9/28 trades, and were dropped rather than carried stale. Do not substitute `sim.py horizon`'s '27-28 / '28-29 blocks — same bodies, no picks, no trades.

# Notes

- Draft / lottery rules: `league-info`. Slot pricing: `eval-pick`.
