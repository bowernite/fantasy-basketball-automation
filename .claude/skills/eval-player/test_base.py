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

EVALS = HERE.parents[2] / 'evals'
OURS = str(EVALS / 'lineup-math' / 'rosters' / 'roster-161025-2025-26.json')
PUBLISHED = [
    "teams/my-team/My Team.md",
    "teams/matthew/Matthew's Team.md",
    "teams/josh/Josh's Team.md",
    "teams/henry/Henry's Team.md",
    "teams/bonin/Bonin's Team.md",
    "teams/brian/Brian's Team.md",
    "teams/jon/Jon's Team.md",
    "teams/todd/Todd's Team.md",
    "teams/hlina/Matt Hlina's Team.md",
    "teams/hlina-todd-jon-boards.md",
]
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

    def test_prices_a_player_on_all_three_boards(self):
        # My Team.md: Cade Cunningham 6 | 6 | 5 -> BASE 8082
        self.assertEqual(run('Cade Cunningham')['Cade Cunningham'],
                         ['6', '6', '5', '8082'])

    def test_a_nickname_no_normalisation_can_reach_still_joins(self):
        # Every hand-checked line in ALIAS, because each one is a league spelling that
        # reaches nothing on any board on its own: Fleaflicker's Bub Carrington is
        # Carlton Carrington, its Ronald Holland is Ron, its Alex Sarr is Alexandre.
        # Nothing about either string connects them, and Sarr is a top-30 asset.
        got = run('Bub Carrington', 'Ronald Holland', 'Alex Sarr')
        self.assertEqual(got['Bub Carrington'][:3], ['292', '194', '244'])
        self.assertEqual(got['Ronald Holland'][:3], ['150', '209', '337'])
        self.assertEqual(got['Alex Sarr'][:3], ['48', '30', '25'])

    def test_board_spellings_a_naive_match_misses_still_join(self):
        # The two shapes that make a league name miss every board row: an accent the
        # boards drop, and a generational suffix the boards carry and Fleaflicker
        # doesn't. Both look exactly like an off-all-3-boards 0.
        got = run('Karlo Matković', 'Marvin Bagley', 'DaRon Holmes')
        self.assertEqual(got['Karlo Matković'][:3], ['338', '342', '448'])   # accent
        self.assertEqual(got['Marvin Bagley'][:3], ['317', '453', '637'])    # Bagley III
        self.assertEqual(got['DaRon Holmes'][:3], ['310', '333', '386'])     # Holmes Jr

    def test_a_name_the_boards_spell_differently_from_each_other_still_joins(self):
        # Jon's Team.md: Terrence Shannon 233 | 180 | 509 -> BASE 544. Dizzle writes him
        # Terrance and both hashtag boards Terrence, and no suffix or accent rule reaches
        # an a/e. Worse than an all-boards miss: he still joins two of three, so nothing
        # refuses. Crowd is printed, not blended, so dizzle's 40% stays in
        self.assertEqual(run('Terrence Shannon')['Terrence Shannon'],
                         ['233', '180', '509', '544'])

    def test_nic_claxton_reaches_hashtag_under_nicolas(self):
        # Todd's Team.md used to print 100 | – | –. Hashtag ranks Nicolas
        # Claxton 98 / 124; Dizzle writes Nic. Two-of-three miss, nothing refuses.
        self.assertEqual(run('Nic Claxton')['Nic Claxton'][:3],
                         ['100', '98', '124'])

    def test_ayo_dosunmu_reaches_dizzle_through_its_typo(self):
        # Dizzle Points writes Dosumnu; league + both Hashtag boards write Dosunmu.
        # 9cat tab spells it right, so a naive "he's off Dizzle" is a failed join.
        self.assertEqual(run('Ayo Dosunmu')['Ayo Dosunmu'][:3],
                         ['156', '151', '110'])

    def test_khaman_maluach_reaches_dizzle_through_its_typo(self):
        # Dizzle Points writes Malauch; league + both Hashtag boards write Maluach.
        # A naive "he's off Dizzle" is a failed join, not a real absence
        self.assertEqual(run('Khaman Maluach')['Khaman Maluach'][:3],
                         ['123', '154', '332'])

    def test_a_roster_file_supplies_every_name_in_it(self):
        # Silently dropping a name is the same failure as a missed join, one level up:
        # the roster is the input, so every entry has to come back out with a row.
        roster = json.loads(pathlib.Path(OURS).read_text(encoding='utf-8'))
        self.assertEqual(sorted(p for p, _ in roster_table(OURS)),
                         sorted(p['n'] for p in roster))

    def test_a_roster_supplies_each_players_team_so_a_duplicate_needs_no_flag(self):
        # A bare Jaylin Williams is refused on the command line; off a roster the file
        # already says which one, and both rows have to resolve to their own player.
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d, 'roster.json')
            f.write_text(json.dumps([{'n': 'Jaylin Williams', 'tm': 'OKC'},
                                     {'n': 'Jaylin Williams', 'tm': 'DEN'}]))
            got = run_raw('--roster', str(f))
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertEqual([c[:3] for _, c in table(got.stdout)],
                         [['318', '245', '688'], ['-', '711', '242']])

    def test_team_resolves_a_duplicate_name_on_every_board_including_the_one_row_boards(self):
        # Only OKC's Jaylin Williams is on Dizzle. Handing DEN's that row is the same
        # error as picking the wrong duplicate, so the DEN row reads off Dizzle.
        got = run('Jaylin Williams:OKC', 'Jaylin Williams:DEN')
        self.assertEqual(got['Jaylin Williams:OKC'][:3], ['318', '245', '688'])
        self.assertEqual(got['Jaylin Williams:DEN'][:3], ['-', '711', '242'])


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
        # My Team.md's one real BASE 0: genuinely off all three boards.
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

    def test_a_duplicate_the_team_cannot_split_is_refused_too(self):
        # Chaz Lanier is on the expert board twice, both DET, ranks 402 and 412 — the
        # board itself cannot tell them apart, so neither can a team argument.
        err = refusal(run_raw('Chaz Lanier:DET'))
        self.assertIn('AMBIGUOUS', err)
        self.assertIn('402', err)
        self.assertIn('412', err)

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
        # Points 35%, not blended with crowd, so two players tied on those two boards stay tied
        even = [(10, 'Even', 'BOS'), (10, 'CrowdOutlier', 'BOS')]
        crowd = [(10, 'Even', 'BOS'), (400, 'CrowdOutlier', 'BOS')]
        with snapshots(even, even, crowd):
            got = priced('Even', 'CrowdOutlier')
        self.assertEqual(got['Even'][:3], ['10', '10', '10'])
        self.assertEqual(got['CrowdOutlier'][:3], ['10', '10', '400'])
        self.assertEqual(got['Even'][3], got['CrowdOutlier'][3])

    def test_rank_1_is_9999_and_the_rank_at_the_square_root_of_D_is_worth_half_of_that(self):
        # The curve's two anchors (Eval Definitions §BASE): V is scaled to 9999 at the
        # top, and "rank a = sqrt(D) is worth half of rank 1". At D = 456 that half-value
        # rank is 21.35, so it falls between the 21st and 22nd player. Every figure in
        # evals/ is on this shape, and a re-scaled or re-shaped curve stays plausible
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

    def test_absence_from_crowd_does_not_enter_the_blend(self):
        # Will Richard is off crowd (depth 764, past D). Crowd is printed, not blended,
        # so BASE is Dizzle Points and Hashtag Points only
        self.assertEqual(run('Will Richard')['Will Richard'],
                         ['325', '376', '-', '145'])

    def test_a_rank_at_or_past_D_is_worth_nothing(self):
        # The curve is 0 from D on, so a player the boards do carry can still price at
        # 0 — Malik Beasley, 494 and 659 with Dizzle's weight renormalised away. The
        # printed ranks are the only thing separating this from a failed join.
        p = run_raw('Malik Beasley')
        D = int(re.search(r'D = 12 x \d+ = (\d+)', p.stdout).group(1))
        row = dict(table(p.stdout))['Malik Beasley']
        self.assertEqual(row[0], '-', row)
        for r in row[1:3]:
            self.assertGreaterEqual(int(r), D, row)  # else pick a deeper player
        self.assertEqual(row[3], '0', row)

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


