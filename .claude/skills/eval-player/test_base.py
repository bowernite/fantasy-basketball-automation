# Offline guard for base.py. No network.
#   python3 .claude/skills/eval-player/test_base.py
import contextlib
import csv
import io
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).parent
SCRIPT = HERE / 'base.py'
sys.path.insert(0, str(HERE))
import base                                                          # noqa: E402

EVALS = HERE.parents[2] / 'strategy'
OURS = str(EVALS / 'lineup-math' / 'rosters' / 'roster-161025-2025-26.json')
ANSI = re.compile(r'\x1b\[[0-9;]*m')


def run_raw(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def table(stdout):
    """base.py's printed table as [(player, [dizP, htP, crd, BASE])], ranks as str."""
    return [(c[0], c[1:]) for c in (l.split('\t') for l in stdout.splitlines())
            if len(c) == 5 and c[0] != 'PLAYER']


def run(*args):
    """base.py's stdout as {player: [dizP, htP, crd, BASE]}, ranks as str."""
    p = run_raw(*args)
    assert p.returncode == 0, p.stderr
    return dict(table(p.stdout))


def refusal(p):
    """The refusal message off a non-zero run, with the traceback's colour stripped."""
    assert p.returncode != 0, p.stdout
    return ANSI.sub('', p.stderr)


def roster_table(path):
    """A roster's rows, confirming whatever all-boards absences it happens to hold.

    The refusal itself has its own test; a roster is re-cut after every trade, so who
    is off all three boards this week is not something a test can pin.
    """
    absent = []
    for _ in range(10):
        p = run_raw('--roster', path, *absent)
        if p.returncode == 0:
            return table(p.stdout)
        err = refusal(p)
        assert 'OFF ALL 3 BOARDS' in err, err
        absent += [a for n in re.findall(r'^\s\s(\S.*?) \([^()]*\)$',
                                         err[err.index('OFF ALL 3 BOARDS'):], re.M)
                   for a in ('--absent', n)]
    raise AssertionError(p.stderr)


@contextlib.contextmanager
def snapshots(dizP, htP, crd, stamp='Updated 1/1/2026'):
    """Run base.py against three made-up boards of `(rank, player, team)` rows.

    The committed snapshots are the right input for join questions -- they hold the real
    spellings. They are the wrong input for the arithmetic in `Eval Definitions §BASE`:
    nobody is ranked 1st on all three, no board stops one rank short of D, and a refresh
    moves every number. These rows are the same CSVs from base.py's side, cut to put a
    player exactly where the rule changes.
    """
    with tempfile.TemporaryDirectory() as d:
        board = []
        for (name, weight, *_), rows in zip(base.BOARDS, (dizP, htP, crd)):
            p = pathlib.Path(d, f'{name}.csv')
            with p.open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['#', 'Player', 'Team', stamp])   # dizzle stamps its header
                w.writerows(rows)
            board.append((name, weight, str(p), '#', 'Player', 'Team'))
        real, base.BOARDS = base.BOARDS, board
        try:
            yield
        finally:
            base.BOARDS = real


