# Bathroom club — dynasty values

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
| Cade Cunningham | 6 | 6 | 5 | 6 | **8196** |
| Amen Thompson | 18 | 24 | 14 | 20 | **5343** |
| Josh Giddey | 24 | 28 | 44 | 33 | **4090** |
| Jalen Duren | 35 | 36 | 27 | 39 | **3761** |
| Darius Garland | 32 | 43 | 58 | 29 | **3214** |
| Zach Edey | 51 | 61 | 69 | 50 | **2368** |
| Desmond Bane | 57 | 66 | 67 | 48 | **2224** |
| Kawhi Leonard | 68 | 107 | 90 | – | **1636** |
| Kyrie Irving | 70 | 95 | 122 | 73 | **1561** |
| Jalen Suggs | 80 | 92 | 103 | 71 | **1540** |
| Naz Reid | 105 | 77 | 104 | – | **1464** |
| Coby White | 93 | 113 | 106 | – | **1310** |
| Fred VanVleet | 134 | 74 | 161 | – | **1207** |
| Myles Turner | 129 | 104 | 135 | – | **1073** |
| Jakob Poeltl | 133 | 135 | 307 | – | **736** |
| Jimmy Butler | 181 | 153 | 154 | – | **692** |
| Anfernee Simons | 198 | 155 | 155 | – | **650** |
| Khaman Maluach | – | 154 | 340 | – | **480** |
| De'Anthony Melton | 229 | 231 | 418 | – | **268** |
| Jay Huff | 271 | 223 | 534 | – | **199** |
| Adem Bona | 284 | 303 | 410 | – | **134** |
| Khris Middleton | 347 | 331 | 553 | – | **32** |
| Marvin Bagley III | 317 | – | 637 | – | **8** |

## Picks

Rookie picks are priced 50/50 off Dizzle's pick chart (player-rank equivalence)
and the Hashtag crowd pick bands.

| Pick | Dizzle | crowd | **VALUE** |
|---|---:|---:|---:|
| 1.09 | #90 → 1525 | #111 → 1191 | **1358** |
| 2.09 | #185 → 562 | #144 → 840 | **701** |
| 3.09 | #275 → 226 | #272 → 234 | **230** |

All own future 1sts, 2nds and 3rds are held. Per `evals/team-projections.md`
they land ~1.10 in each of '27, '28 and '29.

| Pick | Projected slot | **VALUE** |
|---|---|---:|
| '27 1st | ~1.10 | **~1000–1200** |
| '28 1st | ~1.10 | **~900–1100** |
| '29 1st | ~1.10 | **~800–1000** |
