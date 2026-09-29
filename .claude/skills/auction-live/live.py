"""Live rookie draft + FA auction off the commissioner's Sheet. See auction-live.md.

  live.py once    one read: sync sales.tsv/drafted.tsv, rewrite dashboard.md and dashboard.html, print status
  live.py watch   poll; print event lines only when a pick or sale lands
  live.py q NAME [PRICE]  one line on a player, verdict first: bid to <cap>, out or pass; then live Market$,
                        top rival Max Bids. During the rookie draft a rookie gets its board facts
"""
import argparse
import csv
import difflib
import math
import pathlib
import re
import statistics
import sys
import time
import unicodedata
from itertools import takewhile
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / 'google-sheets'))
import sheets  # noqa: E402

import page  # noqa: E402

SHEET_ID = '1-AZXzFGxJ7eRC2QdPNhYEZmUBsBdaF0DBrrjcx_fEgg'
REPO = pathlib.Path(__file__).resolve().parents[3]
DIR = REPO / 'strategy' / 'auction-2026'
US = 'Brett'
EVERY = 3  # seconds between Sheet reads
OURS = "Δw '26–'27 ours"
ROOKIE_PICKS = 36  # until they land, the best undrafted 2026-class rows by BASE count as drafted
TIE = 100  # rookie board BASE gaps up to this are noise (`Rookie Draft 2026.md` §At 2.09)
MID_AT = 0.5  # share of the league's auction spots filled before we nominate from the Mid list
HEAT_N, HEAT_MIN = 8, 5  # rival sales the room heat averages, and how many it needs before it reads
BUBBLE = (278, -98)  # scores of Drummond, Chaney: cut candidates alongside our buys
ROSTER, ROSTER_MAX = 36, 38  # our roster once the pending Hlina deals land (Sheet 34, Duren deal +2), and our max
DRAIN_MIN = 5  # least live Market$ on a pass row we nominate: our $1 opening bid wins it if nobody bids
UNSAFE = {'fa', 'noproj'}  # values.tsv flags that keep a row off our targets and nominations
BUDGET = 200  # per team, before any sale
TRADED = {'2.9': 'Hlina'}  # pick: owner, for deals the Sheet's labels lag (485845 executes draft day)
SUFFIX = {'jr', 'sr', 'ii', 'iii', 'iv'}
# First keyword hit wins: 'jesus' before 'chris' ("Jesus Christ"), 'mongol' before 'han' ("Mongol Khans").
OWNERS = [('bathroom', US), ('jesus', 'Josh'), ('chris', 'Chris'), ('pascal', 'Bonin'), ('don', 'Mitch'),
          ('mongol', 'Henry'), ('han', 'Todd'), ('shai', 'Jon'), ('sga', 'Jon'), ('pharaoh', 'Matthew'),
          ('apostle', 'Hlina'), ('gutes', 'Joe'), ('yao', 'Brian')]


def owner(team, default=None):
    t = team.lower()
    return next((o for k, o in OWNERS if k in t), team.strip() if default is None else default)


def words(name):
    """Lowercase ascii words; drops accents, zero-width chars, apostrophes, dots and Jr./Sr./II."""
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r"['.]", '', s)
    return [w for w in re.split(r'[^a-z0-9]+', s) if w and w not in SUFFIX]


def resolver(names, aliases=()):
    """name -> values.tsv spelling, or None. `aliases` ((sheet text, name) pairs) win, then the exact name, then
    a unique (initial +) surname or close surname, then the one close spelling. A `(tag)` is dropped"""
    exact = {''.join(words(n)): n for n in names}
    exact.update((''.join(words(a)), n) for a, n in aliases if n in names)
    by_last = {}
    for n in names:
        by_last.setdefault(words(n)[-1], []).append(n)

    def resolve(text):
        w = words(re.sub(r'\([^)]*\)', '', text))
        if not w:
            return None
        if ''.join(w) in exact:
            return exact[''.join(w)]
        hits = by_last.get(w[-1], [])
        if len(w) == 1 and not hits:
            near = difflib.get_close_matches(w[0], by_last, n=2, cutoff=0.85)
            hits = by_last[near[0]] if len(near) == 1 else []
        elif len(w) == 2 and len(w[0]) == 1:
            hits = [n for n in hits if words(n)[0].startswith(w[0])]
        elif len(w) > 1:
            hits = []
        if len(hits) == 1:
            return hits[0]
        close = difflib.get_close_matches(''.join(w), exact, n=2, cutoff=0.85)
        return exact[close[0]] if len(close) == 1 else None
    return resolve


