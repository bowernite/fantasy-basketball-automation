# Dizzle Dynasty — local snapshot

Offline copy of the Dizzle Dynasty rankings sheet, in case the source goes away.
It is a public Google Sheet owned by someone else and could be moved, restricted
or overwritten at any time.

- **Source:** `https://docs.google.com/spreadsheets/d/1EmReTa5KUcFFMCy8Fq-NpQG3WU0pMY7XNW54G3EPbEM`
- **Snapshotted:** 2026-07-29
- **Author's own update stamps:** dynasty tabs 7/10/2026 · rookie Points tab 7/7/2026
- **Live fetch:** `dizzle-dynasty` Skill. Use that first; fall back here only if
  the sheet is unreachable, and say you're citing a snapshot.

`dizzle-dynasty.xlsx` is the unmodified download — the CSVs are derived from it,
so it's the thing to re-parse if a column is ever misread.

## Files

Our league is **points**, so the `-points` files are the ones to use. The `9cat`
files are the same author and exist only for cross-checking.

| File | Rows | What |
|---|---|---|
| `july-2026-dynasty-ranks-points.csv` | 466 | **Main board.** Full dynasty ranking |
| `july-2026-dynasty-ranks-9cat.csv` | 465 | Same board, 9-cat scoring |
| `july-2026-rookie-ranks-points.csv` | 70 | Incoming class + college stats |
| `july-2026-rookie-ranks-9cat.csv` | 70 | Same, 9-cat |
| `pick-values.csv` | 60 | Picks 1.01–2.30 |
| `archive/` | — | Tabs hidden in the source = superseded. Historical only |

Row counts exclude the header. Dynasty counts include `TIER BREAK` rows.

## Columns

**Dynasty tabs** — `#`, `Player`, `Position`, `Team`, `DOB`, `Age`,
`Prev. Rank`, `+/- Change`, `Notes/Outlook`.

**Rookie tabs** — the above plus `Tier`, `Projected Position(s)`,
`Position Rank`, `NBA Team`, `Draft Pick` (real NBA slot), `Contract Details`,
`Class`, and a college stat block: `GP MP FG% PTS 3PTA 3PTM REB AST STL BLK TO FT%`.

**`pick-values.csv`** — `Pick`, `Estimated Value`, `Who I Might Take (9Cat)`,
`Who I Might Take (Points)`.

## Gotchas

- **`TIER BREAK` rows** sit inline in the dynasty tabs with a blank `#`. Filter
  them out before ranking, keep them when reading tiers. 16 of them in the
  Points board.
- **`Estimated Value` is a player-rank equivalence, not a score** — `Top 15-25`
  means the pick is worth the player ranked 15th–25th on the dynasty board. It
  composes directly with the boards and needs no convex curve, unlike Hashtag's
  Keeper Value.
- **`Draft Pick` on the rookie tabs is the real NBA slot, not our draft.** Our
  rookie draft takes any player from the class in any order, so our slot N ≈ the
  Nth row, and `Who I Might Take (Points)` is the direct answer.
- `DOB` is ISO (`YYYY-MM-DD`); the source stores Excel date serials. `Age` is
  fractional years as of the author's update date.
- `archive/` tabs use a different column layout (leading blank column, age
  column names its own as-of date) and are months stale — never mix them into a
  current board.
- All tabs are **one analyst**, who also sits on Dynatyze's expert panel. The two
  formats are not two opinions. See "Caveats" in `evaluating-players`.

## Refresh

Overwrites everything here from the live sheet. Run from the repo root.

```bash
uv run --quiet --with openpyxl python - <<'PY'
import io, csv, re, datetime, urllib.request, pathlib, openpyxl
ID = '1EmReTa5KUcFFMCy8Fq-NpQG3WU0pMY7XNW54G3EPbEM'
OUT = pathlib.Path('evals/dizzle-dynasty')
assert OUT.is_dir(), f'run from the repo root — {OUT} not found'
(OUT / 'archive').mkdir(exist_ok=True)

raw = urllib.request.urlopen(
    f'https://docs.google.com/spreadsheets/d/{ID}/export?format=xlsx', timeout=90).read()
(OUT / 'dizzle-dynasty.xlsx').write_bytes(raw)
wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)

def cell(v, pick=False):
    if v is None: return ''
    if isinstance(v, datetime.datetime): return v.date().isoformat()
    # Pick labels are stored as floats: 1.10 -> 1.1, 2.30 -> 2.30000000000004
    if pick and isinstance(v, (int, float)): return f'{v:.2f}'
    if isinstance(v, float) and v.is_integer(): return str(int(v))
    return str(v)

slug = lambda s: re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')
for ws in wb.worksheets:
    rows = [r for r in ws.iter_rows(values_only=True) if any(c is not None for c in r)]
    picks = str(rows[0][0]).strip() == 'Pick'
    dest = (OUT if ws.sheet_state == 'visible' else OUT / 'archive') / f'{slug(ws.title)}.csv'
    with dest.open('w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(
            [[cell(c) for c in rows[0]]]
            + [[cell(c, picks and i == 0) for i, c in enumerate(r)] for r in rows[1:]])
    print(f'{ws.sheet_state:8} {len(rows):>4} rows -> {dest}')
PY
```

Tab names carry the month and change over time — the refresh derives filenames
from them, so **old months persist as stale files**. Delete files whose names no
longer match a visible tab after refreshing.
