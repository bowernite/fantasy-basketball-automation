---
name: team-info
description: Maps every league team to its id, username, owner's real name and the Name we call it by. Use whenever a team, owner or `team_id` is named.
---

# Teams

`team_id` verified against `FetchLeagueStandings` (`get-league-info`).

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

`161015` appears as the long form (the API's) and as **Jon** (`evals/teams/jon/`) — one
team, join either. Bare **"SGA" is the player**, not the team.

**Name** is how we refer to each team everywhere (AGENTS.md §Naming).

`160941` breaks the `1610xx` pattern; don't infer ids.

**`evals/teams/` is named by owner, not team** — ours is `my-team/`, Michael's is `bonin/`,
the rest are the lowercased Name. External
snapshots (`dizzle-dynasty`, `hashtag-basketball`, dated board pulls) live in
`evals/board-snapshots/`.
