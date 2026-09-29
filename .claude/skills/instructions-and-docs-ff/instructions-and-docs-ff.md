---
name: instructions-and-docs-ff
description: Mandates for how to write documentation, evals, instructions for agents, skills, etc. Use when writing/editing any of those, any md file, or comment blocks in code
---

When writing documentation, evals, instructions for agents, skills, etc.:

- Follow `instructions-and-docs` Skill
- Split up amongst files. A single file should not be overwhelming, and can link to other files. A file should not have contents in it that aren't relevant 80-90% of the time a user who opens that file would want to see
- When updating any of these, you'll need to see if linked files need to be updated
- Try to be DRY (e.g. team evals shouldn't all contain context on what different metrics or columns are; instead, there should be one shared file for that)
- This is not an excuse to not use bullet points, line breaks, etc, where warranted and not fluffy

# Do not use this for

- Human team eval files (`*'s Team.md`, `My Team.md`). You still shouldn't be wordy for those, but no need be ultra compact there

# Sims

Trade-shape sims: write JSON configs, run `strategy/lineup-math/run sim_run.py`, copy the big numbers from stdout / JSON `results` into `<Name>.shapes.md` and `<Name> Trade Shapes.md` by hand (`trade-shapes`) — **same session**, before returning. Read `.shapes.md` only. Avoid writing your own scripts whenever possible; rely on your own logic. Canonical workflow in `sims` Skill §Agent workflow; archive rules in `trades` §Simming.
