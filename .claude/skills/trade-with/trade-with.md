User will provide a name

Load their `<Name>.team.md` (`eval-team` §Output). If stale, raise immediately and stop.

Otherwise:

1. Load `strategy/teams/my-team/Ours.team.md` as well
2. Load `trades` Skill
3. Use `read-messages` Skill to catch up on talks so far

Follow `trades` Skill. Brainstorm first (`trades` §Brainstorm); sim only the short list.

When simming new shapes, follow `sims` Skill §Agent workflow (JSON + `sim_run.py` only), then **archive every priced deal** into both `strategy/teams/<owner>/<Name>.shapes.md` and `<Name> Trade Shapes.md` before finishing — right tier, sorted. Do not end the session with unarchived sims unless the user opts out.

Load `<Name>.shapes.md` next to their `.team.md`. Never read `* Trade Shapes.md`. Include the shapes in your analysis if/when warranted.
