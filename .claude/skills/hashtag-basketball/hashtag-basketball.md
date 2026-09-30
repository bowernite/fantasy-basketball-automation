---
description: Hashtag Basketball — use when pulling dynasty rankings, keeper values or draft-pick values from hashtagbasketball.com
---

Market perception for `eval-player` / `eval-pick`, not truth: Fleaflicker `seasonAverage` (`get-league-info`) is the only figure scored under our actual rules.

## Fetch

1. Run the recipes (or the snapshot fallback) in a `general-purpose` subagent (`AGENTS.md` §Subagents). Tell it which recipe(s)/args to run; it hands back the verification header (`BOARD`/`UPDATED`/`VERIFIED`) plus the table, never raw HTML.
2. Pull both boards by default; disagreement between them is the tradeable signal. Picks → crowd only. Our format → expert `DDTYPE=POINT`.
3. Done when each pull printed a header whose four checks (§Verify) passed. Report `BOARD` / `UPDATED` / `VERIFIED` verbatim whenever citing these numbers.

```bash
python3 .claude/skills/hashtag-basketball/crowd_keeper.py 60                                   # Recipe A
python3 .claude/skills/hashtag-basketball/expert_dynasty.py DDTYPE=POINT DDSTAT=800 limit=40   # Recipe B
python3 .claude/skills/hashtag-basketball/test_parse.py                                         # offline guard, both recipes, no network
```

**Run the recipe files as-is; never transcribe, reimplement or "fix" them.** Their parse patterns are correct and have been broken repeatedly by retyping; each file's header says which parts read as typos and aren't. A tripped `assert` means discard the pull; leave the pattern alone.

`WebFetch` 403s on every URL (UA filtering, not auth); the recipes send a browser UA, logged out. Pages are 300KB–3MB.

**Snapshot:** `strategy/board-snapshots/hashtag-basketball/` holds CSVs of both boards plus a `manifest.csv` of stamps, counts and controls (`README.md` there documents columns and gotchas). Cite it only if the site is unreachable, and say so. Rewrite it with `python3 .claude/skills/hashtag-basketball/refresh_snapshot.py` (from the repo root) whenever an eval must stay reproducible: the crowd board re-votes daily and the expert board is overwritten in place.

## Verify

The recipes `assert` all four; a bad control value returns `Oops | Hashtag Basketball` at HTTP 200, so every check is required.

1. `<title>` matches the expected board.
2. Every requested control echoes back `selected`. Any mismatch → discard, not caveat.
3. `Updated:` stamp parsed.
4. Row/card count > 0.

## Two boards: keep separate

| | **Crowd keeper** `/keeper` | **Expert dynasty** `/fantasy-basketball-dynasty-rankings` |
|---|---|---|
| Source | crowdsourced votes | one analyst |
| Freshness | rolling, daily | static dated snapshot |
| Fetch | GET | GET + form POST for any non-default view |
| Draft picks | **yes, priced as rows** | no |
| Points-league view | no | **yes (`DDTYPE=POINT`)** |

## Recipe A: crowd keeper board + pick values

- **`DRA` is the only safe pick discriminator**: matching `Pick` in the name also catches the player **Jalen Pickett**. Recipe A asserts the band count for that reason.
- Ties share a rank, so the last rank exceeds the row count. **Read the printed ordinal, never the row index.** The two `VALUE(+)`/`VALUE(-)` movers tables use different markup and are deliberately not parsed.
- This board ranks the incoming class inline against players, on the crowd's `/keeper` rank (not a class ordinal): one of the boards `eval-pick` §5 needs, alongside Recipe B's `DDTYPE=POINT`.
- Bands cover the NBA's 60 slots, labelled `Pick N` / `Pick N-M`. Ours is 12×4, so look them up by **overall ordinal** (`eval-pick`), never by our round label.

## Recipe B: expert dynasty board

Dropdowns are ASP.NET postbacks; `?DDTYPE=POINT` in the URL is ignored and returns the default board. Recipe B takes any `CTRL=value` pairs plus `limit=N`; **the first control named drives the postback**, the rest ride along at whatever the page already has.

**Pass `DDSTAT=800`.** `DDSTAT` hard-caps rows returned, and the blend needs depth ≥ `D` (`Eval Definitions §BASE`) or the board renormalises out of it; `400` silently truncates, `800` returns the whole board.

| Control | Values |
|---|---|
| `DDTYPE` | `OVERALL` `CONTEND` `REBUILD` `ROOKIE` `POINT`: **`POINT` = our format**; `ROOKIE` = incoming class |
| `DDSTAT` | `300` `400` `500` `800` pool size |
| `DDFORECAST` | `5` `3` seasons |
| `DDPOS` | `All` `PG` `SG` `SF` `PF` `C` |
| `DDTSUM` | `All` or NBA abbr (`SAS`, `OKL`, …) |
| `DDPOSFROM` | `1` Yahoo · `2` Fantrax |

`DDTYPE=ROOKIE` gives **class order**, not board rank (`eval-pick`): our rookie draft takes any player from the class in any order, so slot N ≈ the Nth name. For the class's *board* ranks, re-pull `DDTYPE=POINT`, which carries the class inline.

## Reading it against our league

- **`DDTYPE=POINT` is a generic points league**, and both boards lean 9-cat otherwise (`OVERALL` buries FT%-negative bigs; pull `POINT` if pulling only one). `Eval Definitions §Where our format pulls off consensus` owns that gap.
- **The rank label re-renders per active board**: `Dynasty #N` is the overall rank on the overall board, the points rank on `POINT`. Fetch twice and label the columns separately. `Keeper #N` / `Keeper Value` are crowd figures, constant across both.
- **`KVALUE` (Keeper Value) is not `Eval Definitions`' `VALUE`/`BASE`** and never enters it: it's near-linear, so summing it for a package implies three #60s beat the #1. Only the **rank** crosses boards; run ranks through `Eval Definitions §BASE`'s convex curve. Ceiling >> floor.
- **A "draft class is being loaded into the voting system" notice on the crowd board invalidates its class-year pick rows** until it clears; symptom: a band pricing far off the players inside it, in either direction. Check for the notice on every pull; while it shows, prefer `dizzle-dynasty`'s chart. Dated example with numbers: `strategy/board-snapshots/Boards 2026-07-29.md`.
- Both expert views are one analyst; the crowd board is the only actual market here (`eval-player` §Caveats).
- Ignore position columns for roster fit.

## Other slugs

`/fantasy-basketball-keeper-rankings` 404s; the crowd board is `/keeper`. Read other slugs off the site nav (they aren't guessable), with the same UA + verification rules.