def priced(*argv):
    """base.py's table off whatever boards are in force, as {player: [d, h, c, BASE]}."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        base.main(list(argv))
    return dict(table(buf.getvalue()))


class Joining(unittest.TestCase):
    """League spellings reaching board rows. A missed join prices a real player at ~0."""

    def test_league_spellings_join_every_board_they_are_on(self):
        # Against the committed snapshots, because they hold the real spellings. Ranks
        # move with every re-cut, so only the join is asserted: a '-' here is a real
        # player silently losing a blended board's weight
        cases = {
            'Cade Cunningham': 'plain name',
            # ALIAS: nothing about either string connects them
            'Bub Carrington': 'boards write Carlton',
            'Ronald Holland': 'boards write Ron',
            'Alex Sarr': 'boards write Alexandre',
            'Nic Claxton': 'hashtag writes Nicolas',
            'Terrence Shannon': "dizzle writes Terrance, so he'd join two of three",
            'Ayo Dosunmu': 'dizzle writes Dosumnu',
            'Khaman Maluach': 'dizzle writes Malauch',
            # normalisation
            'Karlo Matković': 'accent the boards drop',
            'Marvin Bagley': 'boards carry III',
            'DaRon Holmes': 'boards carry Jr',
        }
        got = run(*cases)
        for name, why in cases.items():
            with self.subTest(f'{name}: {why}'):
                self.assertNotIn('-', got[name][:2], got[name])

    def test_a_roster_file_supplies_every_name_in_it(self):
        # Silently dropping a name is the same failure as a missed join, one level up:
        # the roster is the input, so every entry has to come back out with a row.
        roster = json.loads(pathlib.Path(OURS).read_text(encoding='utf-8'))
        self.assertEqual(sorted(p for p, _ in roster_table(OURS)),
                         sorted(p['n'] for p in roster))

    def test_a_roster_supplies_each_players_team_so_a_duplicate_needs_no_flag(self):
        # A bare Jaylin Williams is refused on the command line; off a roster the file
        # already says which one, and both rows have to resolve to their own player.
        # Only OKC's is on Dizzle, so handing DEN's that row is the wrong-duplicate error
        dizzle = [(318, 'Jaylin Williams', 'OKC')]
        both = [(204, 'Jaylin Williams', 'OKC'), (711, 'Jaylin Williams', 'DEN')]
        with tempfile.TemporaryDirectory() as d, snapshots(dizzle, both, both):
            f = pathlib.Path(d, 'roster.json')
            f.write_text(json.dumps([{'n': 'Jaylin Williams', 'tm': 'OKC'},
                                     {'n': 'Jaylin Williams', 'tm': 'DEN'}]))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                base.main(['--roster', str(f)])
        self.assertEqual([c[:3] for _, c in table(buf.getvalue())],
                         [['318', '204', '204'], ['-', '711', '711']])

    def test_team_resolves_a_duplicate_name_on_every_board_including_the_one_row_boards(self):
        dizzle = [(318, 'Jaylin Williams', 'OKC')]
        both = [(204, 'Jaylin Williams', 'OKC'), (711, 'Jaylin Williams', 'DEN')]
        with snapshots(dizzle, both, both):
            got = priced('Jaylin Williams:OKC', 'Jaylin Williams:DEN')
        self.assertEqual(got['Jaylin Williams:OKC'][:3], ['318', '204', '204'])
        self.assertEqual(got['Jaylin Williams:DEN'][:3], ['-', '711', '711'])


class RookieSlotPrefix(unittest.TestCase):
    """Dizzle writes each drafted rookie as `R.SS / Name` (`2.07 / Baba Miller`)."""

    def test_a_rookie_row_carrying_its_draft_slot_joins_the_league_name(self):
        dizzle = [(277, '2.07 / Baba Miller', 'LAC'), (11, '1.01 / Cameron Boozer', 'MEM')]
        rest = [(300, 'Baba Miller', 'LAC'), (12, 'Cameron Boozer', 'MEM')]
        with snapshots(dizzle, rest, rest):
            got = priced('Baba Miller', 'Cameron Boozer')
        self.assertEqual(got['Baba Miller'][:3], ['277', '300', '300'])
        self.assertEqual(got['Cameron Boozer'][:3], ['11', '12', '12'])


class TeamMatching(unittest.TestCase):
    """Which of two same-named rows is this player's -- the only question a team answers
    (`eval-player`). The boards spell teams three ways (SAS/SA, PHX/PHO, GSW/GS) and
    dizzle carries mid-move rows, so the match cannot be equality; but a near-miss taken
    as a hit hands a player 400 places of someone else's rank, and a real spelling read
    as a miss deletes a board's weight from his blend."""

    def test_a_team_that_merely_shares_two_letters_is_not_his_row(self):
        # The pairs a prefix match cannot tell apart: the Kings against the Spurs, the
        # Suns against the 76ers, the Clippers against the Lakers. Each name is two
        # players 390 ranks apart, so a loose match is a 390-place error in whichever
        # direction it lands.
        rows = [(10, 'Kings Guy', 'SAC'), (400, 'Kings Guy', 'SA'),
                (10, 'Suns Guy', 'PHX'), (400, 'Suns Guy', 'PHI'),
                (10, 'Clips Guy', 'LAC'), (400, 'Clips Guy', 'LAL')]
        with snapshots(rows, rows, rows):
            got = priced('Kings Guy:SAC', 'Kings Guy:SA', 'Suns Guy:PHX', 'Suns Guy:PHI',
                         'Clips Guy:LAC', 'Clips Guy:LAL')
        self.assertEqual([r[:3] for r in got.values()],
                         [['10'] * 3, ['400'] * 3] * 3, got)

    def test_the_same_franchise_spelled_differently_is_still_his_row(self):
        # The five franchises the committed boards actually disagree about: hashtag
        # writes SA/PHO/GS/NO/NY where dizzle and the league file write the long form.
        # Reading one of those as a miss silently drops 35% of that player's blend.
        pairs = (('SA', 'SAS'), ('PHO', 'PHX'), ('GS', 'GSW'), ('NO', 'NOP'), ('NY', 'NYK'))
        rows = [r for i, (board, league) in enumerate(pairs, 1)
                for r in ((i, f'{league} Guy', board), (i + 100, f'{league} Guy', 'XXX'))]
        with snapshots(rows, rows, rows):
            got = priced(*(f'{league} Guy:{league}' for _, league in pairs))
        for i, (board, league) in enumerate(pairs, 1):
            with self.subTest(f'{league} vs {board}'):
                self.assertEqual(got[f'{league} Guy:{league}'][:3], [str(i)] * 3)

    def test_a_mid_move_row_belongs_to_both_ends_of_the_move(self):
        # Dizzle publishes ~90 rows as "ATL -> PHO" (and one as "IND -> CHI - MIL"),
        # which is one player at either end of the move depending on how fresh the league
        # file is. Matching the source only means his rank vanishes off that board the
        # week the league file catches up with him.
        rows = [(10, 'Moved', 'ATL -> PHO'), (400, 'Moved', 'BOS'),
                (10, 'Twice Moved', 'IND -> CHI - MIL'), (400, 'Twice Moved', 'BOS')]
        with snapshots(rows, rows, rows):
            got = priced('Moved:ATL', 'Moved:PHX', 'Twice Moved:MIL')
        self.assertEqual([r[:3] for r in got.values()], [['10'] * 3] * 3, got)

    def test_a_team_matching_none_of_his_rows_is_refused_not_priced_off_the_first_one(self):
        # The other end of strictness: a team that matches no row means he is off that
        # board, and off all three that is the refusal -- never row one, never a 0.
        rows = [(10, 'Twin', 'BOS'), (400, 'Twin', 'MIA')]
        with snapshots(rows, rows, rows), self.assertRaises(base.Refused) as e:
            priced('Twin:DEN')
        self.assertIn('OFF ALL 3 BOARDS', str(e.exception))


