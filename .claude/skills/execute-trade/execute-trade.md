---
description: Use when the user says a trade was agreed or went through, or asks to execute one
---

1. Confirm it executed on the wire (`get-league-info` §`FetchTrades`). Not yet → change nothing; tell the user it's still pending.
2. Re-cut each side's roster: `strategy/lineup-math/run fetch_data.py roster <team_id>` (`team-info` for ids). Picks moved → also `fetch_data.py picks`.
3. Run `eval-team` fresh for each side that has eval files.
4. Update `strategy/Team Projections.md` as warranted: this season's sim, future outlook (`sims` §Future seasons).
