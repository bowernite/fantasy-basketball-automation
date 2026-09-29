---
description: Run the live rookie draft and FA auction off the commissioner's Google Sheet. Polls it, keeps sales and picks in sync, reprices, rewrites the dashboard, and makes bid and nominate calls. Use when Brett starts the draft or auction, or asks about a player during it.
---

Plan and spend rules: `strategy/auction-2026/Auction 2026.md`. Reading Sheets: `google-sheets` Skill. The Sheet is `1-AZXzFGxJ7eRC2QdPNhYEZmUBsBdaF0DBrrjcx_fEgg`, gid 0, read only.

`L` = `python3 /Users/brett/src/personal/fantasy-basketball/.claude/skills/auction-live/live.py`

## Start

1. Run `L once`. It prints the status line. Fix any `WARN`, `?name` or `ERR` first. From here to the end of the auction, nothing rewrites `values.tsv`.
2. Arm a `Monitor`:
   - command: `L watch 2>>$TMPDIR/auction-watch.err`
   - `timeout_ms`: 1800000
   - description: `auction Sheet: picks and sales`
   - Re-arm the moment it expires. A restart only prints what changed against the tsv files.
3. Tell Brett to open `strategy/auction-2026/dashboard.md` or `dashboard.html` (every pool row, name filter; reloads only when a pick or sale lands, and flags a dead watcher from `beat.js`, which `watch` rewrites every read). Both are rewritten within ~3.5 s of every pick or sale, without waiting on you.

## Files

All in `strategy/auction-2026/`:

- `values.tsv`, `Auction 2026.md`, `aliases.tsv` and `../Rookie Draft 2026.md` are re-read on every change, so edits take effect at the next pick or sale.
  - `values.tsv`: `Market$`, `score`, `dPtitle`, `gap`, `BASE`. The card is every target (`Auction 2026.md` §Targets), by Score. Before the draft ends, rookies it will take show as `(in the draft)`.
  - `Auction 2026.md`: nomination lists come from the bullets under `## Nominating`, in the form `- **Phase:** … : A, B, C.`
  - `aliases.tsv`: `sheet<TAB>name`, one row per Sheet spelling that stays unresolved.
- `sales.tsv` and `drafted.tsv` mirror the Sheet. The Sheet wins, and hand edits get overwritten.
- Drafted rookies drop out on their own. Leave their rows in `values.tsv`.

## Staying responsive

- After a context compaction, reload this skill. Re-arm the Monitor if it is gone.

- Brett's question comes before anything else, including Monitor lines.
- While the draft or auction runs, only run commands that finish in ~1 s: `L q`, reads of `dashboard.md` or `sales.tsv`, and appending to `aliases.tsv`. No tests, sims, sleeps, waits or other blocking commands. The Monitor does the waiting.
- Answer Monitor lines from their own text, with no tool call.

## Monitor lines

- `DRAFTED P → Owner 2.9`: during the rookie draft this line comes alone.
- `OUR PICK 2.9 · take P · BASE · Hashtag expert/crowd · flags · tied …`: we're on the clock. The take follows `Rookie Draft 2026.md` §At 2.09. We hold no '26 picks: 2.09 is Hlina's (485845), so this doesn't fire this year. `TRADED` relabels picks the Sheet still shows under the old owner.
- `DRAFT DONE`, then the status line: at the last pick, or at the first sale if a pick was passed.
- `SOLD P → Owner $12 (mkt 15)`: `mkt` is the live `Market$` after the sale.
- `UNDO …`: the commissioner fixed a cell.
- `ERR sheet read|parse …`: printed once per streak.
- `WARN price "85?" P`: a price with text or cents. It counts as its first digits (`?85` is $85). With no digits (`sold`, `$`) it isn't a sale. Tell Brett once so the commissioner fixes it.
- `WARN dup P`: P is sold to two teams on the Sheet. Tell Brett once so the commissioner fixes it.
- `?P`: no `values.tsv` row matched. Status and dashboard carry `WARN ?P` until it resolves. Resolve it with `L q`. If the Sheet keeps the typo past the next sale, add it to `aliases.tsv` and tell Brett.
- Status follows every sale, UNDO and `DRAFT DONE`, and nothing else: `room 1.12× even (8) · us $175/3 max 173 · best P cap 87 · nom P (early|mid|ENDGAME) [· WARN …]`
  - `room`: rival prices over our live `Market$` (`Auction 2026.md` §Live). `room ? 3/5` until 5 sales count. Above 1, it prices the rest of the plan in every cap.
  - `max`: hard max, 0 once we're full.
  - `best`: the top-Score card row still worth a bid, and our cap on it.
  - `nom`: our next nomination (`Auction 2026.md` §Nominating).