def budgets(rows):
    """{owner: ($ left, spots left, Max Bid)} from the Sheet's formula rows; Max Bid is 0 once full. A text price makes
    a team's `Total budget` and `Max Bid` read `#VALUE!`, and `Open roster spots` skip it; all three then come from the
    team's priced sales."""
    at = {r[0].strip(): r for r in rows if r and r[0].strip() in ('Total budget', 'Max Bid', 'Open roster spots')}
    head = rows[rows.index(at['Total budget']) - 1]
    spent, text = {}, {}
    for _, o, x, cell in sheet_sales(rows):
        spent[o] = spent.get(o, 0) + int(x or 0)
        text[o] = text.get(o, 0) + bool(x and not re.fullmatch(r'\$?\d+(\.\d+)?', cell))
    out = {}
    for c in range(0, len(head), 2):
        num = lambda label: dollars(at[label][c + 1])  # noqa: E731
        o, spots = owner(head[c]), num('Open roster spots')
        left = num('Total budget')
        if left is None:
            left, spots = BUDGET - spent.get(o, 0), spots - text.get(o, 0)
        hard = num('Max Bid')
        out[o] = (left, spots, 0 if not spots else left - spots + 1 if hard is None else hard)
    return out


def dollars(cell):
    """12 from `12`, `$12`, `$12.00` or `-3`; None from anything else (`#VALUE!`, `12 ish`)."""
    m = re.fullmatch(r'(-?)\$?\s*(\d+)(\.0+)?', cell.strip())
    return int(m.group(1) + m.group(2)) if m else None


def sheet_sales(rows):
    """[(player, owner, $, price cell)] in Sheet order, for every name with a price cell. $ = the cell's first digits
    (`85?`, `?85` and `85.5` are $85), or None when it has none (`sold`): not a sale."""
    head = rows[next(i for i, r in enumerate(rows) if r and r[0].strip() == 'Total budget') - 1]
    hdr = next(i for i, r in enumerate(rows) if r and r[0].strip() == 'PLAYER')
    out = []
    for r in rows[hdr + 1:hdr + 16]:
        for c in range(0, len(head), 2):
            price = re.search(r'\d+', r[c + 1])
            if r[c].strip() and r[c + 1].strip():
                out.append((r[c].strip(), owner(head[c]), price and price.group(), r[c + 1].strip()))
    return out


def rookie_grid(rows, rookies, aliases=()):
    """[(pick, owner, player or None)] for every slot of the rookie grid, in pick order. A name goes in a pick's
    label cell or the cell below"""
    top = next(i for i, r in enumerate(rows) if r and r[0].strip() == 'ROOKIE DRAFT') + 1
    end = next(i for i, r in enumerate(rows) if i > top and any(' – ' in c for c in r))
    head, resolve = rows[top], resolver(rookies, aliases)
    keys = {''.join(words(n)): n for n in rookies}
    slots = {}
    for c in range(0, len(head), 2):
        pick = None
        for r in rows[top + 1:end]:
            text = r[c].strip()
            label = re.match(r'(\d)\.\d+', text)
            if label:
                pick, text = f'{label.group(1)}.{c // 2 + 1}', text[label.end():]
                k = ''.join(words(text))
                name = next((n for kk, n in keys.items() if kk in k), None)
                slots[pick] = [owner(k.replace(''.join(words(name)), '') if name else k, owner(head[c])), name]
            elif text and pick:
                slots[pick][1] = resolve(text) or text
    return sorted(((p, TRADED.get(p, o), n) for p, (o, n) in slots.items()),
                  key=lambda x: tuple(map(int, x[0].split('.'))))


def merge(path, now):
    """(rows `path` holds, `now` in their order with new rows last)"""
    old = [tuple(r) for r in csv.reader(open(path, encoding='utf-8'), delimiter='\t')][1:] if path.exists() else []
    return old, [x for x in old if x in now] + [x for x in now if x not in old]


