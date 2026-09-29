# Offline guard for both recipe parses. No network.
# python3 .claude/skills/hashtag-basketball/test_parse.py
# python3 .claude/skills/hashtag-basketball/test_parse.py --record   (re-cut fixtures)
#
# Runs each recipe against recorded real markup and diffs its output against a
# recorded snapshot, then asserts the documented mis-edits still trip an assert
# instead of returning a partial board or the wrong board.
import difflib
import io
import pathlib
import re
import runpy
import sys
import urllib.parse
import urllib.request
from contextlib import redirect_stdout

HERE = pathlib.Path(__file__).parent
SCRIPT = HERE / 'crowd_keeper.py'
FIX = HERE / 'fixtures'
PAGE = FIX / 'crowd-keeper.html'
SNAP = FIX / 'crowd-keeper.expected.txt'
LIMIT = '40'

EXPERT = HERE / 'expert_dynasty.py'
EXP_GET = FIX / 'expert-dynasty.default.html'    # plain GET: whatever the page defaults to
EXP_POST = FIX / 'expert-dynasty.point.html'     # the postback's response: the POINT board
EXP_SNAP = FIX / 'expert-dynasty.expected.txt'
EXP_ARGS = ['DDTYPE=POINT', 'DDSTAT=800', 'limit=6']

# The two ways the pattern has actually been broken, as source mutations.
DROP_CLOSING_TD = (r'<td>([^<]*)</td><td>(\d+)</td>',
                   r'<td>([^<]*)<td>(\d+)</td>')
TIGHTEN_BLANK_COLUMNS = (r'<td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td>',
                         r'<td>([^<]*)</td><td>([\w,]+)</td><td>([\d.]+)</td>')

# The expert board's equivalents: sending the controls as a query string, and reading
# the dropdown's first <option> instead of its `selected` one.
QUERY_STRING_NOT_POSTBACK = ('h = fetch(urllib.parse.urlencode(body).encode())',
                             'h = fetch()')
FIRST_OPTION_NOT_SELECTED = (r'<option[^>]*selected[^>]*value="([^"]*)"',
                             r'<option[^>]*value="([^"]*)"')


def run_script(page, source=None):
    """Run crowd_keeper.py with urlopen stubbed to serve `page`. Returns stdout."""
    real, argv = urllib.request.urlopen, sys.argv
    urllib.request.urlopen = lambda req, timeout=None: io.BytesIO(page)
    sys.argv = [str(SCRIPT), LIMIT]
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            if source is None:
                runpy.run_path(str(SCRIPT), run_name='__main__')
            else:
                exec(compile(source, str(SCRIPT), 'exec'), {'__name__': '__main__'})
    finally:
        urllib.request.urlopen, sys.argv = real, argv
    return buf.getvalue()


def run_expert(source=None, args=None):
    """Run expert_dynasty.py offline. The stub answers a GET with the default board and
    a POST with the POINT board, which is what the site does: the query string is
    ignored, so only a real postback changes the view. -> (stdout, [POST bodies]).
    """
    real, argv = urllib.request.urlopen, sys.argv
    pages = (EXP_GET.read_bytes(), EXP_POST.read_bytes())
    posts = []

    def stub(req, timeout=None):
        if req.data:
            posts.append(req.data.decode())
            return io.BytesIO(pages[1])
        return io.BytesIO(pages[0])

    urllib.request.urlopen = stub
    sys.argv = [str(EXPERT)] + (args or EXP_ARGS)
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            if source is None:
                runpy.run_path(str(EXPERT), run_name='__main__')
            else:
                exec(compile(source, str(EXPERT), 'exec'), {'__name__': '__main__'})
    finally:
        urllib.request.urlopen, sys.argv = real, argv
    return buf.getvalue(), posts


def mutate(find, replace, script=SCRIPT):
    src = script.read_text()
    out = src.replace(find, replace, 1)
    assert out != src, f'mutation no longer applies, pattern moved: {find}'
    return out


