# Offline. python3 .claude/skills/auction-live/test_live.py
# Runs live.py as the CLI against the real 2026-09-24 Sheet export (fixtures/sheet-blank.csv),
# with cells overwritten the way the commissioner would type them.
import csv
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = pathlib.Path(__file__).parent
FIX = HERE / 'fixtures'
BLANK = list(csv.reader(open(FIX / 'sheet-blank.csv', encoding='utf-8')))
OPEN0 = {c: int(BLANK[45][c]) for c in range(1, 24, 2)}


def col(letters):
    return ord(letters) - ord('A')


def sheet(cells=None, ours=None):
    """Blank Sheet plus `cells` ({'Q48': 'name'}), with rows 44-46 recomputed like its formulas. `ours` = our open
    spots before any sale (default: the Sheet's)."""
    rows = [list(r) for r in BLANK]
    open0 = {**OPEN0, col('R'): ours} if ours else OPEN0
    for ref, v in (cells or {}).items():
        rows[int(ref[1:]) - 1][col(ref[0])] = v
    for c in range(1, 24, 2):
        prices = [int(float(rows[r][c].strip().lstrip('$'))) for r in range(47, 62)
                  if re.fullmatch(r'\$?\d+(\.0+)?', rows[r][c].strip())]  # Sheets COUNT: numbers incl. currency
        rows[43][c] = str(200 - sum(prices))
        rows[45][c] = str(open0[c] - len(prices))
        rows[44][c] = str(int(rows[43][c]) - int(rows[45][c]) + 1)
    return rows


def setup():
    """A temp `auction-2026` dir with the rookie board beside it, like `evals/`"""
    d = pathlib.Path(tempfile.mkdtemp()) / 'auction-2026'
    d.mkdir()
    for f in ('values.tsv', 'Auction 2026.md'):
        shutil.copy(FIX / f, d / f)
    shutil.copy(FIX / 'Rookie Draft 2026.md', d.parent / 'Rookie Draft 2026.md')
    return d