def sync(path, cols, now):
    """Rewrite `path` to `now` (kept rows keep their order); return (added, removed, rows as written)."""
    old, rows = merge(path, now)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(cols)
        w.writerows(rows)
    return [x for x in now if x not in old], [x for x in old if x not in now], rows


def load_aliases(d):
    path = d / 'aliases.tsv'
    return [tuple(r[:2]) for r in csv.reader(open(path, encoding='utf-8'), delimiter='\t')][1:] if path.exists() else []


def load_values(d):
    return list(csv.DictReader(open(d / 'values.tsv', encoding='utf-8'), delimiter='\t'))


def section(md, title):
    """Lines of the `## title` section of a markdown file."""
    lines = md.splitlines()
    i = next(i for i, x in enumerate(lines) if x.lstrip('#').strip() == title)
    return list(takewhile(lambda x: not x.startswith('#'), lines[i + 1:]))


def load_nominate(d, resolve):
    """{phase: [names]} from the `## Nominating` bullets of Auction 2026.md ("- **Early:** ... : A, B, C.")."""
    md = (d / 'Auction 2026.md').read_text(encoding='utf-8')
    out = {}
    for x in section(md, 'Nominating'):
        m = re.match(r'- \*\*(\w+):\*\*(.*)', x)
        if m and ':' in m.group(2):
            names = re.sub(r'\([^)]*\)', '', m.group(2).rsplit(':', 1)[1].split('.')[0]).split(',')
            out[m.group(1)] = [resolve(n) or '?' + n.strip() for n in names]
    return out


def load_board(d, resolve):
    """{values.tsv name: (Hashtag expert rank, Hashtag crowd rank, flags)} from `Rookie Draft 2026.md` beside `d`"""
    path = d.parent / 'Rookie Draft 2026.md'
    rows = [[c.strip() for c in x.strip().strip('|').split('|')]
            for x in path.read_text(encoding='utf-8').splitlines() if x.startswith('|')] if path.exists() else []
    head = next((r for r in rows if 'Player' in r), None)
    if not head:
        return {}
    rank = lambda c: int(re.sub(r'\D', '', c)) if re.search(r'\d', c) else None  # noqa: E731
    at = {h.strip('*()'): i for i, h in enumerate(head)}
    return {resolve(r[at['Player']]) or r[at['Player']]: (rank(r[at['Exp']]), rank(r[at['Crowd']]), r[at['Flags']])
            for r in rows if len(r) == len(head) and r[0].isdigit()}


def board_take(s):
    """(take, tied) among the rookies left: best BASE; within TIE BASE of it, the better September Hashtag rank"""
    left = [n for n in s.rookies if n not in s.gone]
    if not left:
        return None, []
    base = lambda n: float(s.by_name[n]['BASE'] or 0)  # noqa: E731
    tied = [n for n in left if base(left[0]) - base(n) <= TIE]
    hashtag = lambda n: [x for x in s.board.get(n, (None, None))[:2] if x] or [math.inf]  # noqa: E731
    take = min(tied, key=lambda n: statistics.mean(hashtag(n)))
    return take, [n for n in tied if n != take]


def board_facts(s, n):
    exp, crowd, flags = s.board.get(n, (None, None, ''))
    return f"BASE {s.by_name[n]['BASE']} · Hashtag {exp or '—'}/{crowd or '—'}" + (f' · {flags}' if flags else '')


def our_pick(s):
    nxt = next(((p, o) for p, o, n in s.slots if not n), None)
    if not nxt or nxt[1] != US:
        return None
    take, tied = board_take(s)
    return (f'OUR PICK {nxt[0]} · take {take} · {board_facts(s, take)}'
            + (' · tied ' + ', '.join(f"{n} {s.by_name[n]['BASE']}" for n in tied) if tied else ''))


def target(row):
    """True if we bid on the row: its `score` beats a $1 body, and it is neither unsigned nor unprojected (UNSAFE)."""
    score = (row.get('score') or '').strip()
    return bool(score) and float(score) > 0 and not UNSAFE & set(row['flag'].split(' · '))


