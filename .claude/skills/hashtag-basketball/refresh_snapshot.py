# Rewrites strategy/board-snapshots/hashtag-basketball/*.csv from both live boards.
#   python3 .claude/skills/hashtag-basketball/refresh_snapshot.py   # from the repo root
#
# Both boards are fetched and parsed before anything is written, so a tripped
# assert leaves the existing snapshot intact. Tripped assert = discard, not
# caveat. Carries the same row regex as crowd_keeper.py — see its header.
import csv, datetime, html, pathlib, re, urllib.parse, urllib.request
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
OUT = pathlib.Path('strategy/board-snapshots/hashtag-basketball')
assert OUT.is_dir(), f'run from the repo root — {OUT} not found'
CROWD = 'https://hashtagbasketball.com/keeper'
EXPERT = 'https://hashtagbasketball.com/fantasy-basketball-dynasty-rankings'
CTRL = ['DDSTAT', 'DDTYPE', 'DDFORECAST', 'DDPOS', 'DDPOSFROM', 'DDTSUM']
WANT = {'DDTYPE': 'POINT', 'DDSTAT': '800'}   # order matters: first key is __EVENTTARGET
now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')

def get(url, data=None):
    hdrs = {'User-Agent': UA, 'Referer': url}
    if data:
        hdrs['Content-Type'] = 'application/x-www-form-urlencoded'
    return urllib.request.urlopen(
        urllib.request.Request(url, data=data, headers=hdrs), timeout=90
    ).read().decode('utf-8', 'replace')

def sel(h, c):
    s = re.search(r'<select[^>]*id="ContentPlaceHolder1_' + c + r'"[^>]*>([\s\S]*?)</select>', h)
    m = s and re.search(r'<option[^>]*selected[^>]*value="([^"]*)"', s.group(1))
    return m.group(1) if m else None

def hid(h, n):
    m = re.search(r'name="' + n + r'"[^>]*value="([^"]*)"', h)
    return html.unescape(m.group(1)) if m else ''

txt = lambda s: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()
cell = lambda s: html.unescape(s).replace('\xa0', '').strip()

def stamp(h):
    m = re.search(r'Updated:</strong>\s*([^<]*)', h)
    assert m, 'NO Updated: STAMP — markup changed, DISCARD'
    return m.group(1).strip()

def notice(h):
    for m in re.finditer(r'class="alert-body"[^>]*>([\s\S]{0,600}?)</div>', h):
        t = txt(m.group(1))
        if 'draft class' in t.lower():
            return t
    return ''

# ---- crowd keeper board (Recipe A) ----------------------------------------
h = get(CROWD)
ctitle = re.search(r'<title>([^<]*)</title>', h).group(1)
assert 'Dynasty' in ctitle, f'WRONG PAGE: {ctitle}'
raw = re.findall(r'<td>(\d+)</td><td class="mw200"><a href="/(\d+)/dynasty">([^<]*)</a></td>'
                 r'<td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td><td>(\d+)</td>', h)
assert raw, 'NO ROWS PARSED — markup changed, do not guess'
cupd, cnotice = stamp(h), notice(h)
votes = re.search(r'([\d,]+) votes', h)
picks = [r for r in raw if r[3].strip() == 'DRA']
assert len(picks) == 8, f'{len(picks)} pick bands, want 8 — DISCARD: {[r[2] for r in picks]}'
crowd = [[r[0], cell(r[2]), r[1], cell(r[3]), cell(r[4]).replace(',', '/'), cell(r[5]), r[6]]
         for r in raw]

# ---- expert dynasty board, Points view (Recipe B) -------------------------
h = get(EXPERT)
body = {'__EVENTTARGET': 'ctl00$ContentPlaceHolder1$' + list(WANT)[0],
        '__EVENTARGUMENT': '', '__LASTFOCUS': '',
        '__VIEWSTATE': hid(h, '__VIEWSTATE'),
        '__VIEWSTATEGENERATOR': hid(h, '__VIEWSTATEGENERATOR'),
        '__EVENTVALIDATION': hid(h, '__EVENTVALIDATION')}
for c in CTRL:
    body['ctl00$ContentPlaceHolder1$' + c] = WANT.get(c) or sel(h, c) or ''
h = get(EXPERT, urllib.parse.urlencode(body).encode())
etitle = re.search(r'<title>([^<]*)</title>', h).group(1)
assert 'Dynasty Rankings' in etitle, f'WRONG PAGE: {etitle}'
got = {c: sel(h, c) for c in CTRL}
bad = [f'{c}: asked {v}, page shows {got[c]}' for c, v in WANT.items() if got[c] != v]
assert not bad, 'CONTEXT MISMATCH — DISCARD: ' + '; '.join(bad)
cards = h.split('<div class="card dyn-card">')[1:]
assert cards, 'NO PLAYER CARDS'
eupd, enotice = stamp(h), notice(h)
STATS = ['FG%', 'FT%', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TO']
expert = []
for c in cards:
    b = [x.strip() for x in re.findall(r'badge badge-light-secondary">([^<]*)<', c)]
    pos = [x for x in b if x in ('PG', 'SG', 'SF', 'PF', 'C')]
    age = next((x for x in b if x.endswith('yo')), '')
    team = next((x for x in b if x not in pos and not x.endswith('yo')), '')
    st = {m[1]: m[0].strip() for m in
          re.findall(r'<div class="m [^"]*">([^<]*)<small>([^<]*)</small>', c)}
    pan = lambda l: (re.search(r'<strong>' + l + r'</strong><span class="v">([^<]*)<', c)
                     or [None, ''])[1].lstrip('#')
    expert.append([re.search(r'dyn-rank">(\d+)', c).group(1),
                   re.search(r'dyn-name">([^<]*)', c).group(1).strip(),
                   '/'.join(pos), team, age.removesuffix('yo'),
                   pan('Keeper'), pan('Keeper Value')] + [st.get(k, '') for k in STATS])

# ---- write ----------------------------------------------------------------
def dump(name, header, rows):
    p = OUT / name
    with p.open('w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([header] + rows)
    print(f'{len(rows):>4} rows -> {p}')

dump('crowd-keeper.csv',
     ['rank', 'player', 'hashtag_id', 'team', 'pos', 'age', 'keeper_value'], crowd)
dump('expert-dynasty-points.csv',
     ['rank', 'player', 'pos', 'team', 'age', 'keeper_rank', 'keeper_value']
     + [s.lower().replace('%', '_pct') for s in STATS], expert)
mx = lambda rows: max(int(r[0]) for r in rows)
dump('manifest.csv',
     ['board', 'file', 'title', 'source_url', 'controls', 'board_updated', 'fetched_utc',
      'rows', 'max_rank', 'pick_bands', 'votes', 'class_loading_notice'],
     [['crowd-keeper', 'crowd-keeper.csv', ctitle, CROWD, 'GET', cupd, now,
       len(crowd), mx(crowd), len(picks),
       votes.group(1).replace(',', '') if votes else '', cnotice],
      ['expert-dynasty-points', 'expert-dynasty-points.csv', etitle, EXPERT,
       ' '.join(f'{c}={got[c]}' for c in CTRL), eupd, now,
       len(expert), mx(expert), '', '', enotice]])
