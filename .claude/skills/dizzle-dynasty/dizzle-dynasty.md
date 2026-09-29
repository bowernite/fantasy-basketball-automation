---
name: dizzle-dynasty
description: Dizzle Dynasty rankings sheet — dynasty and rookie boards in both 9Cat and Points, plus a rookie pick-value chart.
---

_Fetch live with the recipe below (`.claude/skills/dizzle-dynasty/sheet.py`).
`evals/board-snapshots/dizzle-dynasty/` holds a dated CSV/xlsx snapshot — fall back to it only if the
sheet is unreachable, and say you're citing a snapshot. Source updates roughly monthly._

# Dizzle Dynasty

Best-fit external board for this league: it has a **real Points-format
dynasty ranking** and a **pick-value chart**. Start here.

All tabs are one analyst — the 9Cat and Points tabs are not two opinions. See
"Caveats" in `eval-player`.

## Fetch in a subagent

Run the recipe — and any fallback read of the local snapshot in
`evals/board-snapshots/dizzle-dynasty/` — inside a dedicated `Agent` call
(`general-purpose`), never inline. Tell it which tab(s)/limit to pull and have it hand back
`SOURCE`/`TAB`/`FORMAT`/`UPDATED` plus the table; the raw sheet export never enters the main
context (`CLAUDE.md` §*Subagents*).

Public Google Sheet, no auth:
`1EmReTa5KUcFFMCy8Fq-NpQG3WU0pMY7XNW54G3EPbEM`

## Tabs

Tab titles are `<Month> <Year> <board>` — **the month moves, so list tabs first and
never hardcode one.** Match on the board part only.

| Tab suffix | Use |
|---|---|
| `Dynasty Ranks, Points` | **our format** — main board, ~450 ranked players |
| `Dynasty Ranks, 9Cat` | cross-check only |
| `Rookie Ranks, Points` | **our format** — incoming class + college stats |
| `Rookie Ranks, 9Cat` | cross-check only |
| `Pick Values` | 1.01–2.30, `Top N-M` player equivalence + who to take per format |

**Any hidden tab is a stale archive** — an earlier month's board kept in place. The
recipe asserts `visible`; never enumerate which months are hidden, it changes.

**The dynasty board carries the incoming rookie class inline against players, and each
such row is prefixed with the author's own rookie-draft slot** — `1.09 / Brayden
Burries` in the `Player` cell, at that row's real board rank. This is the primary
pick-pricing source: an exact rank per slot, on the same board the players are priced
on (`eval-pick` §4). Match on the prefix, never on the name.

- Coverage runs from `1.01` down to roughly the chart's early round 2 — well past our
  36 slots, but **check the slot you want has a row** rather than assuming.
- The prefix is the author's slot assignment and **drifts from `Pick Values`' own
  `Who I Might Take` column at a few slots.** They are two columns, not one; prefer the
  prefix and don't reconcile them by name.
- The rookie tabs carry the class too, with college stats, but read their `#` per
  `eval-pick` — it is not a board rank.

## Never use gviz

`gviz/tq?sheet=<name>` **silently falls back to the first tab on an unknown or
misspelled name** — no error, HTTP 200. The first tab is 9Cat, so you get 9Cat
while believing you have Points. Verified: `sheet=BOGUS` returns the 9Cat board.
`htmlview` exposes no gids. The recipe uses the xlsx export instead.

## Recipe — run the file, never retype it

```bash
uv run .claude/skills/dizzle-dynasty/sheet.py                                # list tabs
uv run .claude/skills/dizzle-dynasty/sheet.py "Dynasty Ranks, Points" 40     # one tab
```

Match on the board part of the title only, per **Tabs** above. The tab argument is a
substring match and asserts it hit exactly one tab, so list first when unsure.

**Do not transcribe, reimplement or "fix" what is in that file** — in particular do not
swap the xlsx export for gviz. `uv` resolves `openpyxl` from the script's own metadata
block; no venv needed. A tripped `assert` means discard the pull, not caveat it.

```bash
uv run .claude/skills/dizzle-dynasty/test_sheet.py    # offline parse guard, no network
```

Report `SOURCE` / `TAB` / `FORMAT` / `UPDATED` verbatim when citing these numbers.

## Reading it

- Rows reading `TIER BREAK` with a blank rank are tier delimiters, not players.
- `Notes/Outlook` carries the author's reasoning and its own update date — the
  highest-signal column for trade framing; quote it rather than paraphrasing a
  rank.
- `Prev. Rank` / `+/- Change` show momentum, i.e. where perception is moving.
- Pick Values prices picks as **"the player ranked Top N-M"**, not as an
  abstract score — so it needs no *rescaling* (unlike Hashtag's Keeper Value). It
  yields a **rank**, which then goes through `Eval Definitions §BASE`'s curve like any other
  rank. Bands are wide and flatten consecutive slots, so it is the **fallback and
  cross-check** to the dynasty board's slot prefix, not the primary read
  (`eval-pick` §4).
- **Pick Values prices the incoming class only** — the bands track where *this*
  class thins, so it is never a future year's price, only a labelled cross-check
  (`eval-pick`).
- Our rookie draft takes any player from the class in any order, so slot N ≈ the
  Nth name in `Rookie Ranks, Points`, and the `Who I Might Take (Points)` column
  is the direct answer.
- **`Draft Pick` on the rookie tabs is the real NBA slot, not ours** — its row 1 can
  read `1.03`. Never answer "who goes at one of our slots" from it; use the class
  ordinal or the dynasty board's slot prefix.
- `Pick Values` charts the NBA's 60 slots (1.01–1.30, 2.01–2.30) and the dynasty
  board's slot prefixes use the same labels. Ours is 12×3, so look up by **overall
  ordinal** (`eval-pick`), never by our round label.
- Pick labels are floats in the sheet, so a naive read gives `1.1` for 1.10 and
  `2.30000000000004` for 2.30. The recipe and the snapshot both correct this.
- Still 9Cat-derived at root and generic-Points at best (`eval-player` §*Caveats*).