def price(values, gone, teams):
    """Live Market$ for every row: 1 + (Market$ - 1) x k, k = spare $ / Σ(Market$ - 1) over the top (spots left) rows."""
    left, spots = sum(t[0] for t in teams.values()), sum(t[1] for t in teams.values())
    pool = sorted((r for r in values if r['name'] not in gone), key=lambda r: -float(r['Market$']))
    denom = sum(float(r['Market$']) - 1 for r in pool[:spots])
    k = (left - spots) / denom if denom else 1.0
    return k, {r['name']: round(1 + (float(r['Market$']) - 1) * k) for r in values}


def cap(s, n):
    """Our max on a card row (`Auction 2026.md` §Bidding): the most we can pay for n and, with the best buys left priced
    as `best()` prices them, still keep the roster Score `best()` keeps without n, up to hard max. ≤ 0 = no bid"""
    left, spots, hard = s.us
    if not spots:
        return 0
    need = best(s, s.held, spots, left, n)
    bought = lambda price: best(s, s.held + [score(s, n)], spots - 1, left - price, n)  # noqa: E731
    if bought(1) <= need:
        return 0  # n adds nothing: it is cut, or no better than the plan without it
    lo, hi = 1, hard  # bought() falls as the price rises: bisect for the last fit
    while lo < hi:
        mid = (lo + hi + 1) // 2
        lo, hi = (mid, hi) if bought(mid) >= need else (lo, mid - 1)
    return lo


def score(s, n):
    """values.tsv `score`; 0, like a $1 body, for a name it lacks"""
    return float(s.by_name[n].get('score') or 0) if n in s.by_name else 0.0


def best(s, held, spots, left, but=None):
    """Most summed `score` our roster keeps after the cuts. Candidates: `held` (scores of our buys), the unsold card
    rows (not `but`) that `spots` hold at live Market$ × hot room heat on $`left`, $1 bodies (0) in the rest, and
    BUBBLE. The cuts take the lowest, one per player over ROSTER_MAX"""
    cuts = max(0, len(held) + spots + ROSTER - ROSTER_MAX)
    reach = {(0, 0): 0.0}  # (rows, $) -> summed score
    for m in (m for m in s.card if m != but and s.avail(m)):
        for (rows, cost), total in list(reach.items()):
            key = (rows + 1, cost + round(s.live[m] * s.heat))
            if key[0] <= spots and key[1] + spots - key[0] <= left:
                reach[key] = max(reach.get(key, -math.inf), total + score(s, m))
    return max(total + sum(sorted([*held, *BUBBLE] + [0] * (spots - rows))[cuts:]) for (rows, _), total in reach.items())