def run(d, rows, *args, cmd='once'):
    src = d / 'sheet.csv'
    with open(src, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    out = subprocess.run([sys.executable, str(HERE / 'live.py'), cmd, *args, '--src', str(src), '--dir', str(d)],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout


def tsv(path):
    return [r for r in csv.reader(open(path, encoding='utf-8'), delimiter='\t')][1:]


class Once(unittest.TestCase):
    def test_blank_sheet_reports_our_budget_and_writes_dashboard(self):
        d = setup()
        out = run(d, sheet())
        self.assertIn('us $200/4 max 197', out)
        self.assertIn('Baylor Scheierman', (d / 'dashboard.md').read_text())
        self.assertIn('Baylor Scheierman', (d / 'dashboard.html').read_text())

    def test_sale_is_logged_under_the_owner(self):
        d = setup()
        out = run(d, sheet({'U48': 'Harrison Barnes', 'V48': '14'}))
        self.assertEqual(tsv(d / 'sales.tsv'), [['Harrison Barnes', 'Chris', '14']])
        self.assertIn('SOLD Harrison Barnes → Chris $14', out)

    def test_sheet_spellings_resolve_to_values_names(self):
        d = setup()
        out = run(d, sheet({'U48': 'Nae’Qwan Tomlin', 'V48': '5', 'U49': 'jonas valanciunas ', 'V49': '$3',
                            'U50': 'B. Williams', 'V50': '$40.00', 'U51': 'Nobody McFake', 'V51': '1'}))
        self.assertEqual([r[0] for r in tsv(d / 'sales.tsv')],
                         ["Nae'Qwan Tomlin", 'Jonas Valančiūnas', 'Brandon Williams', 'Nobody McFake'])
        self.assertIn('SOLD ?Nobody McFake → Chris $1', out)
        self.assertIn('Brandon Williams\tChris\t40', (d / 'sales.tsv').read_text())

    def test_a_close_misspelling_or_a_team_tag_still_resolves(self):
        d = setup()
        run(d, sheet({'U48': 'Baylor Schierman', 'V48': '80', 'U49': 'Barlow (PHI)', 'V49': '70', 'U50': 'Jaxon Hays',
                      'V50': '5'}))
        self.assertEqual([r[0] for r in tsv(d / 'sales.tsv')], ['Baylor Scheierman', 'Dominick Barlow', 'Jaxson Hayes'])

    def test_a_one_word_misspelling_resolves_to_the_one_close_surname(self):
        d = setup()
        run(d, sheet({'U48': 'Shierman', 'V48': '80', 'U49': 'Smyth', 'V49': '5'}))
        self.assertEqual([r[0] for r in tsv(d / 'sales.tsv')], ['Baylor Scheierman', 'Smyth'])  # Smith: 2+ rows

    def test_alias_maps_a_sheet_typo_that_never_gets_fixed(self):
        d = setup()
        rows = sheet({'E48': 'Hayes Jaxson', 'F48': '70', 'E4': 'Flemings Kingston'})
        self.assertIn('SOLD ?Hayes Jaxson → Mitch $70', run(d, rows))

        (d / 'aliases.tsv').write_text('sheet\tname\nHayes Jaxson\tJaxson Hayes\nFlemings Kingston\tKingston Flemings\n')
        out = run(d, rows)
        self.assertIn('SOLD Jaxson Hayes → Mitch $70', out)
        self.assertIn('DRAFTED Kingston Flemings → Mitch 1.3', out)
        self.assertEqual(run(d, rows, 'jaxson hayes', cmd='q'), 'Jaxson Hayes · sold Mitch $70\n')

    def test_an_unresolved_sale_warns_on_every_status_and_the_dashboard_until_aliased(self):
        d = setup()
        run(d, sheet({'U48': 'Nobody McFake', 'V48': '1'}))
        rows = sheet({'U48': 'Nobody McFake', 'V48': '1', 'A48': 'Luka Garza', 'B48': '9'})
        self.assertRegex(run(d, rows), r'(?m)^room .* · WARN \?Nobody McFake$')
        self.assertIn('WARN ?Nobody McFake', (d / 'dashboard.md').read_text())
        self.assertIn('WARN ?Nobody McFake', (d / 'dashboard.html').read_text())

        (d / 'aliases.tsv').write_text('sheet\tname\nNobody McFake\tHarrison Barnes\n')
        self.assertNotIn('WARN', run(d, rows))
        self.assertNotIn('WARN', (d / 'dashboard.md').read_text())
        self.assertNotIn('WARN', (d / 'dashboard.html').read_text())

    def test_a_player_sold_to_two_teams_warns_on_the_status_and_the_dashboard(self):
        d = setup()
        out = run(d, sheet({**sale('Q', 48, 'Dru Smith', 45), **sale('A', 48, 'Dru Smtih', 30)}))
        self.assertRegex(out, r'(?m)^room .* · WARN dup Dru Smith$')
        self.assertIn('WARN dup Dru Smith', (d / 'dashboard.md').read_text())
        self.assertIn('WARN dup Dru Smith', (d / 'dashboard.html').read_text())

    def test_rookie_picks_are_logged_under_the_pick_owner(self):
        d = setup()
        out = run(d, sheet({'A4': 'Darryn Peterson', 'Q4': 'AJ Dybantsa', 'C3': '1.2 Mikel Brown Jr',
                            'E4': 'Not A Rookie'}))
        self.assertEqual(tsv(d / 'drafted.tsv'), [['Darryn Peterson', 'Todd', '1.1'], ['Mikel Brown', 'Jon', '1.2'],
                                                  ['Not A Rookie', 'Mitch', '1.3'], ['AJ Dybantsa', 'Mitch', '1.9']])
        self.assertIn('DRAFTED AJ Dybantsa → Mitch 1.9', out)
        self.assertIn('DRAFTED ?Not A Rookie → Mitch 1.3', out)

    def test_text_price_breaking_a_budget_formula_does_not_stop_the_sync(self):
        d = setup()
        rows = sheet({'U48': 'Harrison Barnes', 'V48': '14', 'U49': 'Luka Garza', 'V49': '12 ish',
                      'A48': 'Javonte Green', 'B48': '9'})
        rows[43][21] = rows[44][21] = '#VALUE!'  # Chris: Sheets can't sum a text price
        out = run(d, rows)
        self.assertEqual(tsv(d / 'sales.tsv'), [['Javonte Green', 'Todd', '9'], ['Harrison Barnes', 'Chris', '14'],
                                                ['Luka Garza', 'Chris', '12']])
        self.assertIn('- Chris 168 · $174 · 7', (d / 'dashboard.md').read_text())  # the Sheet counted 8 spots
        self.assertIn('Baylor Scheierman · bid to', run(d, rows, 'scheierman', cmd='q'))

    def test_a_text_price_on_our_buy_still_takes_one_of_our_spots(self):
        d = setup()
        rows = after_rookie_draft(sale('Q', 48, 'Dru Smith', '45?'), ours=3)
        rows[43][col('R')] = rows[44][col('R')] = '#VALUE!'  # Sheets can't sum a text price, and COUNT skips it
        self.assertIn('us $155/2 max 154', run(d, rows))

    def test_a_price_with_text_or_cents_still_sells_the_row_and_warns(self):
        d = setup()
        out = run(d, sheet({'E48': 'Baylor Scheierman', 'F48': '85?', 'C48': 'Dru Smith', 'D48': '60.5'}))
        self.assertIn('SOLD Baylor Scheierman → Mitch $85', out)
        self.assertIn('SOLD Dru Smith → Jon $60', out)
        self.assertIn('WARN price "60.5" Dru Smith · "85?" Baylor Scheierman', out)  # Sheet order: Jon's column first
        self.assertIn('Baylor Scheierman · sold Mitch $85', run(d, sheet({'E48': 'Baylor Scheierman', 'F48': '85?'}),
                                                              'scheierman', cmd='q'))

    def test_a_price_with_no_leading_digit_sells_the_row_at_its_digits_and_warns(self):
        d = setup()
        out = run(d, sheet({'E48': 'Baylor Scheierman', 'F48': '?85'}))
        self.assertIn('SOLD Baylor Scheierman → Mitch $85', out)
        self.assertIn('WARN price "?85" Baylor Scheierman', out)

    def test_a_price_with_no_digits_warns_and_is_not_a_sale(self):
        d = setup()
        out = run(d, sheet({'C48': 'Ryan Nembhard', 'D48': 'sold', 'E48': 'Dru Smith', 'F48': '$'}))
        self.assertIn('WARN price "sold" Ryan Nembhard · "$" Dru Smith', out)
        self.assertIn('WARN price "sold" Ryan Nembhard', (d / 'dashboard.md').read_text())
        self.assertEqual(tsv(d / 'sales.tsv'), [])

    def test_pick_only_change_prints_just_the_pick(self):
        d = setup()
        run(d, sheet())
        self.assertEqual(run(d, sheet({'A4': 'Darryn Peterson'})), 'DRAFTED Darryn Peterson → Todd 1.1\n')

    def test_card_strikes_sold_rows(self):
        d = setup()
        run(d, sheet({'W48': 'Baylor Scheierman', 'X48': '80'}))
        self.assertIn('~~Baylor Scheierman~~ Bonin $80', (d / 'dashboard.md').read_text())

    def test_last_spot_cap_is_hard_max_and_endgame_fires(self):
        d = setup()
        cells = {'Q48': 'Brandon Williams', 'R48': '50', 'Q49': 'Marvin Bagley', 'R49': '50',
                 'Q50': 'Dominick Barlow', 'R50': '50'}
        for i, c in enumerate('ACEGIKMOSUW'):
            cells[f'{c}48'], cells[f'{chr(ord(c) + 1)}48'] = f'Filler {i}', '160'
        out = run(d, sheet(cells))
        self.assertIn('us $50/1 max 50', out)
        self.assertIn('nom Baylor Scheierman (ENDGAME)', out)

    def test_full_roster_reads_max_0(self):
        d = setup()
        cells = {**sale('Q', 48, 'Goga Bitadze', 43), **sale('Q', 49, 'Marvin Bagley', 43),
                 **sale('Q', 50, 'Dominick Barlow', 43), **sale('Q', 51, 'Quinten Post', 43)}
        self.assertIn('us $28/0 max 0', run(d, after_rookie_draft(cells)))
        self.assertIn('**Us** $28 · 0 spots · max bid 0', (d / 'dashboard.md').read_text())

    def test_status_names_the_best_card_row_left_and_its_cap(self):
        d = setup()
        self.assertIn('· best Baylor Scheierman cap 154 ·', run(d, after_rookie_draft()))
        out = run(d, after_rookie_draft({'E48': 'Baylor Scheierman', 'F48': '90'}))
        self.assertRegex(out, r'· best Ryan Nembhard cap \d+ ·')

    def test_no_endgame_while_rivals_can_outbid_our_cap(self):
        d = setup()
        out = run(d, after_rookie_draft({'E48': 'Dominick Barlow', 'F48': '88'}))  # Mitch was the only $197 rival
        self.assertIn('us $200/4 max 197', out)
        self.assertNotIn('ENDGAME', out)


def card_cells(d):
    """{player: {column: cell}} for the priced rows of the dashboard's card table."""
    text = (d / 'dashboard.md').read_text()
    lines = text[text.index('## Card'):].split('\n\n##')[0].splitlines()
    head = next([c.strip() for c in x.strip('|').split('|')] for x in lines if x.startswith('| Player'))
    rows = [dict(zip(head, [c.strip() for c in x.strip('|').split('|')])) for x in lines if x.startswith('| ')]
    return {r['Player']: r for r in rows if r['Mkt'].isdigit()}


def card(d):
    """{player: (Mkt, Cap)} from the dashboard's card table, in its order."""
    return {n: (int(r['Mkt']), int(r['Cap'])) for n, r in card_cells(d).items()}


def card_after_draft():
    d = setup()
    run(d, after_rookie_draft())
    return card(d)


def top_rookies():
    """2026-class names, best BASE first."""
    rows = csv.DictReader(open(FIX / 'values.tsv', encoding='utf-8'), delimiter='\t')
    return [r['name'] for r in sorted((r for r in rows if "'26 class" in r['flag']), key=lambda r: -float(r['BASE']))]


def after_rookie_draft(cells=None, picks=None, ours=None):
    """`cells` on a Sheet whose picks, in order, went to `picks` (default: the top 36 2026-class rows by BASE)."""
    refs = [f'{c}{r}' for r in (4, 6, 8) for c in 'ACEGIKMOQSUW']
    return sheet({**dict(zip(refs, top_rookies()[:36] if picks is None else picks)), **(cells or {})}, ours)


def sale(c, r, name, price):
    """Cells for `name` sold at `price` in team column `c`, row `r`"""
    return {f'{c}{r}': name, f'{chr(ord(c) + 1)}{r}': str(price)}


def rivals_fill(n):
    """n $1 sales of made-up names across the rivals, none filling a team"""
    per_team = {'G': 8, 'I': 12, 'K': 7, 'M': 7, 'O': 8, 'S': 8}
    refs = [(c, r) for c, k in per_team.items() for r in range(48, 48 + k)]
    return {k: v for i, (c, r) in enumerate(refs[:n]) for k, v in sale(c, r, f'Filler {i}', 1).items()}


EARLY_LIST = ['Brandon Williams', 'Harrison Barnes', 'Marvin Bagley', 'Javonte Green', 'Luka Garza', 'Goga Bitadze',
              'Jaxson Hayes', 'Terance Mann', 'Pat Spencer', 'Quinten Post', 'Patrick Williams', 'Ryan Nembhard',
              'Al Horford', 'Jarred Vanderbilt', 'Caleb Love']


class Nominate(unittest.TestCase):
    def test_early_list_in_order_skipping_sold_names(self):
        d = setup()
        self.assertIn('nom Brandon Williams (early)', run(d, sheet()))
        self.assertIn('nom Harrison Barnes (early)', run(d, sheet({'U48': 'Brandon Williams', 'V48': '14'})))

    def test_used_up_early_list_falls_back_to_the_priciest_row_we_bid_0_on(self):
        d = setup()
        md = d / 'Auction 2026.md'
        md.write_text(re.sub(r'a \$1 body does: .*', 'a $1 body does: Javonte Green.', md.read_text()))
        out = run(d, after_rookie_draft(sale('I', 48, 'Javonte Green', 5)))
        nom = re.search(r'nom (.+) \(early\)', out).group(1)
        self.assertEqual(nom, next(n for n in top_unsold(d) if card(d).get(n, (0, 0))[1] == 0))
        self.assertIn(nom, card(d))  # a $0-cap target: stuck with us at $1, it costs what a $1 body does

    def test_never_opens_the_1_bid_on_a_pass_row_the_room_may_leave_with_us(self):
        d = setup()
        md = d / 'Auction 2026.md'
        md.write_text(md.read_text().replace('a $1 body does: Brandon Williams', 'a $1 body does: '
                                             'Ben Simmons, Brandon Williams'))
        self.assertIn('nom Brandon Williams (early)', run(d, sheet()))  # Simmons: live Market$ $3

        we_hold_3 = {'Q48': 'Goga Bitadze', 'R48': '50', 'Q49': 'Marvin Bagley', 'R49': '50',
                     'Q50': 'Dominick Barlow', 'R50': '50'}
        self.assertIn('nom Ryan Nembhard (mid)', run(d, after_rookie_draft(we_hold_3)))  # his 213 cuts Bagley's 174

    def test_never_nominates_an_unsigned_or_unprojected_row(self):
        d = setup()
        md = d / 'Auction 2026.md'
        md.write_text(md.read_text().replace('a $1 body does: Brandon Williams', 'a $1 body does: '
                                             'Jonas Valančiūnas, Guerschon Yabusele, Brandon Williams'))
        self.assertIn('nom Brandon Williams (early)', run(d, sheet()))

    def test_mid_list_once_half_the_league_spots_are_filled(self):
        d = setup()
        self.assertIn('(early)', run(d, after_rookie_draft(rivals_fill(45))))
        self.assertIn('nom Ryan Nembhard (mid)', run(d, after_rookie_draft(rivals_fill(46))))


def rival_sales(names, price):
    """`names` sold one each to Todd, Jon, Mitch, ... at `price` (a fixed $ or a function of the name)"""
    cells = {}
    for n, c in zip(names, 'ACEGIKMO'):
        cells.update(sale(c, 48, n, price(n) if callable(price) else price))
    return cells


def market(name):
    rows = csv.DictReader(open(FIX / 'values.tsv', encoding='utf-8'), delimiter='\t')
    return next(round(float(r['Market$'])) for r in rows if r['name'] == name)


class Room(unittest.TestCase):
    def test_cold_when_rivals_pay_the_minimum(self):
        d = setup()
        self.assertRegex(run(d, after_rookie_draft(rival_sales(EARLY_LIST[:8], 1))), r'(?m)^room 0\.00× cold \(8\)')

    def test_hot_when_rivals_pay_double_market(self):
        d = setup()
        self.assertRegex(run(d, after_rookie_draft(rival_sales(EARLY_LIST[:8], lambda n: 2 * market(n)))),
                         r'(?m)^room [12]\.\d\d× hot \(8\)')

    def test_forced_fill_at_the_end_does_not_count(self):
        d = setup()
        cells = {}
        for c in 'ACEGIKMOSUW':  # every rival down to 1 open spot
            for r in range(48, 47 + OPEN0[col(c) + 1]):
                cells.update(sale(c, r, f'Filler {c}{r}', 1))
        run(d, after_rookie_draft(cells))
        for c, n in zip('ACEGIKMO', EARLY_LIST):
            cells.update(sale(c, 47 + OPEN0[col(c) + 1], n, 1))
        self.assertRegex(run(d, after_rookie_draft(cells)), r'(?m)^room \? 0/5')

    def test_waits_for_5_rival_sales_and_leaves_ours_out(self):
        d = setup()
        ours = {'Q48': 'Luka Garza', 'R48': '1', 'Q49': 'Al Horford', 'R49': '1'}
        self.assertRegex(run(d, after_rookie_draft({**rival_sales(EARLY_LIST[:4], 1), **ours})), r'(?m)^room \? 4/5')


class RookieDraft(unittest.TestCase):
    def test_2_9_is_hlinas_though_the_sheet_still_labels_it_ours(self):
        d = setup()
        run(d, after_rookie_draft(picks=top_rookies()[:19]))
        out = run(d, after_rookie_draft(picks=top_rookies()[:20]))
        self.assertNotIn('OUR PICK', out)
        out = run(d, after_rookie_draft(picks=top_rookies()[:21]))
        self.assertIn(f'DRAFTED {top_rookies()[20]} → Hlina 2.9', out)

    def test_query_on_a_rookie_during_the_draft_reads_the_board(self):
        d = setup()
        out = run(d, after_rookie_draft(picks=top_rookies()[:20]), 'stirtz', cmd='q')
        self.assertEqual(out, 'Bennett Stirtz · rookie · BASE 546 · Hashtag 404/269 · '
                              'split: Dizzle 139, expert 404; behind OKC depth\n')

    def test_last_pick_prints_draft_done_and_the_auction_status(self):
        d = setup()
        run(d, after_rookie_draft(picks=top_rookies()[:35]))
        out = run(d, after_rookie_draft()).splitlines()
        self.assertEqual(out[:2], ['DRAFTED Emanuel Sharp → Bonin 3.12', 'DRAFT DONE'])
        self.assertTrue(out[2].startswith('room '))

    def test_first_sale_ends_the_draft_though_a_pick_was_passed(self):
        d = setup()
        passed_on = [n for n in top_rookies()[:36] if n != 'Sergio De Larrea']  # 35 picks, 3.12 left empty
        run(d, after_rookie_draft(picks=passed_on))
        out = run(d, after_rookie_draft(sale('A', 48, 'Luka Garza', 9), picks=passed_on))
        self.assertIn('DRAFT DONE', out)
        self.assertRegex(run(d, after_rookie_draft(sale('A', 48, 'Luka Garza', 9), picks=passed_on), 'de larrea',
                             cmd='q'), r'^Sergio De Larrea · bid to \d+ · ')

class SpendRules(unittest.TestCase):
    def test_card_is_every_row_that_beats_a_1_body_by_score(self):
        d = setup()
        run(d, after_rookie_draft())
        self.assertEqual(list(card(d))[:12], ['Baylor Scheierman', 'Ryan Nembhard', 'Dru Smith', 'Goga Bitadze',
                                              'Dominick Barlow', 'Marvin Bagley', 'Meleek Thomas', 'Brandon Williams',
                                              'Quinten Post', 'Chris Cenac', 'Vít Krejčí', 'Julian Strawther'])
        self.assertEqual(len(card(d)), 29)  # 45 rows score > 0, less the 11 the draft took and the 5 unsigned

    def test_score_alone_makes_a_target_even_when_the_row_hurts_this_season(self):
        d = setup()
        rookies_fall = [n for n in top_rookies()[:40] if n not in ('Sergio De Larrea', 'Meleek Thomas', 'Chris Cenac')]
        run(d, after_rookie_draft(picks=rookies_fall))
        c = card(d)
        for n in ('Sergio De Larrea', 'Meleek Thomas', 'Chris Cenac', 'Ryan Nembhard',
                  'Brandon Williams'):  # ΔP −0.09 to −0.33, Score 147 to 291
            self.assertIn(n, c)
        self.assertNotIn('Javonte Green', c)

    def test_an_unsigned_or_unprojected_row_is_never_a_target(self):
        d = setup()
        run(d, after_rookie_draft(picks=[n for n in top_rookies()[:37] if n != 'Bruce Thornton']))
        c = card(d)
        self.assertIn('Chris Cenac', c)
        for n in ('Bruce Thornton', 'Cameron Payne', 'Killian Hayes', 'Guerschon Yabusele'):  # noproj, fa: Score 272 to 5
            self.assertNotIn(n, c)

    def test_before_the_draft_caps_price_the_top_36_rookies_as_gone(self):
        before, after = setup(), setup()
        run(before, sheet())
        run(after, after_rookie_draft())
        self.assertEqual(card(before), card(after))

    def test_mid_draft_a_reach_pick_replaces_the_last_assumed_rookie(self):
        reach = top_rookies()[:17] + ['Jaron Pierre']
        mid, after = setup(), setup()
        run(mid, after_rookie_draft(picks=reach))
        run(after, after_rookie_draft(picks=top_rookies()[:35] + ['Jaron Pierre']))
        self.assertEqual(card(mid), card(after))

    def test_cap_is_the_most_we_can_pay_and_still_match_the_best_score_the_rest_of_the_pool_buys(self):
        d = setup()
        run(d, after_rookie_draft())
        self.assertEqual({n: c for n, (_, c) in card(d).items() if c}, {
            'Baylor Scheierman': 154, 'Ryan Nembhard': 77, 'Dru Smith': 73})
        # Bitadze 191, Barlow 181, Bagley 174: $0, a 4th buy under Drummond's 278 is the one we cut

    def test_at_3_open_spots_the_cuts_keep_drummond_without_a_1_body(self):
        d = setup()
        self.assertIn('us $200/3 max 198', run(d, after_rookie_draft(ours=3)))
        # 2 cuts, Chaney and Matković: the plan is 3 rows, and a $1 spot would keep only Matković's 134
        self.assertEqual({n: c for n, (_, c) in card(d).items() if c}, {
            'Baylor Scheierman': 155, 'Ryan Nembhard': 78, 'Dru Smith': 73})

    def test_each_buy_re_plans_the_spots_left(self):
        d = setup()
        run(d, after_rookie_draft({'Q48': 'Baylor Scheierman', 'R48': '80'}))
        # $120 over 3 spots: the plan is Nembhard, Dru and a $1 body, so the cuts keep Drummond's 278
        self.assertEqual({n: c for n, (_, c) in card(d).items() if c}, {'Ryan Nembhard': 67, 'Dru Smith': 63})

        run(d, after_rookie_draft({'Q48': 'Baylor Scheierman', 'R48': '80', 'Q49': 'Dru Smith', 'R49': '65'}))
        # $55 over 2 spots: Meleek Thomas (165) at his $23 Market$ is the fallback, so each row over him gets hard max
        self.assertEqual({n: c for n, (_, c) in card(d).items() if c}, dict.fromkeys(
            ['Ryan Nembhard', 'Goga Bitadze', 'Dominick Barlow', 'Marvin Bagley', 'Meleek Thomas'], 54))

    def test_last_spot_puts_hard_max_on_every_row_that_cuts_our_lowest_keeper_and_beats_the_best_one_left_at_market(
            self):
        d = setup()
        we_hold_3 = {'Q48': 'Brandon Williams', 'R48': '50', 'Q49': 'Marvin Bagley', 'R49': '50',
                     'Q50': 'Dominick Barlow', 'R50': '50'}
        run(d, after_rookie_draft(we_hold_3))
        c = card(d)
        self.assertLessEqual(c['Vít Krejčí'][0], 50)  # Krejčí: $50 buys him at market, but his 118 is cut
        # Meleek Thomas (165) is the best row $50 buys at market, and he cuts Brandon Williams (164)
        self.assertEqual({n: cap for n, (_, cap) in c.items() if cap}, dict.fromkeys(
            ['Baylor Scheierman', 'Ryan Nembhard', 'Dru Smith', 'Goga Bitadze', 'Meleek Thomas'], 50))

    def test_a_row_under_matkovic_gets_no_bid_while_a_2nd_1_body_keeps_him(self):
        d = setup()
        rows = after_rookie_draft({**sale('Q', 48, 'Baylor Scheierman', 90), **sale('Q', 49, 'Dru Smith', 55),
                                   **rival_sales(['Ryan Nembhard', 'Goga Bitadze', 'Dominick Barlow', 'Marvin Bagley',
                                                  'Brandon Williams', 'Meleek Thomas', 'Chris Cenac', 'Quinten Post'], 60)})
        self.assertIn('us $55/2 max 54', run(d, rows))
        self.assertRegex(run(d, rows, 'krejci', cmd='q'), r'^Vít Krejčí · pass · ')  # 118: cut before Matković's 134

    def test_last_spot_bids_on_a_row_that_pushes_a_held_buy_into_the_cuts(self):
        d = setup()
        rows = after_rookie_draft({**sale('Q', 48, 'Baylor Scheierman', 138), **sale('Q', 49, 'Dominick Barlow', 1),
                                   **sale('Q', 50, 'Vít Krejčí', 1)})
        self.assertIn('us $60/1 max 60', run(d, rows))
        self.assertRegex(run(d, rows, 'nembhard', cmd='q'), r'^Ryan Nembhard · bid to 60 · ')  # 213 cuts Krejčí's 118

    def test_in_a_hot_room_a_row_the_room_prices_past_our_last_spot_holds_down_no_cap(self):
        d = setup()
        hot = rival_sales(EARLY_LIST[:8], lambda n: 2 * market(n))
        ours = {**sale('Q', 48, 'Quinten Post', 60), **sale('Q', 49, 'Chris Cenac', 40), **sale('Q', 50, 'Vít Krejčí', 40)}
        out = run(d, after_rookie_draft({**hot, **ours}))
        self.assertRegex(out, r'(?m)^room 2\.\d\d× hot \(8\) · us \$60/1 max 60 ')
        self.assertLessEqual(card(d)['Baylor Scheierman'][0], 60)  # at live Market$ we could buy him, at 2× we can't
        self.assertEqual({n: c for n, (_, c) in card(d).items() if c}, dict.fromkeys(
            ['Baylor Scheierman', 'Ryan Nembhard', 'Dru Smith', 'Dominick Barlow', 'Meleek Thomas'], 60))

    def test_values_without_scores_warns(self):
        d = setup()
        rows = [r for r in csv.reader(open(d / 'values.tsv', encoding='utf-8'), delimiter='\t')]
        at = rows[0].index('score')
        rows = [r[:at] + r[at + 1:] for r in rows]
        csv.writer(open(d / 'values.tsv', 'w', newline='', encoding='utf-8'), delimiter='\t').writerows(rows)
        self.assertIn('WARN no scored rows in values.tsv', run(d, sheet()))


class Watch(unittest.TestCase):
    def test_prints_only_on_change_and_once_per_outage(self):
        d = setup()
        src = d / 'sheet.csv'

        def put(rows=None, raw=None):
            tmp = d / 'next.csv'
            if raw is None:
                with open(tmp, 'w', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerows(rows)
            else:
                tmp.write_text(raw)
            tmp.replace(src)

        put(sheet())
        p = subprocess.Popen([sys.executable, '-u', str(HERE / 'live.py'), 'watch', '--every', '0.05',
                              '--src', str(src), '--dir', str(d)], stdout=subprocess.PIPE, text=True)
        try:
            self.assertTrue(p.stdout.readline().startswith('room '))
            put(sheet({'U48': 'Brandon Williams'}))  # name typed, price not yet: nothing to say
            time.sleep(0.3)
            put(sheet({'U48': 'Brandon Williams', 'V48': '14'}))
            self.assertEqual(p.stdout.readline(), 'DRAFT DONE\n')  # the first sale ends the draft
            self.assertTrue(p.stdout.readline().startswith('SOLD Brandon Williams → Chris $14'))
            self.assertIn('nom Harrison Barnes (early)', p.stdout.readline())
            put(raw='<html>Sorry, unable to open the file</html>')
            self.assertTrue(p.stdout.readline().startswith('ERR '))
            put(sheet({'U48': 'Brandon Williams', 'V48': '14', 'A4': 'Darryn Peterson'}))
            self.assertEqual(p.stdout.readline(), 'DRAFTED Darryn Peterson → Todd 1.1\n')
        finally:
            p.kill()

    def test_every_read_leaves_a_heartbeat_naming_the_page_version(self):
        d = setup()
        src = d / 'sheet.csv'
        with open(src, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(sheet())
        p = subprocess.Popen([sys.executable, '-u', str(HERE / 'live.py'), 'watch', '--every', '0.05',
                              '--src', str(src), '--dir', str(d)], stdout=subprocess.PIPE, text=True)
        try:
            p.stdout.readline()
            time.sleep(0.3)
            beat = re.fullmatch(r'window\.BEAT = \{t: ([\d.]+), v: ([\d.]+)\};\n', (d / 'beat.js').read_text())
            self.assertAlmostEqual(float(beat.group(1)), time.time(), delta=1)
            self.assertAlmostEqual(float(beat.group(2)), (d / 'dashboard.html').stat().st_mtime, delta=0.01)
        finally:
            p.kill()


def top_unsold(d):
    text = (d / 'dashboard.md').read_text()
    return [line.split('|')[1].strip() for line in text[text.index('## Top unsold'):].splitlines()
            if line.startswith('| ') and not line.startswith('| Player')]


class Dashboard(unittest.TestCase):
    def test_card_sets_score_and_live_gap_beside_market(self):
        d = setup()
        run(d, after_rookie_draft())
        c = card_cells(d)
        self.assertEqual(c['Baylor Scheierman']['Score'], '296')
        self.assertGreater(int(c['Baylor Scheierman']['Gap']), 0)
        self.assertLess(int(c['Jaxson Hayes']['Gap']), 0)  # Score$ 28 against Market$ 58

    def test_top_unsold_leaves_out_rookies_the_draft_will_take(self):
        d = setup()
        run(d, sheet())
        self.assertNotIn('Cameron Boozer', top_unsold(d))
        self.assertEqual(len(top_unsold(d)), 25)

        run(d, after_rookie_draft(picks=top_rookies()[1:37]))
        self.assertEqual(top_unsold(d)[0], 'Cameron Boozer')

    def test_last_sales_newest_first(self):
        d = setup()
        run(d, sheet({'A48': 'Luka Garza', 'B48': '9'}))
        run(d, sheet({'A48': 'Luka Garza', 'B48': '9', 'W48': 'Harrison Barnes'}))
        run(d, sheet({'A48': 'Luka Garza', 'B48': '9', 'W48': 'Harrison Barnes', 'X48': '12'}))
        text = (d / 'dashboard.md').read_text()
        self.assertIn('Harrison Barnes → Bonin $12\n- Luka Garza → Todd $9', text)


class Query(unittest.TestCase):
    def test_card_row_gets_our_cap_and_other_rows_get_pass(self):
        d = setup()
        rows = sheet({'U48': 'Harrison Barnes', 'V48': '14'})
        self.assertRegex(run(d, rows, 'scheierman', cmd='q'), r'^Baylor Scheierman · bid to \d+ · mkt \d+ · rivals Mitch 197')
        self.assertRegex(run(d, rows, 'scheierman', cmd='q'), r' · score 296 gap \+\d+ · ')
        self.assertRegex(run(d, rows, 'javonte green', cmd='q'), r'^Javonte Green · pass · mkt \d+')
        self.assertIn('ambiguous: Jaxson Hayes, Killian Hayes', run(d, rows, 'hayes', cmd='q'))
        self.assertEqual(run(d, rows, 'barnes', cmd='q'), 'Harrison Barnes · sold Chris $14\n')
        self.assertFalse((d / 'sales.tsv').exists())

    def test_a_price_gets_bid_or_stop(self):
        d = setup()
        rows = after_rookie_draft()
        self.assertRegex(run(d, rows, 'Baylor', 'Scheierman', '50', cmd='q'), r'^Baylor Scheierman · bid to 154 · ')
        self.assertRegex(run(d, rows, 'scheierman', '154', cmd='q'), r'^Baylor Scheierman · out at 154 \(cap 154\) · ')
        self.assertRegex(run(d, rows, 'looney', '3', cmd='q'), r'^Kevon Looney · pass · mkt ')


if __name__ == '__main__':
    unittest.main()