class DuplicateRows(unittest.TestCase):
    """One board listing the same name on the same team twice (Chaz Lanier, DET #393 and
    #416 on Hashtag expert) is one player listed twice, priced at his best rank."""

    def test_a_player_listed_twice_on_one_team_prices_at_his_best_rank(self):
        twice = [(393, 'Chaz Lanier', 'DET'), (416, 'Chaz Lanier', 'DET')]
        once = [(420, 'Chaz Lanier', 'DET')]
        with snapshots(once, twice, once):
            got = priced('Chaz Lanier', 'Chaz Lanier:DET')
        self.assertEqual(got['Chaz Lanier'][:3], ['420', '393', '420'])
        self.assertEqual(got['Chaz Lanier:DET'], got['Chaz Lanier'])

    def test_one_name_twice_with_no_nba_team_is_not_merged(self):
        # Free agents share the `FA` cell, so it says nothing about who either row is
        for label, team in (('free agents', 'FA'), ('blank team', '')):
            rows = [(10, 'Unsigned', team), (400, 'Unsigned', team)]
            with self.subTest(label), snapshots(rows, rows, rows), \
                    self.assertRaises(base.Refused) as e:
                priced('Unsigned')
            self.assertIn('AMBIGUOUS', str(e.exception))

    def test_one_name_on_two_teams_is_still_two_players(self):
        rows = [(10, 'Twin', 'BOS'), (400, 'Twin', 'MIA')]
        with snapshots(rows, rows, rows), self.assertRaises(base.Refused) as e:
            priced('Twin')
        self.assertIn('AMBIGUOUS', str(e.exception))