def state(rows, d):
    """Everything the dashboard, status line and `q` read. Reads files, writes nothing."""
    s = SimpleNamespace(teams=budgets(rows), values=load_values(d))
    s.us = s.teams[US]
    s.by_name = {r['name']: r for r in s.values}
    aliases = load_aliases(d)
    s.resolve = resolver(list(s.by_name), aliases)
    rookies = [r['name'] for r in sorted(s.values, key=lambda r: -float(r['BASE'] or 0)) if "'26 class" in r['flag']]
    sales = sheet_sales(rows)
    s.sales = [(s.resolve(p) or p, t, x) for p, t, x, _ in sales if x]
    s.odd_prices = [(s.resolve(p) or p, cell) for p, _, _, cell in sales if dollars(cell) is None]
    s.rookies = rookies
    s.slots = rookie_grid(rows, rookies, aliases)
    s.picks = [(n, o, p) for p, o, n in s.slots if n]
    board = d / 'draft-board.tsv'  # Fleaflicker's draft, for when the commissioner never logs it on the Sheet
    if not s.picks and board.exists():
        s.picks = [(s.resolve(r['player']) or r['player'], r['team'], r['pick'])
                   for r in csv.DictReader(open(board, encoding='utf-8'), delimiter='\t')]
    s.draft_done = all(n for _, _, n in s.slots) or bool(s.sales)  # a sale means a passed pick stays empty
    s.board = load_board(d, s.resolve)
    s.sold = {p: (t, x) for p, t, x in s.sales}
    s.held = [score(s, p) for p, t, _ in s.sales if t == US]
    s.drafted = {p: (t, x) for p, t, x in s.picks}
    s.gone = s.sold.keys() | s.drafted.keys()
    s.card = sorted((r['name'] for r in s.values if target(r)), key=lambda n: -float(s.by_name[n]['score']))
    # an empty grid means the commissioner never logged the draft: keep the top rookies by BASE out
    picks_to_come = [] if s.draft_done and s.picks else [n for n in rookies if n not in s.gone][:ROOKIE_PICKS - len(s.picks)]
    s.not_in_pool = s.gone | set(picks_to_come)
    s.k, s.live = price(s.values, s.not_in_pool, s.teams)
    s.avail = avail = lambda n: n in s.by_name and n not in s.not_in_pool  # noqa: E731
    _, log = merge(d / 'sales.tsv', s.sales)
    s.heat = max(1.0, room(s, log)[0] or 1.0)
    s.rivals = sorted(((o, t) for o, t in s.teams.items() if o != US and t[1] > 0), key=lambda x: -x[1][2])
    top_rival = max((t[2] for _, t in s.rivals), default=0)
    s.endgame = next((n for n in s.card if avail(n) and cap(s, n) > top_rival), None) if s.us[1] else None
    s.nominee = nominee(s, load_nominate(d, s.resolve))
    sold = [p for p, _, _ in s.sales]
    s.warns = ((['no scored rows in values.tsv'] if not s.card else [])
               + ['price ' + ' · '.join(f'"{c}" {p}' for p, c in s.odd_prices)] * bool(s.odd_prices)
               + [f'?{p}' for p, _, _ in s.sales if p not in s.by_name]
               + [f'dup {p}' for p in dict.fromkeys(sold) if sold.count(p) > 1])
    return s


def nominee(s, lists):
    """Our next nomination per `Auction 2026.md` §Nominating, as `name (phase)`, or None once we are full"""
    if not s.us[1]:
        return None
    filled = len(s.sales) / (len(s.sales) + sum(t[1] for t in s.teams.values()))
    ours = [n for n in lists.get('Mid', []) + s.card if n in s.card and s.avail(n)]
    mid = next((n for n in ours if cap(s, n) > 0), None)
    drain = [r['name'] for r in sorted(s.values, key=lambda r: -s.live[r['name']]) if r['name'] not in s.not_in_pool]
    safe = lambda n: (s.live[n] >= DRAIN_MIN and not UNSAFE & set(s.by_name[n]['flag'].split(' · '))  # noqa: E731
                      and not (n in s.card and cap(s, n) > 0))  # a $0-cap target left with us costs what a $1 body does
    early = next((n for n in lists.get('Early', []) + drain if s.avail(n) and safe(n)), None)
    if s.endgame:  # nobody can outbid us on it, and rival max bids only fall: drain them first
        return f'{early} (early)' if early and s.us[1] > 1 else f'{s.endgame} (ENDGAME)'  # a stuck drain can't take our last spot
    if mid and (filled >= MID_AT or s.us[1] == 1 or not early):
        return f'{mid} (mid)'
    return f"{early or '?'} (early)"


def room(s, log):
    """(Σ(price − 1) / Σ(expected − 1), n) over the last HEAT_N rival sales expected at ≥ $5, before the forced fill.
    Expected = the live Market$ just before the sale, replayed from the log; ratio None until HEAT_MIN such sales"""
    paid = expected_total = n = 0
    for i in range(len(log) - 1, -1, -1):
        p, t, x = log[i]
        if n == HEAT_N:
            break
        if t == US or p not in s.by_name:
            continue
        later = log[i:]
        teams = {o: (left + sum(int(y) for _, u, y in later if u == o), spots + sum(1 for _, u, _ in later if u == o), 0)
                 for o, (left, spots, _) in s.teams.items()}
        spots_left = [spots for _, spots, _ in teams.values()]
        forced_fill = sum(spots_left) <= 2 * sum(1 for x in spots_left if x)
        if forced_fill:
            continue
        k, _ = price(s.values, s.not_in_pool - {q for q, _, _ in later}, teams)
        expected = 1 + (float(s.by_name[p]['Market$']) - 1) * k
        if expected >= 5:
            paid, expected_total, n = paid + int(x) - 1, expected_total + expected - 1, n + 1
    return (paid / expected_total if n >= HEAT_MIN else None), n


