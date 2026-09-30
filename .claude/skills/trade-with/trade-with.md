---
disable-model-invocation: true
---

The user names an owner.

1. Load their `<Name>.team.md` (`eval-team` §Output). Stale → tell the user and stop
2. Load `strategy/teams/my-team/Ours.team.md` and their `<Name>.shapes.md` (next to their `.team.md`)
3. Catch up on talks so far via `read-messages-ff` Skill
4. Follow `trades` Skill through §Simming's done condition: every priced deal archived in both shape files, unless the user opts out
