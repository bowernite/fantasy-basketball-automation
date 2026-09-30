---
description: Dizzle Dynasty — use when pulling the Dizzle Dynasty rankings sheet (dynasty or rookie boards, 9Cat or Points) or its rookie pick-value chart
---

Best-fit external board for this league, so start here: it has a **real Points-format dynasty ranking** and a **pick-value chart**. All tabs are one analyst; the 9Cat and Points tabs are not two opinions (`eval-player` §Caveats). Source updates roughly monthly.

## Fetch

1. Run the recipe (or the snapshot fallback) in a `general-purpose` subagent (`AGENTS.md` §Subagents). Tell it which tab(s)/limit to pull; it hands back `SOURCE`/`TAB`/`FORMAT`/`UPDATED` plus the table, never the raw export.
2. List tabs first when unsure. The tab argument is a substring match on the board part of the title (§Tabs) and asserts it hit exactly one tab.
3. Done when the pull printed its header with no tripped `assert`. Report `SOURCE` / `TAB` / `FORMAT` / `UPDATED` verbatim when citing these numbers.

```bash
uv run .claude/skills/dizzle-dynasty/sheet.py                                # list tabs
uv run .claude/skills/dizzle-dynasty/sheet.py "Dynasty Ranks, Points" 40     # one tab
uv run .claude/skills/dizzle-dynasty/test_sheet.py                           # offline parse guard, no network
```

**Run `sheet.py` as-is; never transcribe, reimplement or "fix" it**, and keep its xlsx export (never gviz: `gviz/tq?sheet=<name>` silently falls back to the first tab, 9Cat, on an unknown or misspelled name at HTTP 200; `htmlview` exposes no gids). `uv` resolves `openpyxl` from the script's metadata block; no venv needed. A tripped `assert` means discard the pull, not caveat it.

Public Google Sheet, no auth: `1EmReTa5KUcFFMCy8Fq-NpQG3WU0pMY7XNW54G3EPbEM`

**Snapshot:** `strategy/board-snapshots/dizzle-dynasty/` holds a dated CSV/xlsx snapshot. Cite it only if the sheet is unreachable, and say so.

## Tabs

Tab titles are `<Month> <Year> <board>`; **the month moves, so match on the board part only.**

| Tab suffix | Use |
|---|---|
| `Dynasty Ranks, Points` | **our format**: main board, ~450 ranked players |
| `Dynasty Ranks, 9Cat` | cross-check only |
| `Rookie Ranks, Points` | **our format**: incoming class + college stats |
| `Rookie Ranks, 9Cat` | cross-check only |
| `Pick Values` | 1.01–2.30, `Top N-M` player equivalence + who to take per format |

**Any hidden tab is a stale archive** (an earlier month's board); the recipe asserts `visible`.

## Pricing picks

**Primary: the dynasty board's slot prefix.** The board carries the incoming class inline, each row prefixed with the author's rookie-draft slot (`1.09 / Brayden Burries` in the `Player` cell) at that row's real board rank: an exact rank per slot on the same board the players are priced on (`eval-pick` §4). Match on the prefix, never the name.

- Coverage runs from `1.01` to roughly the chart's early round 2 and can stop short of our 48 slots (chart `2.18`), so **check the slot you want has a row**.
- The prefix **drifts from `Pick Values`' `Who I Might Take` column at a few slots.** Prefer the prefix; don't reconcile them by name.

**Fallback and cross-check: `Pick Values`.** It prices picks as **"the player ranked Top N-M"**, so it yields a **rank** (no rescaling, unlike Hashtag's Keeper Value) that goes through `Eval Definitions §BASE`'s curve like any rank. Bands are wide and flatten consecutive slots (`eval-pick` §4).

- **It prices the incoming class only**; the bands track where *this* class thins, so it is never a future year's price, only a labelled cross-check (`eval-pick`).
- It charts the NBA's 60 slots (1.01–1.30, 2.01–2.30), as do the slot prefixes. Ours is 12×4, so look up by **overall ordinal** (`eval-pick`), never by our round label.
- Pick labels are floats in the sheet (`1.1` for 1.10, `2.30000000000004` for 2.30); the recipe and the snapshot both correct this.

**Rookie tabs:** our rookie draft takes any player from the class in any order, so slot N ≈ the Nth name in `Rookie Ranks, Points`, and its `Who I Might Take (Points)` column is the direct answer. Read their `#` per `eval-pick`; it is not a board rank. **`Draft Pick` there is the real NBA slot, not ours** (row 1 can read `1.03`); answer "who goes at one of our slots" from the class ordinal or the dynasty board's slot prefix.

## Reading rows

- `TIER BREAK` rows with a blank rank are tier delimiters, not players.
- `Notes/Outlook` carries the author's reasoning and its own update date: the highest-signal column for trade framing. Quote it rather than paraphrasing a rank.
- `Prev. Rank` / `+/- Change` show where perception is moving.
- Still 9Cat-derived at root and generic-Points at best (`eval-player` §Caveats).
