# Dynatyze dynasty rankings, free tier (dynatyze).
#   python3 .claude/skills/dynatyze/board.py
#
# The row pattern captures PICK/DRAFT rows too — same `/basketball/players/`
# href as players. Ranks are non-contiguous and rows < top rank: the gaps
# hydrate client-side (dynatyze.md), not a parse failure. DO NOT "fix" it.
# Guard, offline: python3 .claude/skills/dynatyze/test_parse.py
import re, html, urllib.request
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
url = 'https://dynatyze.com/basketball/dynasty-rankings'
h = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}),
                           timeout=60).read().decode('utf-8', 'replace')

title = html.unescape(re.search(r'<title>([^<]*)</title>', h).group(1))
assert 'Dynasty Rankings' in title and 'Dynatyze' in title, f'WRONG PAGE: {title}'
upd = re.search(r'<time dateTime="([\d-]+)"', h)
scope = re.search(r'·\s*([^<]{0,40}ranked)', h)
rows = re.findall(
    r'tabular-nums text-muted-foreground">(\d+)</span>'
    r'<a[^>]*href="(/basketball/players/[^"]*)"[^>]*>([^<]*)</a>'
    r'<span[^>]*>([^<]*)</span><span[^>]*>([^<]*)</span><span[^>]*>([^<]*)</span>', h)
assert rows, 'NO ROWS PARSED — markup changed, do not guess'
picks = [r for r in rows if r[3] == 'PICK']
# >= 2, not == 2: the two known future-1st rows must parse, but Dynatyze adding a
# third (a Late 1st) is new data, not a broken pull — hard-failing the whole board
# over it would discard 68 good player rows. The count prints so a new row is seen.
assert len(picks) >= 2, f'{len(picks)} pick rows, want >=2 — DISCARD: {[r[2] for r in picks]}'

print(f'SOURCE   Dynatyze ({url})')
print(f'TITLE    {title}')
print(f'UPDATED  {upd.group(1) if upd else "??"}   {scope.group(1).strip() if scope else ""}')
print(f'ROWS     {len(rows)}  (free tier cap — not a full board)')
print('#\tPLAYER\tPOS\tTEAM\tDYNVAL')
for r in rows:
    print(f'{r[0]}\t{html.unescape(r[2])}\t{r[3]}\t{r[4]}\t{r[5]}')