class Refusals(unittest.TestCase):
    """What base.py refuses to guess at. A wrong row here is invisible downstream."""

    def test_an_all_boards_absence_refuses_to_print_a_row(self):
        # The failure mode this file exists for: a missed join looks exactly like a
        # genuine 0, so 0 has to be asked for rather than returned.
        p = run_raw('Chaney Johnson')
        err = refusal(p)
        self.assertIn('Chaney Johnson', err)
        self.assertIn('OFF ALL 3 BOARDS', err)
        self.assertNotIn('\t0', p.stdout)

    def test_a_hand_checked_absence_is_confirmed_by_flag_and_then_prices_at_zero(self):
        # Chaney Johnson is genuinely off all three boards
        p = run_raw('--absent', 'Chaney Johnson', 'Chaney Johnson')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(dict(table(p.stdout))['Chaney Johnson'],
                         ['-', '-', '-', '0'])
        self.assertIn('hand-checked', p.stdout)

    def test_an_absent_flag_naming_nobody_being_priced_is_refused(self):
        # --absent is a hand-check on one player. Misspell it and it confirms nothing
        # while still printing the confirmation line -- and the player it was meant
        # for goes back to being an unexplained 0.
        p = run_raw('--absent', 'Chaney Johsnon', 'Cade Cunningham')
        err = refusal(p)
        self.assertIn('Chaney Johsnon', err)
        self.assertNotIn('hand-checked', p.stdout)

    def test_an_absent_flag_for_a_player_the_boards_do_carry_is_refused(self):
        # The other way a hand-check goes stale: the flag outlives the absence, the
        # boards pick the player up, and the header keeps announcing him as a
        # hand-checked BASE 0 while his row prints real ranks. Provenance that
        # contradicts the table it sits above is worse than none.
        p = run_raw('--absent', 'Cade Cunningham', 'Cade Cunningham')
        err = refusal(p)
        self.assertIn('Cade Cunningham', err)
        self.assertNotIn('hand-checked', p.stdout)

    def test_a_bare_duplicate_name_refuses_to_pick_a_row(self):
        # Two active Jaylin Williams (DEN 26yo, OKC 24yo) — 435 ranks apart on the
        # crowd board, so guessing either one is a silent 400-place error.
        err = refusal(run_raw('Jaylin Williams'))
        self.assertIn('AMBIGUOUS', err)
        self.assertIn('DEN', err)
        self.assertIn('OKC', err)

    def test_every_refusal_is_a_readable_message_that_survives_python_O(self):
        # Two ways a guard stops being a guard. `assert` is what -O strips, and these
        # guards are the entire reason the file exists -- they cannot be an
        # optimisation. And a traceback buries the one line that says what to do
        # under a stack it cannot act on.
        for label, args in (('ambiguous name', ['Jaylin Williams']),
                            ('off all 3 boards', ['Chaney Johnson']),
                            ('bad roster file', ['--roster', str(HERE / 'nope.json')]),
                            ('unreadable roster size', ['--roster-size', 'twenty-eight']),
                            # A flag whose value the shell ate is a mistyped run like any
                            # other, and it lands on the same three guards.
                            ('--absent last', ['Cade Cunningham', '--absent']),
                            ('--roster last', ['--roster']),
                            ('--roster-size last', ['--roster-size'])):
            for flags in ([], ['-O']):
                with self.subTest(f'{label} {flags}'):
                    p = subprocess.run([sys.executable, *flags, str(SCRIPT), *args],
                                       capture_output=True, text=True)
                    self.assertNotEqual(p.returncode, 0, p.stdout)
                    self.assertNotIn('Traceback', p.stderr)
                    self.assertLessEqual(len(p.stderr.strip().splitlines()), 4, p.stderr)

    def test_a_roster_size_that_prices_the_whole_league_at_zero_is_refused(self):
        # D = teams x roster_size is the whole scale, so a size of 0 puts every rank at
        # or past D — a full table of confident 0s, exit 0, for players ranked 6th in
        # the world. Same silent 0 as a failed join, arriving through the flag instead.
        p = run_raw('--roster-size', '0', 'Cade Cunningham')
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertEqual(table(p.stdout), [])
        self.assertIn('--roster-size', refusal(p))

    def test_an_unusable_roster_file_fails_instead_of_printing_an_empty_table(self):
        # An empty roster is a whole team priced at nothing and no row to notice it by.
        with tempfile.TemporaryDirectory() as d:
            bad = pathlib.Path(d, 'not-json.json')
            bad.write_text('<html>rate limited</html>')
            for label, path in (('missing', str(pathlib.Path(d, 'nope.json'))),
                                ('not json', str(bad))):
                with self.subTest(label):
                    p = run_raw('--roster', path)
                    self.assertNotEqual(p.returncode, 0, p.stdout)
                    self.assertEqual(table(p.stdout), [])


