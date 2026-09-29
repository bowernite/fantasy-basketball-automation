# Team projections

Run 2026-09-29 (see [Notes](#notes)).

## '26-27

| PF rank | Team | PF | Wins | P(title) % | Own Sept '27 slot |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | Brett | **32,172** | **16.2** | **55** | **1.12** |
| 2 | Michael | 30,717 | 12.8 | 15 | 1.11 |
| 3 | Brian | 30,308 | 13.1 | 7 | 1.10 |
| 4 | Josh | 30,100 | 11.8 | 9 | 1.09 |
| 5 | Hlina | 30,029 | 11.7 | 6 | 1.05–1.11 (prior) |
| 6 | Mitch | 29,876 | 10.9 | 7 | 1.05–1.11 (prior) |
| 7 | Joe | 28,671 | 9.4 | 2 | 1.03–1.10 (prior) |
| 8 | Todd | 27,876 | 7.6 | <1 | 1.03–1.09 (prior) |
| 9 | Henry | 26,806 | 6.2 | 0 | 1.02–1.09 (prior) |
| 10 | Chris | 26,327 | 5.6 | 0 | 1.02–1.09 (prior) |
| 11 | Matthew | 26,187 | 5.2 | 0 | 1.01–1.08 (prior) |
| 12 | Jon | 25,384 | 3.6 | 0 | 1.01–1.07 (prior) |

## '27-28 to '32-33, no trades

| Team: PF (k) · mean rank · P(title) % | '26-27 base ◊ | '27-28 | '28-29 | '29-30 | '30-31 † | '31-32 † | '32-33 † | Rookie share † '30-31 / '31-32 / '32-33 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Brett | **31 · 1** | **31 · 2 · 40** | **29 · 4 · 15** | **28 · 6 · 5** | **27 · 7 · 2** | **26 · 8 · 1** | **25 · 8 · 1** | 19 / 30 / 44% |
| Michael | 29 · 2 | 27 · 7 · 3 | 26 · 8 · 1 | 26 · 9 · 1 | 25 · 9 · 1 | 25 · 9 · 1 | 25 · 9 · 1 | 35 / 48 / 60% |
| Brian | 28 · 4 | 27 · 7 · 3 | 27 · 8 · 1 | 26 · 8 · 1 | 25 · 8 · 1 | 25 · 8 · 1 | 25 · 8 · 1 | 29 / 41 / 53% |
| Josh | 28 · 3 | 26 · 8 · 1 | 24 · 10 · <1 | 23 · 11 · <1 | 23 · 11 · <1 | 23 · 11 · 0 | 23 · 10 · <1 | 43 / 61 / 76% |
| Hlina | 28 · 6 | 30 · 3 · 15 | 31 · 3 · 25 | 31 · 3 · 25 | 31 · 3 · 25 | 31 · 3 · 25 | 30 · 3 · 20 | 21 / 25 / 32% |
| Mitch | 28 · 5 | 30 · 3 · 25 | 31 · 3 · 30 | 31 · 3 · 30 | 31 · 3 · 30 | 31 · 3 · 25 | 30 · 3 · 25 | 14 / 19 / 24% |
| Joe | 27 · 7 | 27 · 7 · 4 | 27 · 7 · 4 | 27 · 7 · 3 | 27 · 7 · 2 | 26 · 7 · 2 | 26 · 7 · 2 | 41 / 52 / 62% |
| Todd | 26 · 8 | 27 · 8 · 2 | 27 · 7 · 3 | 27 · 7 · 3 | 27 · 6 · 3 | 27 · 6 · 3 | 27 · 6 · 4 | 32 / 42 / 51% |
| Henry | 25 · 9 | 27 · 8 · 2 | 27 · 7 · 2 | 28 · 6 · 3 | 28 · 6 · 3 | 27 · 6 · 3 | 27 · 6 · 3 | 27 / 36 / 47% |
| Chris | 25 · 10 | 22 · 12 · 0 | 21 · 12 · 0 | 20 · 12 · 0 | 21 · 12 · 0 | 22 · 11 · 0 | 23 · 11 · 0 | 55 / 71 / 82% |
| Matthew | 24 · 11 | 26 · 8 · 2 | 28 · 6 · 5 | 29 · 5 · 10 | 30 · 4 · 15 | 30 · 3 · 20 | 30 · 3 · 20 | 17 / 22 / 27% |
| Jon | 24 · 12 | 27 · 7 · 3 | 29 · 5 · 10 | 30 · 4 · 15 | 30 · 3 · 20 | 30 · 3 · 20 | 30 · 3 · 20 | 28 / 33 / 39% |

# Notes

Inputs: 9/29 rosters (post rookie draft, FA auction and trades), 9/29 projections and boards, pick ledger fetched 9/29 15:00.

**'26-27 table**

- PF: `sim.py horizon`, '26-27 block (projected season PF, every roster padded to 38). Wins (of 19 matchups) and P(title): `sim.py title` (20k seasons). P(title) rounded to the nearest 5 from 10 up, nearest 1 below 10 (`<1` = under 1, 0 stays 0), so the column no longer sums exactly to 100. Ours: 1-seed 85%, P(title | 1-seed) 56%.
- Own Sept '27 slot: the slot of the team's own '27 pick, whoever holds it now. The draft follows record rank, not PF rank (`league-info` §Drafting), so every slot here is a prior. PF ranks 1–4 map to 13 − rank; ranks 5–12 take `horizon`'s hard-coded prior bands (`LOTTERY_PRIOR`; not simmed, source undocumented).
- P(seed 1–4) from `title` (seeds go by record, so ≈ the draft's top-4 cut): Brett 100 · Brian 78 · Michael 76 · Josh 54 · Hlina 49 · Mitch 32 · Joe 10 · Todd 1. Brian projects more wins than Michael (13.1 vs 12.8), so 1.10/1.11 may swap.

**'27-28 to '32-33 table**

- `sim.py future`, 600 paths, seed 1. A "no trades" read, uncalibrated, not a forecast. Its GP basis is the model's forecast (lower than the projections' GP the '26-27 table uses).
- Method: every player follows his own progression path (FP/G, GP, exit). Each offseason: exits leave; a 4-round draft slots each pick by its original team's sampled finish and hands the rookie to the current holder ('30+ picks stay with their team); rookies are fresh paths cloned from the 2026 class at that ordinal; cuts to 38 by BASE (frozen at today's boards) + 300·formula Δw as a proxy for Score; pads with FA filler. The '26-27 schedule repeats every season.
- ◊ `future`'s own '26-27 (PF · mean rank, model GP): the base for reading each team's step into '27-28. Year-1 numbers of record are the '26-27 table; don't compare across the two tables.
- PF is in thousands, rounded to a whole number. Mean rank is the mean PF rank over paths, not record rank; rounded to a whole number. P(title) is rounded to the nearest 5 from 10 up, nearest 1 below 10 (`<1` = under 1), so a season's column no longer sums exactly to 100.
- † Rookie share = share of the team's top-12 FP held by rookies the sim drafted, all clones of the 2026 class. By '30-31 to '32-33 they carry 14–82% of a top 12, so read those seasons as a trend, not a number.
- Seed noise: another seed moves unrounded P(title) ~0.4 points on average, up to ~3 for a favourite, so the rounded figures can shift a step. Same inputs repeat to the digit.
- Known biases:
  - Every class copies 2026's strong top (plus the model's top-5 over-projection), and the '27 top is known to be weak. That inflates teams with low slots, or holding picks from teams that finish low. Hand estimate, not a sim output: ~1–2k PF in '30-31 to '32-33 for Chris and Josh, ~0.5–1k for Michael, Brian and Joe; also Hlina, Jon and Joe in '27-28 via their extra '27 1sts.
  - No trades or FA pickups: aging cores restock only through the draft.
  - Progression pulls high projections toward the mean on top of aging (`sim.py progression` medians by '30-31: Cunningham 47.6 → 43.8, Giddey 42.1 → 36.3 FP/G).
  - Unsized: role vets 29+ run high; BASE never ages; bracket R1 wins don't move the draft cut.
  - Cut proxy: bites in the '27 and '28 offseasons (Jon 3.5 and 1.1 cuts, Brett 2.6 and 2.7, Joe 1.2), so it shapes their '27-28 and '28-29; under 1 cut per team per offseason from '29.
  - Negligible: the reused schedule, and four players with no birthday (Lewis, Ilyasova, Marković, Ishchenko) exiting after '26-27.

**Re-run**

- '26-27: `strategy/lineup-math/run sim.py horizon title` (PF and slots from `horizon`'s '26-27 block only; its later blocks are superseded by `future`).
- '27-28 on: `strategy/lineup-math/run sim.py future` (~1 min). After a trade, injury or projections/boards/BASE refresh, follow `sims` §Future seasons and read `Δ vs last run`.
- Progression medians cited in Notes: `strategy/lineup-math/run sim.py progression`.
- Slot pricing off these finishes: `eval-pick`.
