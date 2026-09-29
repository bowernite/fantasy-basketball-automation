# Expert dynasty board, any control view (hashtag-basketball Recipe B).
#   python3 .claude/skills/hashtag-basketball/expert_dynasty.py DDTYPE=POINT DDSTAT=800 limit=40
#
# Dropdowns are ASP.NET postbacks — a query string is ignored, so the first
# control named becomes __EVENTTARGET and the rest ride along. Every asked-for
# control is re-read off the response and asserted: a bad value returns
# `Oops | Hashtag Basketball` at HTTP 200. DO NOT relax those asserts.
import re, sys, html, urllib.parse, urllib.request
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
URL = 'https://hashtagbasketball.com/fantasy-basketball-dynasty-rankings'
CTRL = ['DDSTAT', 'DDTYPE', 'DDFORECAST', 'DDPOS', 'DDPOSFROM', 'DDTSUM']
want = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)
limit = int(want.pop('limit', 40))

def fetch(data=None):
    hdrs = {'User-Agent': UA, 'Referer': URL}
    if data:
        hdrs['Content-Type'] = 'application/x-www-form-urlencoded'
    return urllib.request.urlopen(
        urllib.request.Request(URL, data=data, headers=hdrs), timeout=90
    ).read().decode('utf-8', 'replace')

def sel(h, c):
    s = re.search(r'<select[^>]*id="ContentPlaceHolder1_' + c + r'"[^>]*>([\s\S]*?)</select>', h)
    m = s and re.search(r'<option[^>]*selected[^>]*value="([^"]*)"', s.group(1))
    return m.group(1) if m else None

def hid(h, n):
    m = re.search(r'name="' + n + r'"[^>]*value="([^"]*)"', h)
    return html.unescape(m.group(1)) if m else ''

h = fetch()
if want:
    body = {'__EVENTTARGET': 'ctl00$ContentPlaceHolder1$' + list(want)[0],
            '__EVENTARGUMENT': '', '__LASTFOCUS': '',
            '__VIEWSTATE': hid(h, '__VIEWSTATE'),
            '__VIEWSTATEGENERATOR': hid(h, '__VIEWSTATEGENERATOR'),
            '__EVENTVALIDATION': hid(h, '__EVENTVALIDATION')}
    for c in CTRL:
        body['ctl00$ContentPlaceHolder1$' + c] = want.get(c) or sel(h, c) or ''
    h = fetch(urllib.parse.urlencode(body).encode())

title = re.search(r'<title>([^<]*)</title>', h).group(1)
assert 'Dynasty Rankings' in title, f'WRONG PAGE: {title}'
got = {c: sel(h, c) for c in CTRL}
bad = [f'{c}: asked {v}, page shows {got[c]}' for c, v in want.items() if got[c] != v]
assert not bad, 'CONTEXT MISMATCH — DISCARD: ' + '; '.join(bad)
cards = h.split('<div class="card dyn-card">')[1:]
assert cards, 'NO PLAYER CARDS'

upd = re.search(r'Updated:</strong>\s*([^<]*)', h)
print(f'BOARD    expert dynasty ({URL})')
print(f'TITLE    {title}')
print(f'UPDATED  {upd.group(1).strip() if upd else "??"}')
print('VERIFIED ' + '  '.join(f'{c}={got[c]}' for c in CTRL) + f'  cards={len(cards)}')
print(f'RANKCOL  rank below is the {got["DDTYPE"]} board ONLY')
print('#\tPLAYER\tPOS\tTEAM\tAGE\tKEEPER#\tKVALUE\tPTS/REB/AST/STL/BLK/TO')
for c in cards[:limit]:
    b = [x.strip() for x in re.findall(r'badge badge-light-secondary">([^<]*)<', c)]
    pos = [x for x in b if x in ('PG', 'SG', 'SF', 'PF', 'C')]
    age = next((x for x in b if x.endswith('yo')), '-')
    team = next((x for x in b if x not in pos and not x.endswith('yo')), '-')
    st = {m[1]: m[0] for m in re.findall(r'<div class="m [^"]*">([^<]*)<small>([^<]*)</small>', c)}
    pan = lambda l: (re.search(r'<strong>' + l + r'</strong><span class="v">([^<]*)<', c) or [None, '-'])[1]
    rank = re.search(r'dyn-rank">(\d+)', c).group(1)
    name = re.search(r'dyn-name">([^<]*)', c).group(1).strip()
    line = '/'.join(st.get(k, '-') for k in ('PTS', 'REB', 'AST', 'STL', 'BLK', 'TO'))
    print(f'{rank}\t{name}\t{"/".join(pos)}\t{team}\t{age}\t{pan("Keeper")}\t{pan("Keeper Value")}\t{line}')
