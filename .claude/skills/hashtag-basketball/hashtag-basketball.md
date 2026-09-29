---
name: hashtag-basketball
description: Pull dynasty rankings, keeper values and draft-pick values off hashtagbasketball.com, with proof of which board you're actually reading.
---

_Fetch live with the recipes below. `strategy/board-snapshots/hashtag-basketball/` holds a CSV snapshot
of both boards plus a `manifest.csv` of stamps, counts and controls — fall back to it
only if the site is unreachable, and say you're citing a snapshot. Rewrite that snapshot
with `python3 .claude/skills/hashtag-basketball/refresh_snapshot.py` (from the repo root)
whenever an eval must stay reproducible, since the crowd board re-votes daily and the
expert board is overwritten in place. Its `README.md` documents the columns and gotchas._

# Hashtag Basketball

Market perception for `eval-player` / `eval-pick`. Not truth —
Fleaflicker `seasonAverage` (`get-league-info`) is the only figure scored under
our actual rules.

## Fetch in a subagent

Run the recipes — and any fallback read of the local snapshot in
`strategy/board-snapshots/hashtag-basketball/` — inside a dedicated `Agent` call
(`general-purpose`), never inline. Tell it which recipe(s)/args to run and have it hand back
the printed verification header (`BOARD`/`UPDATED`/`VERIFIED`) plus the table; raw HTML never
enters the main context (`CLAUDE.md` §*Subagents*).

**`WebFetch` 403s on every URL** (UA filtering, not auth) — the recipes send a browser
UA, logged out. Pages are 300KB–3MB: take the recipes' tabular output, never read raw
HTML into context.

## Two boards — keep separate

| | **Crowd keeper** `/keeper` | **Expert dynasty** `/fantasy-basketball-dynasty-rankings` |
|---|---|---|
| Source | crowdsourced votes | one analyst |
| Freshness | rolling, daily | static dated snapshot |
| Fetch | GET | GET + form POST for any non-default view |
| Draft picks | **yes, priced as rows** | no |
| Points-league view | no | **yes (`DDTYPE=POINT`)** |

Pull both by default; disagreement between them is the tradeable signal. Picks →
crowd only. Our format → expert `DDTYPE=POINT`.

## Recipes — run the files, never retype them

Each recipe is a script in this skill's directory. Run it as-is; it prints the
verification header and the board. `KVALUE` is Keeper Value, **not** `Eval Definitions`'
`VALUE`/`BASE`.

```bash
python3 .claude/skills/hashtag-basketball/crowd_keeper.py 60                              # Recipe A
python3 .claude/skills/hashtag-basketball/expert_dynasty.py DDTYPE=POINT DDSTAT=800 limit=40   # Recipe B
```

**Do not transcribe, reimplement or "fix" what is in those files.** Their parse
patterns are correct as written and have been broken repeatedly by retyping; each file's
header states which parts read as typos and are not. If output looks wrong, an `assert`
fires — read it, discard the pull, do not edit the pattern.

```bash
python3 .claude/skills/hashtag-basketball/test_parse.py    # offline guard, both recipes, no network
```

## Recipe A — crowd keeper board + pick values

**`DRA` is the only safe pick discriminator** — matching `Pick` in the name also catches
the player **Jalen Pickett**. Recipe A asserts the band count for that reason.

Ranks are not contiguous — ties share a rank, so the board's last rank exceeds its
row count. **Read the printed ordinal, never the row index.** Two `VALUE(+)`/`VALUE(-)`
movers tables on the page use different markup and are deliberately not parsed.

This board **does** rank the incoming class inline against players, on the crowd's
`/keeper` rank rather than a class ordinal — one of the boards `eval-pick` §5
needs, alongside Recipe B's `DDTYPE=POINT`.

Bands cover the NBA's 60 slots, and are labelled `Pick N` / `Pick N-M` in that space.
Ours is 12×3, so look them up by **overall ordinal** (`eval-pick`), never by our
round label.

## Recipe B — expert dynasty board

Dropdowns are ASP.NET postbacks; `?DDTYPE=POINT` is ignored and returns the
default board.

**Pass `DDSTAT=800`.** `DDSTAT` is a hard cap on rows returned, and the blend needs
depth ≥ `D` (`Eval Definitions §BASE`) or the board renormalises out of it.
`400` truncates at 400 and silently loses that depth; `800` returns the whole board.

Recipe B takes any `CTRL=value` pair as an argument plus `limit=N`; **the first control
named drives the postback**, the rest ride along at whatever the page already has.

| Control | Values |
|---|---|
| `DDTYPE` | `OVERALL` `CONTEND` `REBUILD` `ROOKIE` `POINT` — **`POINT` = our format**; `ROOKIE` = incoming class |
| `DDSTAT` | `300` `400` `500` `800` pool size — **use `800`**, anything less caps the board |
| `DDFORECAST` | `5` `3` seasons |
| `DDPOS` | `All` `PG` `SG` `SF` `PF` `C` |
| `DDTSUM` | `All` or NBA abbr (`SAS`, `OKL`, …) |
| `DDPOSFROM` | `1` Yahoo · `2` Fantrax |

`DDTYPE=ROOKIE` gives **class order**, not board rank (`eval-pick`) — our rookie
draft takes any player from the class in any order, so slot N ≈ the Nth name. For the
class's *board* ranks, re-pull `DDTYPE=POINT`, which carries the class inline against
players.

## Verify the board before using any number

The recipes `assert` on all four; a bad control value returns `Oops | Hashtag
Basketball` at HTTP 200, so none are optional.

1. `<title>` matches the expected board.
2. Every requested control echoes back `selected`. Any mismatch → discard, don't
   caveat.
3. `Updated:` stamp parsed.
4. Row/card count > 0.

Report `BOARD` / `UPDATED` / `VERIFIED` verbatim whenever citing these numbers.

## Reading it against our league

- **`DDTYPE=POINT` is a generic points league**, and both boards lean 9-cat otherwise
  (`OVERALL` buries FT%-negative bigs — pull `POINT` if pulling only one).
  `Eval Definitions §Where our format pulls off consensus` owns that gap.
- **The rank label re-renders per active board**: `Dynasty #N` is the overall
  rank on the overall board, the points rank on `POINT`. Fetch twice and label
  the columns separately. `Keeper #N` / `Keeper Value` are crowd figures and are
  constant across both.
- **`KVALUE` (Keeper Value) is not BASE** and never enters it — a near-linear scale, so
  summing it for a package implies three #60s beat the #1. Only the **rank** crosses
  boards; run ranks through `Eval Definitions §BASE`'s convex curve. Ceiling >> floor.
- **A "draft class is being loaded into the voting system" notice on the crowd board
  invalidates its class-year pick rows** until it clears — the symptom is a band pricing
  far off the players inside it, in either direction. Prefer `dizzle-dynasty`'s chart
  while it shows. Check for the notice on every pull; a dated instance with numbers is
  in `strategy/board-snapshots/Boards 2026-07-29.md`.
- Both expert views are one analyst, and the crowd board is the only actual
  market here. See "Caveats" in `eval-player`.
- Ignore position columns for roster fit.

## Other slugs

`/fantasy-basketball-keeper-rankings` 404s — the crowd board is `/keeper`. Other slugs
are not guessable; read them off the site nav, and apply the same UA + verification
rules.