def room_label(s, log):
    r, n = room(s, log)
    if r is None:
        return f'room ? {n}/{HEAT_MIN}'
    return f"room {r:.2f}× {'hot' if r >= 1.15 else 'cold' if r <= 0.87 else 'even'} ({n})"


def status(s, log):
    top = next(((n, c) for n in s.card if s.avail(n) and (c := cap(s, n)) > 0), None) if s.us[1] else None
    return (f'{room_label(s, log)} · us ${s.us[0]}/{s.us[1]} max {s.us[2]}'
            + (f' · best {top[0]} cap {top[1]}' if top else '')
            + (f' · nom {s.nominee}' if s.nominee else '')
            + ''.join(f' · WARN {w}' for w in s.warns))


def dashboard(s, log):
    out = [f'# Auction live · {room_label(s, log)} · {time.strftime("%H:%M:%S")}', '',
           f'**Us** ${s.us[0]} · {s.us[1]} spots · max bid {s.us[2]}',
           f'**Nominate** {s.nominee or "-"}', *(f'**WARN {w}**' for w in s.warns), '',
           '## Card: Score, live Market$, gap, our cap', '', '| Player | Score | Mkt | Gap | Cap |',
           '|---|---:|---:|---:|---:|']
    for n in s.card:
        if n in s.sold:
            out.append(f'| ~~{n}~~ {s.sold[n][0]} ${s.sold[n][1]} | | | | |')
        elif n in s.drafted:
            out.append(f'| ~~{n}~~ drafted {s.drafted[n][0]} | | | | |')
        elif n in s.not_in_pool:
            out.append(f'| {n} (in the draft) | | | | |')
        else:
            out.append(f"| {n} | {s.by_name[n]['score']} | {s.live[n]} | {gap(s, n):+d} | {cap(s, n)} |")
    out += ['', '## Rivals: max bid · $ left · spots', '']
    out += [f'- {o} {t[2]} · ${t[0]} · {t[1]}' for o, t in s.rivals]
    out += ['', '## Last sales', ''] + [f'- {p} → {t} ${x}' for p, t, x in log[::-1][:8]]
    out += ['', '## Top unsold: live Market$ · BASE · Δw ours', '',
            '| Player | Mkt | BASE | ours |', '|---|---:|---:|---:|']
    top = sorted((r for r in s.values if r['name'] not in s.not_in_pool), key=lambda r: -s.live[r['name']])[:25]
    out += [f"| {r['name']} | {s.live[r['name']]} | {r['BASE']} | {r[OURS]} |" for r in top]
    return '\n'.join(out) + '\n'


def gap(s, n):
    """values.tsv `gap` (Score$ − Market$) at the live multiplier: > 0 = the room underprices the row against our Score."""
    return round(float(s.by_name[n]['gap']) * s.k)


def query(s, text):
    """One line, verdict first (`bid to <cap>`, `out` on a trailing price ≥ cap, or `pass`), then live
    Market$ and the rivals who can pay the most"""
    m = re.fullmatch(r'(.*?)\s+\$?(\d+)', text.strip())
    text, at = (m.group(1), int(m.group(2))) if m else (text, None)
    k = ''.join(words(text))
    hits = [s.resolve(text)] if s.resolve(text) else [n for n in s.by_name if k in ''.join(words(n))]
    if len(hits) != 1:
        return f'{text} · ' + (f'ambiguous: {", ".join(hits[:6])}' if hits else 'not in values.tsv')
    n = hits[0]
    if n in s.sold:
        return f'{n} · sold {s.sold[n][0]} ${s.sold[n][1]}'
    if n in s.drafted:
        return f'{n} · drafted {s.drafted[n][0]} {s.drafted[n][1]}'
    if n in s.rookies and not s.draft_done:
        return f'{n} · rookie · {board_facts(s, n)}'
    c = cap(s, n) if n in s.card else 0
    verdict = 'pass' if c <= 0 else f'out at {at} (cap {c})' if at is not None and at >= c else f'bid to {c}'
    r = s.by_name[n]
    scored = f" · score {r['score']} gap {gap(s, n):+d}" if r['score'] else ''
    return (f"{n} · {verdict} · mkt {s.live[n]} · rivals "
            + ' '.join(f'{o} {t[2]}' for o, t in s.rivals[:3]) + f"{scored} · BASE {r['BASE']} ours {r[OURS]}")


