# Offline. python3 .claude/skills/auction-live/test_page.py
import html
import pathlib
import re
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import page  # noqa: E402


def row(name, score='', market='10', dp='', base='100', ours='-0.05'):
    return {'name': name, 'score': score, 'Market$': market, 'dPtitle': dp, 'BASE': base, "Δw '26–'27 ours": ours}


def setup():
    values = [row('Baylor Scheierman', '375', '66', '1.35', '268', '0.01'),
              row('Jaxson Hayes', '205', '58', '1.28', '129', '-0.10'),
              row("D'Angelo Russell", '69', '24', '-0.33', '170', '-0.33'),
              row('Vít Krejčí', '159', '43', '0.62', '148', '-0.02'),
              row('Cameron Boozer', '', '197', '', '6655', '0.85')]
    s = SimpleNamespace(values=values, by_name={r['name']: r for r in values}, us=(120, 3, 118),
                        nominee='Brandon Williams (early)', warns=[], card=['Baylor Scheierman', 'Vít Krejčí'],
                        live={r['name']: round(float(r['Market$'])) for r in values},
                        sold={'Jaxson Hayes': ('Mitch', '70')}, drafted={'Cameron Boozer': ('Todd', '1.1')},
                        rivals=[('Mitch', (130, 3, 128)), ('Todd', (200, 6, 195))])
    s.not_in_pool = set(s.sold) | set(s.drafted)
    caps = {'Baylor Scheierman': 100, 'Vít Krejčí': 42}
    return s, [('Jaxson Hayes', 'Mitch', '70')], (lambda s, n: caps[n]), (lambda s, n: 12)


def table_rows(text):
    """{player: [cell texts]} from the big table's body."""
    body = text[text.index('<tbody'):text.index('</tbody>')]
    out = {}
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', body, re.S):
        cells = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
        if cells:  # section label rows carry only a <th>
            out[cells[0]] = cells
    return out


class Render(unittest.TestCase):
    def test_card_rows_carry_our_cap_and_the_rest_read_pass(self):
        s, log, cap, gap = setup()
        rows = table_rows(page.render(s, log, 'room ? 1/5', cap, gap))
        self.assertEqual(rows['Baylor Scheierman'][:6], ['Baylor Scheierman', '100', '66', '375', '+1.35', '+12'])
        self.assertEqual(rows["D'Angelo Russell"][1], 'pass')

    def test_card_rows_lead_by_score_then_the_rest_by_market(self):
        s, log, cap, gap = setup()
        rows = list(table_rows(page.render(s, log, 'room ? 1/5', cap, gap)))
        self.assertEqual(rows[:2], ['Baylor Scheierman', 'Vít Krejčí'])
        self.assertNotIn('Cameron Boozer', rows)

    def test_sold_row_is_struck_with_buyer_and_price(self):
        s, log, cap, gap = setup()
        text = page.render(s, log, 'room ? 1/5', cap, gap)
        self.assertRegex(text, r'<tr class="sold"[^>]*>\s*<td><s>Jaxson Hayes</s> Mitch \$70</td>')

    def test_names_are_escaped_and_the_filter_box_survives_reload(self):
        s, log, cap, gap = setup()
        text = page.render(s, log, 'room ? 1/5', cap, gap)
        self.assertIn('D&#x27;Angelo Russell', text)
        self.assertRegex(text, r'<input[^>]*id="q"[^>]*autofocus')
        self.assertIn('location.hash', text)

    def test_reloads_only_when_the_watchers_beat_says_the_page_was_rewritten(self):
        s, log, cap, gap = setup()
        text = page.render(s, log, 'room ? 1/5', cap, gap)
        self.assertRegex(text, r'const GEN = \d{10}\.\d+;')
        self.assertIn('beat.js?_=', text)
        self.assertIn('b.v - GEN > 1', text)
        self.assertNotRegex(text, r'setTimeout\([^)]*location\.reload')


if __name__ == '__main__':
    unittest.main()
