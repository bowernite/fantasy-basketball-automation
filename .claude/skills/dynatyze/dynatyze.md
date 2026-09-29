---
name: dynatyze
description: Dynatyze NBA dynasty rankings — freshest board available, but the free tier is shallow and has no points-league view. Only external price on future picks.
---

# Dynatyze

**Corroboration for elite players only** — daily, but ~70 free rows and no points view.
Sanity-check that `dizzle-dynasty` / `hashtag-basketball` aren't stale on a top-tier
player; never a primary board, never past the free tier, **never in the BASE blend**
(`Eval Definitions §BASE`: reference only).

## Fetch in a subagent

Run the recipe — and any fallback read of the dated snapshot in
`strategy/board-snapshots/Boards 2026-07-29.md` — inside a dedicated `Agent` call
(`general-purpose`), never inline. Have it hand back `SOURCE`/`UPDATED`/`ROWS` plus the
table; raw page content never enters the main context (`CLAUDE.md` §*Subagents*).

**Future picks are the one exception** — the only external price on one anywhere. Two
surfaces:

- **Inline `PICK`/`DRAFT` rows** on the dynasty board, already in the recipe's output (same
  `/basketball/players/` href). Coarse `Early`/`Mid 1st` buckets only. Read them even when
  they rank past the players we'd use.
- **`/basketball/pick-rankings` — the full board**, every slot × round × year at our league
  shape, so slot labels map 1:1 with no ordinal conversion. **Client-rendered; `curl`
  returns nothing.** Each row expands to a panel printing an **implied dynasty rank**, an
  uncertainty band, a per-cell trade weight `w`, and a per-year class-strength dial with
  its own stamp.

Two properties to carry into pricing (`eval-pick/future-picks.md` owns the method):

- **The slot curve is a parametric template, numerically identical across years** — only
  the 1.01 anchor and the trade blend are class-specific, so **its shape carries no class
  information.**
- **`w = 0` means the cell is that template alone, with no market in it.** Published per
  cell; near-year 1sts and later-year 2nds differ sharply.

**Year label = NBA class year.** `<YEAR>` is the draft our league holds that September
(`FetchLeagueDraftBoard?season=<YEAR>`), set by the **preceding** season's finish. Restate
it that way in output (`get-league-info`).

`WebFetch` 403s; `curl -L` with a browser UA works. Only
`/basketball/dynasty-rankings` is server-rendered — `rookie-rankings` (advertises pick
values 1–60), `expert-consensus` and `pick-rankings` render client-side and return **no
data** to curl. For the first two, don't retry and don't cite marketing copy as data;
`pick-rankings` carries real data, so render it (`agent-browser`). `/llms.txt` is the URL
index if new pages are needed.

## Recipe — run the file, never retype it

```bash
python3 .claude/skills/dynatyze/board.py
```

**Do not transcribe, reimplement or "fix" what is in that file.** Its row pattern is
correct as written; it sends the browser UA and asserts the page identity. A tripped
`assert` means discard the pull, not caveat it.

```bash
python3 .claude/skills/dynatyze/test_parse.py    # offline parse guard, no network
```

Report `SOURCE` / `UPDATED` / `ROWS` verbatim when citing.

⚠️ **`DYNVAL` is not BASE.** The site's value column is a normalised scale that **also
tops out at 9,999**, so it looks like `Eval Definitions`' `VALUE` and is a different quantity.
Keep the recipe's rename, never label it `VALUE`, and **never compare or blend it with
BASE, Hashtag's Keeper Value, or Dizzle's tiers.** Only the **rank** crosses boards.

**Rows can come back fewer than the top rank** — the gaps are hydrated client-side (the
incoming rookie class), not withheld ranks. Re-render before concluding a player is
missing; absence never means "low value", nor "outside the free tier".

Dated ranks, including the pick rows: `strategy/board-snapshots/Boards 2026-07-29.md`.
