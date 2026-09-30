---
description: Use whenever a league team, owner, username or `team_id` comes up, or to find a team's `strategy/teams/` dir
---

`team_id` verified against `FetchLeagueStandings`. **Name** is the one to use (AGENTS.md §Naming).

| Team | `team_id` | Username | Owner | Name |
|---|---|---|---|---|
| Bathroom club (**us**) | 161025 | `brettford` | Brett | Brett |
| Pascals of Pangea | 161016 | `mBone` | Michael Bonin | Michael |
| Jesus Christ and his Disciples | 161024 | `Brohard` | Josh | Josh |
| King Christopher of Bavaria | 161014 | `chris96` | Chris Kelnhofer | Chris |
| Yao Ming Dynasty | 161018 | `Scal` | Brian W. | Brian |
| The Gutes of Gotland | 161017 | `j0epa` | Joe Kelnhofer | Joe |
| Matthew the Apostle | 161021 | `RoyceWhite` | Matt Hlina | Hlina |
| Pharaoh Mattankhamun-Ra | 160941 | `Matthew7` | Matthew Pook | Matthew |
| Mongol Khans Freak Militia | 161019 | `henry12287` | Henry | Henry |
| Shai Gilgeous-Alexander the Great (**SGA-the-Great**) | 161015 | `KIMJONIL` | Jon | Jon |
| The Don | 161020 | `MitchBrault3` | Mitch | Mitch |
| The Han Dybantsy | 161022 | `t27marino` | Todd | Todd |

- `161015` appears as the long form (the API's) and as **Jon** (`strategy/teams/jon/`) — one team, join either. Bare **"SGA" is the player**, not the team
- Take ids from this table; `160941` breaks the `1610xx` pattern
- **`strategy/teams/` is named by owner, not team**: ours is `my-team/`, Michael's is `bonin/`, the rest are the lowercased Name. External board snapshots (`dizzle-dynasty`, `hashtag-basketball`, dated board pulls) live in `strategy/board-snapshots/`
