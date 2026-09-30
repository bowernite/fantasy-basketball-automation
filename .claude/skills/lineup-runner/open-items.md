# Lineup runner: open items

As of 2026-09-30: deployed and running every 5 min, saves **off**, alerts reach Trello only. One live save from the Worker (with restore) passed.

## Needs the user

1. **Pushover**: install it on the phone and sign up, then sign in at pushover.net in the agent browser. An agent then sets the secrets (`operations.md` §Secrets) and sends a test alert for the user to confirm. Until then nothing reaches the phone
2. **healthchecks.io check** for the dead-man (`operations.md` §Secrets)
3. **Approve automated saves.** Gate: 1 and 2 live and a test alert confirmed on the phone
4. **Manual edits vs hourly runs**: once saves are on, a manual lineup edit is overwritten within ~1 h. The user said to flag this for later; decide before relying on manual edits in season

## Game-day tasks

- **Before 10/20**: see T-40/T-15 runs fire live once (e.g. a bearer-guarded debug route that injects a fake tip at now + 45 min, removed after); preseason has no real tip targets
- **10/20, opening night (tips 2:00p, 6:00p, 8:30p CT)**: expect `/runs` records around 1:20p/1:45p, 5:20p/5:45p, 7:50p/8:15p CT plus hourlies
- **10/20 after the 2:00p CT tip**: pull the signed-in lineup page and `FetchRoster` for day 1 from `GET /captures` (the Worker stores the day's first check with locked rows, and any failing check), scan them for secrets and personal data, add them as fixtures, and run `decideLineup` tests on them. This settles the locked-row markup (`fleaflicker.md`), whether the page vs API cross-check still agrees once starters lock (a mismatch fails every later run that day), and the in-progress matchup markup. After the last tip, capture the fully locked page too (does the form or Save button survive?). If saves are on, note the save response for a locked player
- **Opening week**: measure injury-feed lag and untagged OUT news from `/runs` (`jq '[.[].days[].injuries // empty]'`, same for `untaggedOutNews`). Then decide an ESPN OUT-only scoring override and whether untagged OUT news should score
- **2027 season finale**: check what the API returns at rollover. An empty `eligibleLineupPeriods` would make every tick throw (a priority-0 alert every 3 h)

## Backlog

- Game-day digest once saves are on: at each day's first T-40, send starters, benched players with a game, and changes (Pushover priority −1)
- A NaN score `alert()` in `src/prioritization/score-weighting.ts` fails the whole day: score 0 and warn instead
- Only `.alert-danger` banners fail a run; decide fail vs warning if a real `.alert-warning` shows up
- One problem can alert twice (hourly and tip runs fingerprint differently; warnings change as games start). Trello "Still failing" comments send the body in the URL and also say it for warnings
- Stale bundled projections: rostered players missing from generated `src/data/player-data.ts` (`projections` Skill)
- `tsc` doesn't cover `src/worker/`, and the empty-slot / over-fill guards in `decide-lineup.ts` have no test reaching them
- Only if needed: `/api/SetLineup` fallback, a GitHub Actions backup runner, a per-run LLM review, Pushover receipts, a "recovered" message, pruning dedupe keys