def published_rows(path):
    """[(player, [dizP, htP, crd, BASE])] off an eval file's Players table.

    Boards is one cell (`6 • 6 (5)`); BASE is the next numeric cell.
    """
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        c = [x.strip().strip('*') for x in line.strip().strip('|').split('|')]
        if len(c) < 4:
            continue
        boards = next((cell for cell in c if '•' in cell), None)
        if boards is None:
            continue
        m = re.match(r'^\s*(.+?)\s•\s(.+?)\s\((.+?)\)\s*$', boards)
        if not m:
            continue
        parts = [p.strip() for p in m.groups()]
        idx = c.index(boards)
        if idx + 1 >= len(c):
            continue
        try:
            cells = []
            for x in (*parts, c[idx + 1]):
                x = x.replace('–', '-')
                cells.append('-' if x == '-' else str(int(x.replace(',', ''))))
        except ValueError:
            continue
        rows.append((re.sub(r'\s*(†|→.*)$', '', c[0]).strip().strip('*'), cells))
    return rows


class PublishedEvals(unittest.TestCase):
    """Every number in a shipped eval, re-derived. The reason the rest of this exists."""

    def test_reproduces_every_published_BASE_and_per_board_rank(self):
        for name in PUBLISHED:
            with self.subTest(name):
                want = dict(published_rows(EVALS / name))
                self.assertGreaterEqual(len(want), 15, f'{name}: table moved')
                self.assertEqual(self.rederive(name, want), want, '; '.join(
                    f'{p} published {want[p]}' for p in want))

    def rederive(self, doc, want):
        """`want`'s names back through the CLI, splitting any name it refuses as
        AMBIGUOUS into NAME:TEAM candidates — the doc publishes one row for a name two
        players share, so exactly one of them has to reproduce it."""
        # A row the file publishes as off all three boards IS the hand-check.
        args = [a for p, c in want.items() if c[:3] == ['-'] * 3
                for a in ('--absent', p)]
        pending, got = list(want), {}
        while True:
            p = run_raw(*pending, *args)
            if p.returncode == 0:
                return {**got, **dict(table(p.stdout))}
            err = refusal(p)
            who = re.search(r"AMBIGUOUS.*?'([^']+)'", err)
            self.assertIsNotNone(who, f'{doc}: {err}')
            who = who.group(1)
            pending.remove(who)
            cand = {}
            for t in dict.fromkeys(re.findall(r'\b([A-Z]{2,4}) #\d+', err)):
                q = run_raw(f'{who}:{t}')
                cand[t] = dict(table(q.stdout)).get(f'{who}:{t}', 'REFUSED')
            hits = [t for t, row in cand.items() if row == want[who]]
            self.assertEqual(len(hits), 1,
                             f'{doc}: {who} publishes {want[who]}; candidates {cand}')
            got[who] = want[who]


if __name__ == '__main__':
    unittest.main(verbosity=2)
