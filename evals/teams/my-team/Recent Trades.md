# Recent trades — Jul–Sep '26

Our four big numbers (`trades` §The big numbers). `ΔBASE` is the default-`a` point (`Eval Definitions §BASE`); pick-slot ranges use the midpoint of the published bound. Formula `Δw` is the league curve (`Eval Definitions §Δw`). Formula `Δw` recut 2026-09-03 (league curve). `Δw (them)` only for Hlina and Josh (`trades` §Competitors). Picks are BASE-only.

Hlina deal assumed through (`Pending Trades.md`). Rows do not sum (formula `Δw` does). Season/title simmed 9/2/26 · formula `Δw` recut 9/3/26.

## Joint — before all six vs after (today)

Sharpe `GPp` = 0 (`overrides-2026.json`).

| | ΔBASE | Δw | Δw (season) | ΔP(title) |
| --- | ---: | ---: | ---: | ---: |
| All six | **+2,892** | **+4.28** | **+2.51** | **+37.7** |

Before `P(title)` 9.2% → after **47.0%** (`Ours.team.md`).

## Now — undo on today's roster

Reverse the deal, flip signs. Sharpe at 0. Same boards/projections as the joint.

| When         | With    | Out               | In                                     |      ΔBASE |        Δw | Δw (season) | ΔP(title) | Δw (them) |
| ------------ | ------- | ----------------- | -------------------------------------- | ---------: | --------: | ----------: | --------: | --------: |
| 7/29         | Mitch   | ('26 1.09)        | Williams+('27 2nd Don)+('27 2nd Chris) | **+1,480** | **+0.79** |   **+0.26** |  **+6.9** |         — |
| 7/31         | Matthew | James+Maluach     | Walker+Queta+('28 3rd Pharaoh)         |   **+425** | **+0.75** |   **+0.64** |  **+6.7** |         — |
| 8/13         | Henry   | Holmes+('26 3.09) | Hunter+('28 3rd Henry)                 |   **+310** | **+0.24** |   **+0.04** |  **+1.2** |         — |
| 8/13         | Matthew | Amen              | Murray+Sharpe+Eason +Vassell+Kuminga   |   **+455** | **+0.54** |       -0.25 |      -3.8 |         — |
| 9/22         | Josh    | Kawhi+Turner      | Bridges+Gordon+Collins                 |       -180 | **+0.42** |   **+0.17** |  **+4.5** | **-0.42** |
| 9/2 assumed  | Hlina   | Duren             | Green+Camara+Smith                     |   **+402** | **+0.99** |   **+0.35** | **+10.2** | **-0.99** |

Amen isolation is negative on season/title because Sharpe is OFS and the other five deals already filled those slots.

## At the time — roster as it stood

Deals applied in order on the pre-window roster (Bagley back for the Mitch cut). Sharpe at **57 GP** (8/27 eval, pre-override). Amen `ΔBASE` **+242** is the 8/13 board arithmetic (Amen 5,360 vs five 5,602) — not today's boards.

| When         | With    | Out               | In                                     |      ΔBASE |        Δw | Δw (season) | ΔP(title) | Δw (them) |
| ------------ | ------- | ----------------- | -------------------------------------- | ---------: | --------: | ----------: | --------: | --------: |
| 7/29         | Mitch   | ('26 1.09)        | Williams+('27 2nd Don)+('27 2nd Chris) | **+1,480** | **+0.79** |   **+0.42** |  **+5.7** |         — |
| 7/31         | Matthew | James+Maluach     | Walker+Queta+('28 3rd Pharaoh)         |   **+425** | **+0.75** |   **+1.03** |  **+7.9** |         — |
| 8/13         | Henry   | Holmes+('26 3.09) | Hunter+('28 3rd Henry)                 |   **+310** | **+0.24** |   **+0.18** |  **+3.8** |         — |
| 8/13         | Matthew | Amen              | Murray+Sharpe+Eason +Vassell+Kuminga   |   **+242** | **+1.15** |   **+0.70** |  **+8.0** |         — |
| 9/22         | Josh    | Kawhi+Turner      | Bridges+Gordon+Collins                 |       -180 | **+0.42** |   **+0.25** |  **+6.5** | **-0.42** |
| 9/2 assumed  | Hlina   | Duren             | Green+Camara+Smith                     |   **+402** | **+0.99** |   **+0.21** |  **+8.8** | **-0.99** |

8/13 HIS on a thinner roster, old method (joint sim as `Δw`, band 1–2 title): `Amen sims.md` **+0.98 / +5.74**. Do not mix columns with this table.
