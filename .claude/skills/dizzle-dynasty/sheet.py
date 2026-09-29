# /// script
# dependencies = ["openpyxl"]
# ///
# Dizzle Dynasty rankings sheet, one tab (dizzle-dynasty).
#   uv run .claude/skills/dizzle-dynasty/sheet.py "Dynasty Ranks, Points" [LIMIT]
#   uv run .claude/skills/dizzle-dynasty/sheet.py     # no tab argument lists tabs
#
# xlsx export on purpose: `gviz/tq?sheet=<name>` silently falls back to the first
# tab (9Cat) on an unknown name, HTTP 200. DO NOT swap in gviz. The `visible`
# assert catches hidden tabs, which are stale archives of an earlier month.
import io, re, sys, urllib.request, datetime, openpyxl
ID = '1EmReTa5KUcFFMCy8Fq-NpQG3WU0pMY7XNW54G3EPbEM'
want = sys.argv[1] if len(sys.argv) > 1 else None
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 40

raw = urllib.request.urlopen(
    f'https://docs.google.com/spreadsheets/d/{ID}/export?format=xlsx', timeout=90).read()
wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)

if not want:
    for ws in wb.worksheets:
        print(f'{ws.sheet_state:8} {ws.title}')
    sys.exit()

hits = [ws for ws in wb.worksheets if want.lower() in ws.title.lower()]
assert len(hits) == 1, f'"{want}" matched {[w.title for w in hits]} — be more specific'
ws = hits[0]
assert ws.sheet_state == 'visible', f'"{ws.title}" is HIDDEN = stale archive — do not use'

rows = [r for r in ws.iter_rows(values_only=True) if any(c is not None for c in r)]
assert rows, 'NO ROWS'
head = [str(c) if c is not None else '' for c in rows[0]]
stamp = next((m.group(1) for c in head for m in [re.search(r'Updated\s*([\d/]+)', c)] if m), None)
fmt = 'POINTS' if 'points' in ws.title.lower() else '9CAT' if '9cat' in ws.title.lower() else 'n/a'

print(f'SOURCE   Dizzle Dynasty ({ID})')
print(f'TAB      {ws.title}  [{ws.sheet_state}]')
print(f'FORMAT   {fmt}   UPDATED {stamp or "see tab name"}   ROWS {len(rows) - 1}')
print('\t'.join(head))

def cell(v, pick=False):
    if v is None: return ''
    if isinstance(v, datetime.datetime): return v.date().isoformat()
    # Pick labels are floats in the sheet: 1.10 -> 1.1, 2.30 -> 2.30000000000004
    if pick and isinstance(v, (int, float)): return f'{v:.2f}'
    if isinstance(v, float):
        return f'{v:.2f}'.rstrip('0').rstrip('.') if v % 1 else str(int(v))
    return str(v)

picks = head[0].strip() == 'Pick'
for r in rows[1:limit + 1]:
    print('\t'.join(cell(c, picks and i == 0) for i, c in enumerate(r)))
