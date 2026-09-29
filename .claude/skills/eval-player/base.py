# BASE (eval-team's VALUE) per player: Dizzle Points and Hashtag Points blended
# through the rank curve, Hashtag crowd printed beside them, off the committed
# snapshots in strategy/. Re-cut those first if they are stale
# (hashtag-basketball, dizzle-dynasty) -- this reads them, it does not fetch.
#
#   python3 .claude/skills/eval-player/base.py "Cade Cunningham" "Kyrie Irving"
#   python3 .claude/skills/eval-player/base.py --roster strategy/lineup-math/rosters/roster-161025-2025-26.json \
#       --absent "Chaney Johnson"                 # every name in a fetch_data.py roster file
#   ... "Jaylin Williams:OKC"                     # NAME:TEAM where a name is two players
#   ... --roster-size 28                          # D = teams x roster_size, default announced 38
#
# It REFUSES rather than returning BASE 0 for a player off all three boards, and refuses
# rather than guessing between two players with one name. Both are the same silent error:
# a failed join is indistinguishable from a real 0, and it has shipped as one twice.
# `--absent NAME` is how you record a 0 you have hand-checked on each board.
#
# Curve and depth rule are eval-team's. Blend weights: BASE.md.
# Guard, offline: python3 .claude/skills/eval-player/test_base.py
import csv, glob, json, math, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.join(HERE, os.pardir, os.pardir, os.pardir, 'strategy')
TEAMS, ROSTER_SIZE = 12, 38          # league-info: announced post-Sept '26 size

MONTHS = ('january february march april may june july august september october november'
          ' december').split()


class Refused(Exception):
    """Something base.py will not guess past. Printed as its own line, not as a
    traceback: the message IS the output, and it has to survive `python -O`."""


def refuse(msg):
    raise Refused(msg)


def newest(d, suffix='dynasty-ranks-points.csv'):
    """Newest `<month>-<year>-<suffix>` in `d`. NEVER hardcode the month: dizzle-dynasty
    re-snapshots under a new one and the old file stays put, so a hardcoded name goes
    stale in place while every rank in the eval keeps resolving. Raises, never falls back.
    """
    found = []
    for p in glob.glob(os.path.join(d, '*-' + suffix)):
        m = re.match(r'([a-z]+)-(\d{4})-', os.path.basename(p))
        if m and m.group(1) in MONTHS:
            found.append(((int(m.group(2)), MONTHS.index(m.group(1))), p))
    if not found:
        refuse(f'NO SNAPSHOT — no <month>-<year>-{suffix} in {d}')
    return max(found)[1]


BOARDS = [
    ('dizP', 0.40, newest(os.path.join(EVALS, 'board-snapshots', 'dizzle-dynasty')), '#', 'Player', 'Team'),
    ('htP', 0.35, os.path.join(EVALS, 'board-snapshots', 'hashtag-basketball',
                               'expert-dynasty-points.csv'), 'rank', 'player', 'team'),
    ('crd', 0, os.path.join(EVALS, 'board-snapshots', 'hashtag-basketball',
                            'crowd-keeper.csv'), 'rank', 'player', 'team'),
]


def curve(D):
    """-> a, V(). eval-team: rank a is worth half of rank 1, and 0 at or past D."""
    a = math.sqrt(D)
    return a, lambda r: 0.0 if r >= D else 9999 * (a + 1) / (D - 1) * (D - r) / (a + r)


# Spellings no normalisation can reach: nicknames, and boards that disagree with each
# other letter for letter. Both sides run through `key`, so this is any spelling -> the
# one key they all have to land on, one line per name, each hand-checked on all three
# boards. Suffixes and accents do NOT belong here -- `key` already folds those.
ALIAS = {'bub carrington': 'carlton carrington',
         'ronald holland': 'ron holland',
         'alex sarr': 'alexandre sarr',
         'terrance shannon': 'terrence shannon',   # dizzle's a, hashtag's and the league's e
         'nic claxton': 'nicolas claxton',
         'ayo dosumnu': 'ayo dosunmu',
         'khaman malauch': 'khaman maluach',
         'bogoljbub markovic': 'bogoljub markovic',  # dizzle's typo
         'david jones garcia': 'david jones',        # league's full name, hashtag's short
         'nikola urisic': 'nikola djurisic'}         # NFKD drops Đ outright