Reply to Brett in at most 2 lines, and only when it changes what he does:

- `OUR PICK`: give the take, plus any flag or tie.
- `nom … (ENDGAME)`: say it.
- A target sells, or we buy: give `best` and its cap.
- `room` turns hot, cold or even: say it once.
- `ERR`: say it once. If it lasts past 1 min, use Fallback.
- `DRAFTED`: stay silent.

## Brett asks

- "X up": run `L q X` and relay the verdict (`bid to <cap>` or `pass`). The line also carries `score` and the live `gap` (`Pricing.md`).
- "X at 14": run `L q X 14` and relay the verdict (`bid to <cap>`, `out at 14 (cap …)` or `pass`).
- Quote caps only from `L q` or `dashboard.md`. The caps in `Auction 2026.md` are the blank-Sheet opening.
- A sale the Sheet doesn't show yet isn't in any cap. Say so when you give one.
- A rookie during the draft: `L q X` gives its BASE, Hashtag ranks and flags.
- "Nominate?": the `nom` field.
- Anything else: `L q`, `dashboard.md` or `sales.tsv`. Never load `values.tsv` whole.

## Code

`live.py` holds the plan's arithmetic. `price()` is the live multiplier `k`. Until all 36 picks land or the first sale shows, `k` counts the best undrafted 2026-class rows by BASE as drafted, and the plan, card and top unsold leave them out. `target()` is §Targets. `best()` is the plan's roster Score: our buys, the plan's rows at live `Market$` × heat (above 1), $1 bodies at 0 and `BUBBLE` (Drummond, Matković, Chaney), less the cuts, the lowest one per player over 38. `cap()` is §Bidding: the most we pay and still match `best()` without the row, up to hard max, and 0 when the row adds nothing. `page.py` renders `dashboard.html`. `gap()` is the live gap. `nominee()` is §Nominating. `room()` is the room heat. `board_take()` is the 2.09 rule. When the plan changes, update the code and `test_live.py` together.

Tests: `python3 .claude/skills/auction-live/test_live.py` and `test_page.py`. They run on `fixtures/`: the real blank Sheet from 2026-09-24 and copies of `values.tsv`, `Auction 2026.md` and `Rookie Draft 2026.md`. Re-copy them when they change.

## Sheet layout

Everything is found from label cells, not row numbers.

- Rookie grid: under `ROOKIE DRAFT`, with one column pair per team in draft order. A label like `1.9THE DON` means that team owns the pick. The name goes in the label cell or the cell below it.
- Auction:
  - The row above `Total budget` holds the team names.
  - `Total budget` (the $ left), `Max Bid` and `Open roster spots` are formulas over the 15 sale rows under `PLAYER`, so the Sheet is the ledger.
  - A text price makes that team's `Total budget` and `Max Bid` read `#VALUE!`, and `Open roster spots` skip it. All three then come from its priced sales.
  - A name with no digit in its price cell doesn't count as a sale.
  - The budget formula skips the 15th sale row.
- The FA list under `AVAILABLE FREE AGENTS` is ignored.
- `OWNERS` maps team names to owners by keyword. An unknown team name shows up as its raw header.

## Names

`words()` converts to NFKD ascii, lowercases, and drops `'`, `’`, `.`, zero-width characters and Jr/Sr/II/III/IV. A `(tag)` is dropped. A name matches on the exact key first, then on a unique surname (with an initial if one is given), or for one word the one close surname, then on the one close spelling.

## Fallback

If the Sheet can't be read, Brett downloads it with File > Download > CSV. Run `L once --src <csv>` after each sale he reports.