class Blend(unittest.TestCase):
    """Ranks to BASE: the depth rule, the curve and the scale it is built on."""

    def test_crowd_rank_does_not_enter_the_blend(self):
        # Crowd is the third printed rank. BASE is Dizzle Points 40% and Hashtag
        # Points 35%, not blended with crowd, so players tied on those two boards stay
        # tied whatever crowd says, including nothing
        even = [(10, 'Even', 'BOS'), (10, 'CrowdOutlier', 'BOS'), (10, 'OffCrowd', 'BOS')]
        crowd = [(10, 'Even', 'BOS'), (400, 'CrowdOutlier', 'BOS'), (999, 'Deep', 'BOS')]
        with snapshots(even, even, crowd):
            got = priced('Even', 'CrowdOutlier', 'OffCrowd')
        self.assertEqual(got['Even'][:3], ['10', '10', '10'])
        self.assertEqual(got['CrowdOutlier'][:3], ['10', '10', '400'])
        self.assertEqual(got['OffCrowd'][:3], ['10', '10', '-'])
        self.assertEqual({r[3] for r in got.values()}, {got['Even'][3]})

    def test_rank_1_is_9999_and_the_rank_at_the_square_root_of_D_is_worth_half_of_that(self):
        # The curve's two anchors (Eval Definitions §BASE): V is scaled to 9999 at the
        # top, and "rank a = sqrt(D) is worth half of rank 1". At D = 456 that half-value
        # rank is 21.35, so it falls between the 21st and 22nd player. Every figure in
        # strategy/ is on this shape, and a re-scaled or re-shaped curve stays plausible
        # while turning every published comparison into a different number.
        rows = [(1, 'First', 'BOS'), (21, 'Above Root', 'BOS'), (22, 'Below Root', 'BOS')]
        with snapshots(rows, rows, rows):
            got = priced('First', 'Above Root', 'Below Root')
        self.assertEqual(got['First'][3], '9999')
        self.assertGreater(int(got['Above Root'][3]), 9999 / 2)
        self.assertLess(int(got['Below Root'][3]), 9999 / 2)

    def test_a_split_row_is_worth_the_blend_of_its_values_not_the_value_of_its_mean_rank(self):
        # Split's weighted mean rank is 0.40x1 + 0.35x300 = 140.65, which is
        # not where Flat sits; averaging ranks first would still collapse the
        # elite rank. Through the curve the elite rank is worth several times
        # the flat row, and §BASE's split-row warning only means anything if the two differ.
        top = [(1, 'Split', 'BOS'), (180, 'Flat', 'BOS')]
        rest = [(300, 'Split', 'BOS'), (180, 'Flat', 'BOS')]
        with snapshots(top, rest, rest):
            got = priced('Split', 'Flat')
        self.assertGreater(int(got['Split'][3]), 2 * int(got['Flat'][3]),
                           f'{got["Split"]} vs {got["Flat"]}')

    def test_a_board_one_rank_short_of_D_renormalises_where_one_reaching_D_scores_zero(self):
        # The depth rule's boundary is exactly depth < D, and the live boards sit
        # nowhere near it (450 and 764 against D = 456), so only a cut board pins it.
        # Same player both times: absent from the first board, 1st on the other two.
        elsewhere = [(1, 'Rated', 'BOS')]
        with snapshots([(455, 'Deepest', 'BOS')], elsewhere, elsewhere):
            short = priced('Rated')['Rated']
        with snapshots([(456, 'Deepest', 'BOS')], elsewhere, elsewhere):
            reaches = priced('Rated')['Rated']
        self.assertEqual(short, ['-', '1', '1', '9999'])    # weight gone, not zeroed
        self.assertEqual(reaches, ['-', '1', '1', '4666'])  # a real 0 at 40%: 0.35/0.75 x 9999

    def test_a_rank_at_or_past_D_is_worth_nothing(self):
        # The curve is 0 from D on, so a player the boards do carry can still price at
        # 0. The printed ranks are the only thing separating this from a failed join.
        short = [(450, 'Deepest', 'BOS')]
        deep = [(456, 'Carried', 'BOS'), (494, 'Past D', 'BOS')]
        with snapshots(short, deep, deep):
            got = priced('Carried', 'Past D')
        self.assertEqual(got['Carried'], ['-', '456', '456', '0'])
        self.assertEqual(got['Past D'], ['-', '494', '494', '0'])

    def test_a_better_rank_on_every_board_always_scores_higher(self):
        # BASE only means anything as an ordering. An inverted or clipped curve would
        # keep printing plausible numbers and turn every eval built on it upside down.
        ranked = {p: [int(x) for x in c] for p, c in roster_table(OURS) if '-' not in c}
        pairs = [(a, ra, b, rb) for a, ra in ranked.items() for b, rb in ranked.items()
                 if all(x < y for x, y in zip(ra[:3], rb[:3]))]
        self.assertGreater(len(pairs), 20, ranked)   # else the roster proves nothing
        for a, ra, b, rb in pairs:
            self.assertGreater(ra[3], rb[3], f'{a} {ra} vs {b} {rb}')

    def test_roster_size_is_an_argument_because_D_sets_the_whole_scale(self):
        # eval-team: roster_size is the size in effect for the season being valued, and
        # BASE compares only within one D. 38 is announced, 28 is current.
        p = run_raw('--roster-size', '28', 'Cade Cunningham')
        self.assertIn('D = 12 x 28 = 336', p.stdout)
        self.assertNotEqual(dict(table(p.stdout))['Cade Cunningham'][3],
                            run('Cade Cunningham')['Cade Cunningham'][3])