def test_parses_recorded_board():
    got = run_script(PAGE.read_bytes())
    want = SNAP.read_bytes().decode()
    assert got == want, '\n' + '\n'.join(difflib.unified_diff(
        want.splitlines(), got.splitlines(), 'recorded', 'now', lineterm=''))


def test_a_dropped_closing_td_parses_nothing():
    try:
        run_script(PAGE.read_bytes(), mutate(*DROP_CLOSING_TD))
    except AssertionError as e:
        assert 'NO ROWS PARSED' in str(e), e
    else:
        raise AssertionError('a dropped </td> still parsed the board — guard is dead')


def test_demanding_pos_and_age_loses_the_pick_bands():
    try:
        run_script(PAGE.read_bytes(), mutate(*TIGHTEN_BLANK_COLUMNS))
    except AssertionError as e:
        assert 'pick bands, want 8' in str(e), e
    else:
        raise AssertionError('tightened columns still found 8 bands — guard is dead')


def test_parses_recorded_expert_board():
    got, _ = run_expert()
    want = EXP_SNAP.read_bytes().decode()
    assert got == want, '\n' + '\n'.join(difflib.unified_diff(
        want.splitlines(), got.splitlines(), 'recorded', 'now', lineterm=''))


def test_a_query_string_instead_of_the_postback_is_caught():
    try:
        run_expert(mutate(*QUERY_STRING_NOT_POSTBACK, script=EXPERT))
    except AssertionError as e:
        assert 'CONTEXT MISMATCH' in str(e) and 'DDTYPE' in str(e), e
    else:
        raise AssertionError('a GET still passed the control echo — guard is dead')
    # What that assert is standing in front of: the default board, printed as if asked for.
    src = mutate(*QUERY_STRING_NOT_POSTBACK, script=EXPERT)
    out, _ = run_expert(src.replace('assert not bad', 'bad = bad and None'))
    assert 'DDTYPE=OVERALL' in out and 'the OVERALL board ONLY' in out, out


def test_reading_the_first_option_instead_of_the_selected_one_is_caught():
    # `sel` proves the board it got. Dropping `selected` reads every dropdown's first
    # option, so it echoes back a view nobody asked for and can never disagree.
    try:
        run_expert(mutate(*FIRST_OPTION_NOT_SELECTED, script=EXPERT))
    except AssertionError as e:
        assert 'CONTEXT MISMATCH' in str(e), e
    else:
        raise AssertionError('the first <option> still verified — guard is dead')


def test_dropping_card_from_the_card_class_finds_no_cards():
    try:
        run_expert(mutate('<div class="card dyn-card">', '<div class="dyn-card">',
                          script=EXPERT))
    except AssertionError as e:
        assert 'NO PLAYER CARDS' in str(e), e
    else:
        raise AssertionError('a wrong card class still split the board — guard is dead')


def test_the_first_control_named_drives_the_postback_and_the_rest_ride_along():
    # No assert in the recipe covers this, and the page cannot report it: an
    # __EVENTTARGET naming the wrong control returns a board that still echoes back
    # every value asked for.
    body = urllib.parse.parse_qs(run_expert(args=['DDTYPE=POINT', 'DDSTAT=800'])[1][0])
    ctl = 'ctl00$ContentPlaceHolder1$'
    assert body['__EVENTTARGET'] == [ctl + 'DDTYPE'], body['__EVENTTARGET']
    swapped = urllib.parse.parse_qs(run_expert(args=['DDSTAT=800', 'DDTYPE=POINT'])[1][0])
    assert swapped['__EVENTTARGET'] == [ctl + 'DDSTAT'], swapped['__EVENTTARGET']
    assert body[ctl + 'DDTYPE'] == ['POINT'] and body[ctl + 'DDSTAT'] == ['800'], body
    assert body[ctl + 'DDFORECAST'] == ['5'], body   # rides along at the page's own value
    assert body['__VIEWSTATE'][0], 'postback without __VIEWSTATE is rejected live'