def key(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    s = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b', '',
               s.lower().replace('.', '').replace("'", '').replace('-', ' '))
    s = ' '.join(s.split())
    return ALIAS.get(s, s)


def load(path, rankcol, namecol, teamcol):
    rows = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            r = row[rankcol]
            if r and r.isdigit():
                rows.setdefault(key(row[namecol]), []).append((int(r), row[teamcol]))
    return rows


def stamp(path):
    """The board's own UPDATED stamp, off whichever provenance its snapshot carries.

    Never the file's mtime: the refresh rewrites all of them, and a board can be a
    month older than the pull that captured it.
    """
    manifest = os.path.join(os.path.dirname(path), 'manifest.csv')
    if os.path.exists(manifest):
        with open(manifest, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                if row['file'] == os.path.basename(path):
                    return row['board_updated']
    with open(path, newline='', encoding='utf-8') as f:      # dizzle: in the header row
        m = re.search(r'Updated\s*([\d/]+)', next(f))
    if not m:
        refuse(f'NO UPDATED STAMP in {path} — provenance unknown, DISCARD')
    return m.group(1)


# Board spelling -> the spelling the league files use. The boards disagree with each
# other and with Fleaflicker, and the near-misses are all real franchises: SA is the
# Spurs and SAC the Kings, PHO the Suns and PHI the 76ers, LAL and LAC different teams.
# So the match is normalise-then-equality, never a prefix. (sim.py's FF2ESPN, inverted.)
NBA = {'SA': 'SAS', 'PHO': 'PHX', 'GS': 'GSW', 'NO': 'NOP', 'NY': 'NYK',
       'BRK': 'BKN', 'WSH': 'WAS', 'UTAH': 'UTA', 'CHO': 'CHA'}


def franchises(cell):
    """Every franchise a team cell names. Dizzle publishes rows mid-move as
    `ATL -> PHO` (and one as `IND -> CHI - MIL`), which is one player at either end
    of the move depending on how fresh the league file is, so both ends count.
    """
    return {NBA.get(t, t) for t in re.findall(r'[A-Za-z]+', cell.upper())}


def pick(hits, team, strict):
    """The one row for this player, or None if he is off the board.

    Team only ever breaks a tie (`eval-player`), and a lone row is taken as-is.
    `strict` is set for a name that collides on ANY board — then the name is not a key
    on any of them, so a lone row still has to match the team or he counts as off that
    board. An unresolved tie refuses: a wrong row is a silent 400-place error.
    """
    if not hits or (len(hits) < 2 and not strict):
        return hits[0][0] if hits else None
    want = franchises(team)
    best = [h for h in hits if want & franchises(h[1])]
    if not best:
        return None                      # strict, and none of these rows is his
    if len(best) > 1:
        refuse('AMBIGUOUS — %s matches %s, and the board itself cannot tell them apart'
               % (team, hitlist(best)))
    return best[0][0]


def hitlist(hits):
    return ', '.join(f'{t or "no team"} #{r}' for r, t in hits)


def roster(path):
    """A fetch_data.py roster file as [(label, name, team)]. Anything else refuses:
    a rate-limited fetch lands as HTML, and an empty table is a whole team priced at
    nothing with no row to notice it by.
    """
    try:
        with open(path, encoding='utf-8') as f:
            rows = json.load(f)
    except (OSError, ValueError) as e:
        refuse(f'BAD --roster {path} — {e}')
    if not (isinstance(rows, list) and rows
            and all(isinstance(p, dict) and 'n' in p and 'tm' in p for p in rows)):
        refuse(f'BAD --roster {path} — expected fetch_data.py\'s non-empty list of '
               '{"n": name, "tm": team}')
    return [(p['n'], p['n'], p['tm']) for p in rows]


def parse(argv):
    """-> ([(label, name, team)], {confirmed-absent key: as spelled}, roster_size)."""
    who, absent, size, it = [], {}, ROSTER_SIZE, iter(argv)

    def val(flag):
        v = next(it, None)
        if v is None:
            refuse(f'{flag} WITH NO VALUE — it takes the next argument')
        return v

    for a in it:
        if a == '--absent':
            n = val(a)
            absent[key(n)] = n
        elif a == '--roster-size':
            size = val(a)
            if not size.isdigit() or not int(size):
                refuse(f'BAD --roster-size {size!r} — D = teams x roster_size is the '
                       'whole scale, and a size under 1 puts every rank past D, so the '
                       'table reads 0 for everybody')
            size = int(size)
        elif a == '--roster':
            who += roster(val(a))
        else:
            n, _, t = a.partition(':')
            who.append((a, n, t))
    return who, absent, size


def main(argv):
    boards = [(n, w, load(p, rc, nc, tc)) for n, w, p, rc, nc, tc in BOARDS]
    depth = {n: max(r for hits in b.values() for r, _ in hits) for n, _, b in boards}
    names, absent, size = parse(argv)
    D = TEAMS * size
    A, V = curve(D)
    collide = {k for _, _, b in boards for k, hits in b.items() if len(hits) > 1}

    out, blind = [], []
    for label, who, team in names:
        k = key(who)
        if k in collide and not team:
            refuse('AMBIGUOUS — %r is two different players, so pass NAME:TEAM: %s'
                   % (who, '; '.join(f'{n} {hitlist(b[k])}'
                                     for n, _, b in boards if k in b)))
        ranks = [pick(b.get(k) or [], team, k in collide) for _, _, b in boards]
        if not any(r is not None for r in ranks) and k not in absent:
            blind.append(f'{label} ({team or "no team given"})')
        num = tot = 0.0
        for (n, w, _), r in zip(boards, ranks):
            if r is None and depth[n] < D:
                continue                 # absence and below-depth indistinguishable
            num, tot = num + w * (V(r) if r is not None else 0.0), tot + w
        out.append((label, k, ranks, round(num / tot) if tot else 0))

    # A hand-check on a name nobody here has confirms nothing, so it is a typo, and the
    # player it was meant for is back to being an unexplained 0.
    stray = [n for k, n in absent.items() if k not in {k for _, k, _, _ in out}]
    if stray:
        refuse('--absent NAMES NOBODY BEING PRICED — nothing was hand-checked by: '
               + ', '.join(stray))

    # And a hand-check the boards have since outlived announces a BASE 0 over a row that
    # prints real ranks. Drop the flag; it is describing an absence that ended.
    found = [lb + ' (' + ', '.join(f'{n} #{r}' for (n, _, _), r in zip(boards, ranks)
                                   if r is not None) + ')'
             for lb, k, ranks, _ in out
             if k in absent and any(r is not None for r in ranks)]
    if found:
        refuse('--absent ON A PLAYER THE BOARDS CARRY — no longer off all 3: '
               + ', '.join(found))

    # A missed join is indistinguishable from a real 0, so 0 is asked for, never returned.
    if blind:
        refuse('OFF ALL 3 BOARDS, so BASE would read 0 — search each surname on each '
               'board before believing it (eval-player -> Joining names):\n  '
               + '\n  '.join(blind))

    print('BASE     blended points-format dynasty board rank and nothing else (eval-team)')
    print(f'CURVE    D = {TEAMS} x {size} = {D}   a = sqrt(D) = {A:.3f}   '
          'V(r) = 9999*(a+1)/(D-1)*(D-r)/(a+r), 0 at or past D')
    print(f'SIZE     roster_size {size} (league-info) — BASE compares only within '
          'one D, so re-run every eval when it moves')
    for (n, w, _), (_, _, p, _, _, _) in zip(boards, BOARDS):
        if not w:
            print(f'{n:8} printed  {os.path.basename(p)}  UPDATED {stamp(p)}  '
                  f'DEPTH {depth[n]}  not in the blend')
            continue
        rule = ('< D, so absence renormalises this weight away' if depth[n] < D
                else '>= D, so absence here is a value of 0')
        print(f'{n:8} {w:.0%}  {os.path.basename(p)}  UPDATED {stamp(p)}  '
              f'DEPTH {depth[n]}  {rule}')
    if absent:
        print('ABSENT   BASE 0 as hand-checked, not as a failed join: '
              + ', '.join(lb for lb, k, _, _ in out if k in absent))
    print('PLAYER\t' + '\t'.join(n for n, _, _ in boards) + '\tBASE')
    for label, _, ranks, base in out:
        print(f'{label}\t' + '\t'.join('-' if r is None else str(r) for r in ranks)
              + f'\t{base}')


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Refused as e:
        sys.exit(f'\nREFUSED  {e}')      # the message, on stderr, and nothing else
