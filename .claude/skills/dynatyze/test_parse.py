# Offline guard for the dynasty-rankings row parse. No network.
# python3 .claude/skills/dynatyze/test_parse.py
# python3 .claude/skills/dynatyze/test_parse.py --record   (re-cut fixtures)
#
# Runs board.py against recorded real markup and diffs its output against a recorded
# snapshot, then asserts each documented "fix" of the row parse still trips an assert —
# or, for the withheld ranks, the snapshot — instead of yielding a quietly wrong board.
import difflib
import io
import pathlib
import re
import runpy
import sys
import urllib.request
from contextlib import redirect_stdout

HERE = pathlib.Path(__file__).parent
SCRIPT = HERE / 'board.py'
FIX = HERE / 'fixtures'
PAGE = FIX / 'dynasty-rankings.html'
SNAP = FIX / 'dynasty-rankings.expected.txt'

# The documented "fix"es, as source mutations.
TIGHTEN_POS_AND_TEAM = (r"r'<span[^>]*>([^<]*)</span><span[^>]*>([^<]*)</span>",
                        r"r'<span[^>]*>([FGC]+)</span><span[^>]*>([A-Z]{3})</span>")
RENUMBER_RANKS = ('for r in rows:\n' + r"    print(f'{r[0]}\t",
                  'for i, r in enumerate(rows, 1):\n' + r"    print(f'{i}\t")
DROP_CLOSING_SPAN = (r"r'<span[^>]*>([^<]*)</span><span",
                     r"r'<span[^>]*>([^<]*)<span")
SPACE_AT_THE_LITERAL_SEAM = (r"([^<]*)</a>'", r"([^<]*)</a> '")


def run_script(page, source=None):
    """Run board.py with urlopen stubbed to serve `page`. Returns stdout."""
    real = urllib.request.urlopen
    urllib.request.urlopen = lambda req, timeout=None: io.BytesIO(page)
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            if source is None:
                runpy.run_path(str(SCRIPT), run_name='__main__')
            else:
                exec(compile(source, str(SCRIPT), 'exec'), {'__name__': '__main__'})
    finally:
        urllib.request.urlopen = real
    return buf.getvalue()


def data_rows(out):
    """The board's own rows, split on tabs — header lines don't start with a digit."""
    return [l.split('\t') for l in out.splitlines() if l[:1].isdigit()]


def mutate(find, replace):
    src = SCRIPT.read_text()
    out = src.replace(find, replace, 1)
    assert out != src, f'mutation no longer applies, pattern moved: {find}'
    return out


def test_parses_recorded_board():
    got = run_script(PAGE.read_bytes())
    want = SNAP.read_bytes().decode()
    assert got == want, '\n' + '\n'.join(difflib.unified_diff(
        want.splitlines(), got.splitlines(), 'recorded', 'now', lineterm=''))


def test_demanding_real_pos_and_team_loses_the_pick_rows():
    try:
        run_script(PAGE.read_bytes(), mutate(*TIGHTEN_POS_AND_TEAM))
    except AssertionError as e:
        assert 'pick rows, want' in str(e), e
    else:
        raise AssertionError('tightened columns still found 2 pick rows — guard is dead')


def test_a_dropped_closing_span_parses_nothing():
    try:
        run_script(PAGE.read_bytes(), mutate(*DROP_CLOSING_SPAN))
    except AssertionError as e:
        assert 'NO ROWS PARSED' in str(e), e
    else:
        raise AssertionError('a dropped </span> still parsed the board — guard is dead')


def test_a_space_between_two_adjacent_tags_parses_nothing():
    """The tags really are adjacent; the row literals are concatenated, not joined."""
    try:
        run_script(PAGE.read_bytes(), mutate(*SPACE_AT_THE_LITERAL_SEAM))
    except AssertionError as e:
        assert 'NO ROWS PARSED' in str(e), e
    else:
        raise AssertionError('a space at the </a><span seam still parsed — guard is dead')


def test_renumbering_the_withheld_ranks_is_caught():
    """Rows < top rank with gaps is the site withholding ranks. No assert covers it —
    the snapshot does, so the fixture has to keep the gaps."""
    want = SNAP.read_bytes().decode()
    ranks = [int(r[0]) for r in data_rows(want)]
    assert ranks == sorted(ranks) and len(ranks) < max(ranks), f'fixture lost the gaps: {ranks}'
    got = run_script(PAGE.read_bytes(), mutate(*RENUMBER_RANKS))
    assert [int(r[0]) for r in data_rows(got)] == list(range(1, len(ranks) + 1)), 'inert mutation'
    assert got != want, 'renumbered ranks still matched the snapshot — guard is dead'


def record():
    """Re-cut the fixture from the live board: verbatim <li> slices, nothing hand-typed."""
    UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
          '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
    h = urllib.request.urlopen(urllib.request.Request(
        'https://dynatyze.com/basketball/dynasty-rankings',
        headers={'User-Agent': UA}), timeout=60).read().decode('utf-8', 'replace')
    grab = lambda p: re.search(p, h).group(0)
    rows = re.findall(r'<li [^>]*>[\s\S]*?</li>', h)   # `<li[^>]*>` also eats `<link ...>`
    rows = [t for t in rows if '/basketball/players/' in t]
    keep, seen = [], set()
    for t in rows[:24] + [t for t in rows if '>PICK<' in t]:
        if t not in seen:
            seen.add(t)
            keep.append(t)
    page = ('<html><head>' + grab(r'<title>[^<]*</title>') + '</head><body>'
            + grab(r'<p class="mt-3 text-sm text-muted-foreground">[\s\S]*?</p>')
            + grab(r'<ol [^>]*>') + ''.join(keep) + '</ol></body></html>')
    FIX.mkdir(exist_ok=True)
    PAGE.write_bytes(page.encode())
    SNAP.write_bytes(run_script(page.encode()).encode())
    print(f'{len(keep)} rows -> {PAGE}\n{SNAP}')


if __name__ == '__main__':
    if '--record' in sys.argv[1:]:
        record()
        sys.exit()
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print(f'ok  {t.__name__}')
    print(f'{len(tests)} passed')
