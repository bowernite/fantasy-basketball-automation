# Hashtag Basketball — local snapshot

Offline copy of the two hashtagbasketball.com boards that carry 60% of BASE
(`team-eval`). Neither is reproducible upstream: the crowd board is re-voted daily,
and the expert board is a dated snapshot that gets overwritten in place. Without
this directory no published eval can be re-checked.

- **Sources:** `https://hashtagbasketball.com/keeper` ·
  `https://hashtagbasketball.com/fantasy-basketball-dynasty-rankings`
- **Snapshotted:** 2026-07-29 (`manifest.csv`'s `fetched_utc` is UTC, so it reads 07-30)
- **Boards' own update stamps:** crowd `29 July 2026` ·
  expert `02 July 2026 by Joseph Mamone`
- **Live fetch:** `hashtag-basketball` Skill. Use that first; fall back here only if
  the site is unreachable, and say you're citing a snapshot.

`manifest.csv` is the staleness check — per board: page title, the controls that
produced it, the board's own `Updated:` stamp, our fetch time, row count, rank span,
pick-band count, vote total, and the crowd board's draft-class notice if it was
showing. Compare `board_updated` against a live pull before trusting anything here.

## Files

| File | Rows | What |
|---|---|---|
| `expert-dynasty-points.csv` | 766 | **Expert board, `DDTYPE=POINT` — our format.** 35% of BASE |
| `crowd-keeper.csv` | 759 | Crowd `/keeper` board, pick bands inline. 25% of BASE |
| `manifest.csv` | 2 | Provenance + staleness fields, one row per board |

Row counts exclude the header. Both boards reach well past `D` = 12 × 38 = 456, so
absence from either is a real 0 — never renormalise a weight off these two
(`team-eval` → *Depth and absence*).

Only the expert Points view is snapshotted; `OVERALL` / `CONTEND` / `REBUILD` /
`ROOKIE` are one postback each off the Skill and enter no blend.

## Columns

**`crowd-keeper.csv`** — `rank`, `player`, `hashtag_id`, `team`, `pos`, `age`,
`keeper_value`.

**`expert-dynasty-points.csv`** — `rank`, `player`, `pos`, `team`, `age`,
`keeper_rank`, `keeper_value`, then the board's projection line: `fg_pct`, `ft_pct`,
`3pm`, `pts`, `reb`, `ast`, `stl`, `blk`, `to`.

`age` is numeric on both (the expert page renders `22.6yo`) and `pos` is `/`-joined
on both (the crowd page renders `PF,C`). `keeper_rank` / `keeper_value` are the
**crowd** figures the expert page mirrors, so they match `crowd-keeper.csv` and do
not vary by expert view.

## Gotchas

- **`keeper_value` is not BASE and never enters it.** It is near-linear, so summing
  it for a package implies three #60s beat the #1. Only the **rank** crosses boards,
  through `team-eval`'s curve.
- **Draft picks are the 8 `team == DRA` rows in `crowd-keeper.csv`**, ranked inline
  against players with blank `pos`/`age`. Filter on `DRA`, never on `Pick` in the
  name — that also catches **Jalen Pickett**. Bands cover the NBA's 60 slots, so look
  them up by overall ordinal `(R-1)×12 + S` (`evaluating-picks`).
- **`class_loading_notice` is non-empty in this snapshot**, so its pick rows are
  distorted in both directions — worked numbers in `evals/board-snapshots/boards-2026-07-29.md`.
  A blank field is the only clean state for those 8 rows.
- **`rank` is not the row index.** Ties and server-side skips both break it: 759
  crowd rows span 1–764 (ordinals 134, 136, 140–142 are absent from the page
  itself), 766 expert cards span 1–772. Read `rank`, never a line number.
- **The expert board ships duplicate cards** — 766 cards, 764 distinct players in
  this snapshot (`Chaz Lanier` at 402 and 412, `Nigel Hayes` twice at 485). Dedupe
  before counting depth or blending.
- **Names are not keys.** Two different players are called `Jaylin Williams` (OKC
  #245, DEN #711 on the expert board). `hashtag_id` is on the crowd board only, so
  join on `(player, team)` and hand-check collisions.
- **Blank cells are the page's, not a parse failure** — the expert board leaves
  `pos` empty for 117 rows (incoming class, no eligibility yet), `keeper_value` for
  30, and the whole stat line for anyone without an NBA season.
- Both expert views are one analyst; the crowd board is the only actual market here.
  See "Caveats" in `evaluating-players`.

## Refresh

Overwrites all three files from the live boards. Run from the repo root.

```bash
python3 .claude/skills/hashtag-basketball/refresh_snapshot.py
```

**Run the script — never retype or reimplement its parse.** It fetches and parses both
boards before writing anything, so a failed assert leaves the existing snapshot intact.
The asserts are Recipe A / Recipe B's (`hashtag-basketball`), and a tripped one means
discard, not caveat.

The counts and stamps above are this snapshot's — after refreshing, update them and
the gotcha figures from `manifest.csv`.