class Header(unittest.TestCase):
    """What the table has to say about itself to be readable months later."""

    def test_the_dizzle_month_is_discovered_never_hardcoded(self):
        # dizzle-dynasty re-snapshots under a new month and the old file stays put, so a
        # hardcoded month goes stale in place while every rank in the eval keeps resolving.
        with tempfile.TemporaryDirectory() as d:
            for m in ('july-2026', 'march-2026', 'january-2027'):
                pathlib.Path(d, f'{m}-dynasty-ranks-points.csv').touch()
            self.assertEqual(pathlib.Path(base.newest(d)).name,
                             'january-2027-dynasty-ranks-points.csv')

    def test_a_directory_with_no_month_stamped_snapshot_refuses_instead_of_falling_back(self):
        # The other half of never hardcoding the month: a renamed, deleted or
        # half-written refresh has to stop the run, because the fallbacks available --
        # an older file, no dizzle board at all -- both publish quietly.
        with tempfile.TemporaryDirectory() as d:
            pathlib.Path(d, 'dynasty-ranks-points.csv').touch()          # no month-year
            pathlib.Path(d, 'smarch-2026-dynasty-ranks-points.csv').touch()
            with self.assertRaises(base.Refused) as e:
                base.newest(d)
        self.assertIn('NO SNAPSHOT', str(e.exception))

    def test_a_snapshot_carrying_no_update_stamp_is_refused_not_headed_with_a_blank(self):
        # A board with no provenance could be any vintage, and the header is the only
        # thing a reader has to date these numbers by months later.
        rows = [(1, 'Someone', 'BOS')]
        with snapshots(rows, rows, rows, stamp=''), self.assertRaises(base.Refused) as e:
            priced('Someone')
        self.assertIn('NO UPDATED STAMP', str(e.exception))

    def test_the_header_states_each_boards_weight_stamp_depth_and_absence_rule(self):
        # eval-team -> Output: every board's update stamp AND depth, because the depth
        # is what decides whether an absence renormalises or scores 0. Crowd is printed,
        # not a blend weight
        h = run_raw('Cade Cunningham').stdout
        for w in ('40%', '35%'):
            self.assertIn(w, h)
        self.assertNotIn('25%', h)
        self.assertRegex(h, r'\bcrd\b.*printed')
        self.assertRegex(h, r'\bcrd\b.*not in the blend')
        D = int(re.search(r'D = 12 x \d+ = (\d+)', h).group(1))
        stamps = re.findall(r'UPDATED (\S[^\n]*?)\s+DEPTH (\d+)', h)
        self.assertEqual(len(stamps), 3, h)
        self.assertEqual(sum(int(d) < D for _, d in stamps), h.count('renormalises'), h)


if __name__ == '__main__':
    unittest.main(verbosity=2)