def record():
    """Re-cut the fixture from the live board: verbatim <tr> slices, nothing hand-typed."""
    UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
          '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
    h = urllib.request.urlopen(urllib.request.Request(
        'https://hashtagbasketball.com/keeper', headers={'User-Agent': UA}),
        timeout=90).read().decode('utf-8', 'replace')
    grab = lambda p: re.search(p, h).group(0)
    trs = re.findall(r'<tr>[\s\S]*?</tr>', h)
    head = next(t for t in trs if '>PLAYER<' in t)
    body = [t for t in trs if 'mw200' in t]
    keep, seen = [], set()
    for t in body[:24] + [t for t in body if '<td>DRA</td>' in t]:
        if t not in seen:
            seen.add(t)
            keep.append(t)
    page = ('<html><head>' + grab(r'<title>[^<]*</title>') + '</head><body>'
            + grab(r'<span>Up-to-date[^<]*</span>')
            + grab(r'<span class="text-muted"><strong>Updated:</strong>[^<]*</span>')
            + '<table>' + head + ''.join(keep) + '</table></body></html>')
    FIX.mkdir(exist_ok=True)
    PAGE.write_bytes(page.encode())
    SNAP.write_bytes(run_script(page.encode()).encode())
    print(f'{len(keep)} rows -> {PAGE}\n{SNAP}')


CARD = '<div class="card dyn-card">'


def cut_expert(h, cards):
    """One expert response down to what the recipe reads, verbatim.

    Kept: title, the Updated stamp, all six <select> blocks with their real selected
    options, and `cards` verbatim card slices. __VIEWSTATE is 290KB of base64 the recipe
    only echoes back, so its VALUE is truncated -- the only edited byte in either fixture.
    """
    keep = [re.search(r'<title>[^<]*</title>', h).group(0),
            re.search(r'<strong>Updated:</strong>[^<]*', h).group(0)]
    for c in ['DDSTAT', 'DDTYPE', 'DDFORECAST', 'DDPOS', 'DDPOSFROM', 'DDTSUM']:
        keep.append(re.search(
            r'<select[^>]*id="ContentPlaceHolder1_' + c + r'"[^>]*>[\s\S]*?</select>',
            h).group(0))
    for n in ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION']:
        v = re.search(r'name="' + n + r'"[^>]*value="([^"]*)"', h).group(1)
        keep.append('<input type="hidden" name="%s" value="%s" />'
                    % (n, re.sub(r'&[^;]*$', '', v[:64])))
    parts = h.split(CARD)
    assert len(parts) > cards + 1, f'only {len(parts) - 1} cards on the page'
    return ('<html><head>' + keep[0] + '</head><body>' + ''.join(keep[1:])
            + CARD + CARD.join(parts[1:1 + cards]) + '</body></html>')


def record_expert(cards=8):
    """Re-cut both expert fixtures by TAPPING the real recipe's own two fetches, so the
    postback is never reimplemented here -- that is the edit the recipe forbids."""
    real, argv, seen = urllib.request.urlopen, sys.argv, []

    def tap(req, timeout=None):
        body = real(req, timeout=timeout).read()
        seen.append(body.decode('utf-8', 'replace'))
        return io.BytesIO(body)

    urllib.request.urlopen = tap
    sys.argv = [str(EXPERT)] + EXP_ARGS
    try:
        with redirect_stdout(io.StringIO()):
            runpy.run_path(str(EXPERT), run_name='__main__')
    finally:
        urllib.request.urlopen, sys.argv = real, argv
    assert len(seen) == 2, f'{len(seen)} fetches, expected GET then postback'
    FIX.mkdir(exist_ok=True)
    EXP_GET.write_bytes(cut_expert(seen[0], cards).encode())
    EXP_POST.write_bytes(cut_expert(seen[1], cards).encode())
    EXP_SNAP.write_bytes(run_expert()[0].encode())
    print(f'{cards} cards x2 -> {EXP_GET}\n{EXP_POST}\n{EXP_SNAP}')


if __name__ == '__main__':
    if '--record' in sys.argv[1:]:
        record()
        record_expert()
        sys.exit()
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print(f'ok  {t.__name__}')
    print(f'{len(tests)} passed')
