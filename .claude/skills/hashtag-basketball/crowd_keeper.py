# Crowd keeper board + draft-pick bands (hashtag-basketball Recipe A).
#   python3 .claude/skills/hashtag-basketball/crowd_keeper.py [LIMIT]   # LIMIT default 60
#
# DO NOT EDIT THE ROW REGEX. It reads as if it holds two typos and holds none:
#   - the `</a></td><td>` seam between the two string literals is the real cell
#     boundary — the player name sits in an `<a>` inside the player `<td>`.
#   - every `([^<]*)` is permissive on purpose: pick rows fill team/pos/age with
#     `&nbsp;`, so demanding those columns silently drops all 8 pick bands.
# Guard, offline: python3 .claude/skills/hashtag-basketball/test_parse.py
import re, sys, html, urllib.request
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
URL = 'https://hashtagbasketball.com/keeper'
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 60
h = urllib.request.urlopen(urllib.request.Request(URL, headers={'User-Agent': UA}),
                           timeout=90).read().decode('utf-8', 'replace')

title = re.search(r'<title>([^<]*)</title>', h).group(1)
assert 'Dynasty' in title, f'WRONG PAGE: {title}'
rows = re.findall(r'<td>(\d+)</td><td class="mw200"><a href="/(\d+)/dynasty">([^<]*)</a></td>'
                  r'<td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td><td>(\d+)</td>', h)
assert rows, 'NO ROWS PARSED — markup changed, do not guess'
upd = re.search(r'Updated:</strong>\s*([^<]*)', h)
assert upd, 'NO Updated: STAMP — markup changed, DISCARD'
votes = re.search(r'([\d,]+) votes', h)
picks = [r for r in rows if r[3].strip() == 'DRA']
assert len(picks) == 8, f'{len(picks)} pick bands, want 8 — DISCARD: {[r[2] for r in picks]}'

print('BOARD    crowd keeper (/keeper)')
print(f'TITLE    {title}')
print(f'UPDATED  {upd.group(1).strip()}   votes={votes.group(1) if votes else "??"}')
print(f'ROWS     {len(rows)}   picks={len(picks)}')
c = lambda s: html.unescape(s).replace('\xa0', '').strip() or '-'
print('#\tPLAYER\tTEAM\tPOS\tAGE\tKVALUE')   # Keeper Value, NOT eval-team's VALUE/BASE
for r in rows[:limit]:
    print(f'{r[0]}\t{c(r[2])}\t{c(r[3])}\t{c(r[4])}\t{c(r[5])}\t{r[6]}')
print('\nDRAFT PICKS')
for r in picks:
    print(f'{r[0]}\t{r[2]}\t{r[6]}')