def once(rows, d, always=True):
    """Sync sales.tsv/drafted.tsv, rewrite dashboard.md and dashboard.html; return event lines + status. The status
    follows sales, UNDOs and the draft's end, or every read when `always`"""
    s = state(rows, d)
    new_picks, undone_picks, _ = sync(d / 'drafted.tsv', ('player', 'team', 'pick'), s.picks)
    added, removed, log = sync(d / 'sales.tsv', ('player', 'team', '$'), s.sales)
    html = page.render(s, log, room_label(s, log), cap, gap)
    for name, text in (('dashboard.md', dashboard(s, log)), ('dashboard.html', html)):
        tmp = d / f'.{name}.tmp'
        tmp.write_text(text, encoding='utf-8')
        tmp.replace(d / name)
    tag = lambda p: p if p in s.by_name else '?' + p  # noqa: E731
    pick = our_pick(s)
    grid_full = all(n for _, _, n in s.slots)
    draft_just_done = len(added) == len(log) and (new_picks and grid_full or added and not grid_full)  # no sale before
    return ([f'DRAFTED {tag(p)} → {t} {x}' for p, t, x in new_picks]
            + [f'UNDO {tag(p)} → {t} {x}' for p, t, x in undone_picks]
            + ([pick] if pick else [])
            + (['DRAFT DONE'] if draft_just_done else [])
            + [f'SOLD {tag(p)} → {t} ${x} (mkt {s.live.get(p, "?")})' for p, t, x in added]
            + [f'UNDO {tag(p)} → {t} ${x}' for p, t, x in removed]
            + ([status(s, log)] if always and not (new_picks or undone_picks) or added or removed or draft_just_done else []))


def watched(rows):
    """The part of the Sheet a pick or sale changes: everything above the FA list."""
    end = next((i for i, r in enumerate(rows) if r and r[0].startswith('AVAILABLE FREE AGENTS')), len(rows))
    return rows[:end]


def beat(d):
    """beat.js: when the Sheet was last read, and which dashboard.html is current. The page polls it."""
    html = d / 'dashboard.html'
    tmp = d / '.beat.js.tmp'
    tmp.write_text(f'window.BEAT = {{t: {time.time():.3f}, v: {html.stat().st_mtime if html.exists() else 0:.3f}}};\n')
    tmp.replace(d / 'beat.js')


def watch(src, d, every):
    """Print event lines + status whenever a pick or sale lands; timings go to stderr."""
    t0 = time.monotonic()

    def fetch():
        nonlocal t0
        t0 = time.monotonic()
        rows = sheets.read(src)
        beat(d)
        return rows

    first = True
    for rows, err in sheets.poll(fetch, every, key=watched):
        t1 = time.monotonic()
        try:
            lines = [f'ERR sheet read: {str(err)[:120]}'] if err else once(rows, d, always=first)
            first = first and bool(err)
        except Exception as e:  # layout changed under us: say so, keep polling
            lines = [f'ERR parse: {type(e).__name__} {str(e)[:120]}']
        if lines:
            print('\n'.join(lines), flush=True)
        print(f'{time.time():.3f} fetch {1000 * (t1 - t0):.0f}ms tick {1000 * (time.monotonic() - t1):.0f}ms',
              file=sys.stderr, flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['once', 'watch', 'q'])
    ap.add_argument('name', nargs='*', help='q: a player, optionally followed by the current price')
    ap.add_argument('--src', default=sheets.export_url(SHEET_ID))
    ap.add_argument('--dir', type=pathlib.Path, default=DIR)
    ap.add_argument('--every', type=float, default=EVERY)
    a = ap.parse_args(argv)
    if a.cmd == 'watch':
        return watch(a.src, a.dir, a.every)
    rows = sheets.read(a.src)
    print(query(state(rows, a.dir), ' '.join(a.name)) if a.cmd == 'q' else '\n'.join(once(rows, a.dir)))


if __name__ == '__main__':
    main()
