---
description: Dynatyze — use when pulling Dynatyze NBA dynasty rankings (elite-player corroboration) or its future-pick board
---

**Corroboration for elite players only**: daily, but ~70 free rows and no points view. Use it to sanity-check that `dizzle-dynasty` / `hashtag-basketball` aren't stale on a top-tier player; never a primary board, never past the free tier, **never in the BASE blend** (`Eval Definitions §BASE`: reference only). **Exception: future picks**, where it's the only external price anywhere (§Future picks).

## Fetch

1. Run the recipe (or the snapshot fallback) in a `general-purpose` subagent (`AGENTS.md` §Subagents); it hands back `SOURCE`/`UPDATED`/`ROWS` plus the table, never raw page content.
2. Done when the pull printed its header with no tripped `assert`. Report `SOURCE` / `UPDATED` / `ROWS` verbatim when citing.

```bash
python3 .claude/skills/dynatyze/board.py
python3 .claude/skills/dynatyze/test_parse.py    # offline parse guard, no network
```

**Run `board.py` as-is; never transcribe, reimplement or "fix" it.** Its row pattern is correct as written; it sends the browser UA and asserts the page identity. A tripped `assert` means discard the pull, not caveat it.

**Snapshots:** `strategy/board-snapshots/dynatyze/` (dated `player-board-*.txt` and `pick-board-*.tsv`; `eval-pick`'s `pick_prices.py` reads the newest `pick-board-*.tsv`) and `strategy/board-snapshots/Boards 2026-07-29.md` (dated ranks incl. pick rows).

## Site access

`WebFetch` 403s; `curl -L` with a browser UA works. Only `/basketball/dynasty-rankings` is server-rendered. `rookie-rankings` (advertises pick values 1–60), `expert-consensus` and `pick-rankings` render client-side and return **no data** to curl: for the first two, move on without retrying and cite no marketing copy as data; `pick-rankings` carries real data, so render it (`browser` Skill). `/llms.txt` is the URL index if new pages are needed.

**Rows can come back fewer than the top rank**: the gaps (the incoming rookie class) hydrate client-side; they aren't withheld ranks. Re-render before concluding a player is missing; absence never means "low value", nor "outside the free tier".

⚠️ **`DYNVAL` is not BASE.** The site's value column is a normalised scale that **also tops out at 9,999**, so it looks like `Eval Definitions`' `VALUE` but is a different quantity. Keep the recipe's rename, never label it `VALUE`, and **never compare or blend it with BASE, Hashtag's Keeper Value, or Dizzle's tiers.** Only the **rank** crosses boards.

## Future picks

Two surfaces:

- **Inline `PICK`/`DRAFT` rows** on the dynasty board, already in the recipe's output (same `/basketball/players/` href). Coarse `Early`/`Mid 1st` buckets only. Read them even when they rank past the players we'd use.
- **`/basketball/pick-rankings`: the full board**, every slot × round × year at our league shape (toggle `12tm` + `R1`–`R4`), so slot labels map 1:1 with no ordinal conversion. **Client-rendered; `curl` returns nothing.** Each row expands to a panel printing an **implied dynasty rank**, an uncertainty band, a per-cell trade weight `w`, and a per-year class-strength dial with its own stamp.

Carry into pricing (`eval-pick/future-picks.md` owns the method):

- **The slot curve is a parametric template, numerically identical across years**: only the 1.01 anchor and the trade blend are class-specific, so **its shape carries no class information.**
- **`w = 0` means the cell is that template alone, with no market in it.** Published per cell; near-year 1sts and later-year 2nds differ sharply.

**Year label = NBA class year.** `<YEAR>` is the draft our league holds that September (`FetchLeagueDraftBoard?season=<YEAR>`), set by the **preceding** season's finish. Restate it that way in output (`get-league-info`).
