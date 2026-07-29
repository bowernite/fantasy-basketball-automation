# The Don (Mitch) — dynasty values

**Player values are the blended board rank and nothing else** — no adjustment
for injury, role, team situation or contract. Pick values are the exception:
a pick's slot depends on where its team finishes, so those embed a projection.

**2026-07-29.** Points-format dynasty boards only, blended
**40% Dizzle Points · 35% Hashtag Points · 25% Hashtag crowd**.
Dynatyze is shown for reference but not blended.

Ranks → the 9999 scale via a convex curve zeroed at replacement (~rank 400):
`V(r) = 1.0966 × (10000/(1 + (r/21.4)^1.0276) − 470)`
Where a player is absent from a board, the remaining weights renormalise.

Sources: `dizzle-dynasty`, `hashtag-basketball`, `dynatyze` Skills.

## Players

`dizP` Dizzle Points (10 Jul, 466 deep) · `htP` Hashtag Points (2 Jul, 400) ·
`crd` Hashtag crowd (29 Jul, 759) · `dyn` Dynatyze (29 Jul, top 68).
Lower rank = better. `–` = outside that board, except under `dyn`, where it
means not shown — Dynatyze withholds individual ranks, so absence is not a
statement of value.

| Player | dizP | htP | crd | dyn | **VALUE** |
|---|---:|---:|---:|---:|---:|
| Luka Dončić | 3 | 3 | 6 | 3 | **8902** |
| Cooper Flagg | 5 | 7 | 2 | 5 | **8502** |
| Deni Avdija | 26 | 31 | 21 | 26 | **4401** |
| Franz Wagner | 28 | 34 | 33 | 24 | **3918** |
| Jaren Jackson Jr. | 53 | 37 | 49 | 37 | **2937** |
| Keyonte George | 49 | 47 | 47 | 52 | **2825** |
| Walker Kessler | 47 | 78 | 65 | 54 | **2303** |
| Collin Murray-Boyles | 65 | 86 | 68 | – | **1928** |
| Derik Queen | 86 | 83 | 56 | – | **1839** |
| Reed Sheppard | 88 | 87 | 88 | – | **1570** |
| Mark Williams | 114 | 97 | 121 | – | **1217** |
| Moussa Diabaté | 170 | 140 | 137 | – | **791** |
| Zaccharie Risacher | 235 | 166 | 150 | – | **572** |
| Isaiah Collier | 221 | 190 | 139 | – | **567** |
| Will Riley | 166 | 191 | 354 | – | **472** |
| Nikola Topić | 213 | 334 | 208 | – | **319** |
| Tre Jones | 214 | 366 | 458 | – | **171** |

## Picks

Sept '26 holdings verified against `FetchLeagueDraftBoard`: 1.03 and 2.03 are his
own; 1.04, 1.08, 1.10 and 3.11 were acquired. 3.11 originates from King
Christopher. He holds no third of his own.

Priced 50/50 off Dizzle's pick chart (player-rank equivalence) and the Hashtag
crowd pick bands.

| Pick | Dizzle | crowd | **VALUE** |
|---|---:|---:|---:|
| 1.03 | #20 → 5158 | #40 → 3264 | **4211** |
| 1.04 | #30 → 4025 | #40 → 3264 | **3644** |
| 1.08 | #82 → 1688 | #64 → 2171 | **1930** |
| 1.10 | #112 → 1177 | #111 → 1191 | **1184** |
| 2.03 | #135 → 920 | #144 → 840 | **880** |
| 3.11 | #275 → 226 | #272 → 234 | **230** |

### Future firsts

`evals/team-projections.md` projects him 6th in '26-27 (range 2–8), 4th in
'27-28 and 2nd in '28-29. Only the top 4 make the playoffs; non-playoff slot =
13 − finish.

| Pick | Projected slot | **VALUE** |
|---|---|---:|
| '27 1st | 1.7 (range 1.5–1.12) | **~1450–1950** |
| '28 1st | ~1.10 | **~900–1100** |
| '29 1st | ~1.10 | **~800–1000** |

The '27 range is bracketed by two methods: slot-EV across his projected finish
using Dizzle's pick chart, less a 2027-class discount and time, gives ~1440;
Dynatyze prices `2027 Mid 1st` at board rank #72 → ~1930 all-in. `2027 Early
1st` sits at #41 → ~3200, reached only on a bottom-4 finish. The Hashtag crowd
board prices 2026 bands only.
