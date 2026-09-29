# python3 .claude/skills/eval-pick/test_pick_prices.py    (offline, no network)
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pick_prices.py')
DYN_HEADER = 'year\tround\tslot\trank\tvalue\tp25\tp75\tw\tprovenance'
CROWD_HEADER = 'rank,player,hashtag_id,team,pos,age,keeper_value'
MANIFEST_HEADER = ('board,file,title,source_url,controls,board_updated,fetched_utc,rows,max_rank,'
                   'pick_bands,votes,class_loading_notice')


def setup(dyn_cells, crowd_bands=(), notice=''):
    """A board-snapshots dir. dyn_cells: (year, round, slot, rank, w); every other cell of
    '27-'29 R1-R4 is filled at a rank rising with its ordinal, as a real board does. crowd_bands: (rank, name)."""
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, 'dynatyze'))
    os.makedirs(os.path.join(root, 'hashtag-basketball'))
    given = {(y, r, s): (rank, w) for y, r, s, rank, w in dyn_cells}
    lines = [DYN_HEADER]
    for y in (2027, 2028, 2029):
        for r in (1, 2, 3, 4):
            for s in range(1, 13):
                rank, w = given.get((y, r, s), (20 + 8 * ((r - 1) * 12 + s), 0))
                lines.append(f'{y}\t{r}\t{s:02d}\t{rank}\t0\t0\t0\t{w}\tengine')
    with open(os.path.join(root, 'dynatyze', 'pick-board-2026-09-29.tsv'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    with open(os.path.join(root, 'hashtag-basketball', 'crowd-keeper.csv'), 'w') as f:
        f.write('\n'.join([CROWD_HEADER, '1,Some Player,1,BOS,PG,25,2000']
                          + [f'{rank},{name},9,DRA,,,1000' for rank, name in crowd_bands]) + '\n')
    with open(os.path.join(root, 'hashtag-basketball', 'manifest.csv'), 'w') as f:
        f.write(MANIFEST_HEADER + '\n'
                + f'crowd-keeper,crowd-keeper.csv,t,u,GET,29 September 2026,x,1,1,1,1,{notice}\n')
    return root


def run(root, *ranges):
    out = subprocess.run([sys.executable, SCRIPT, '--snapshots', root, *ranges],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout


def price(out, year, row, rnd):
    """VALUE printed for `row` ('05' or '05–11') in round `rnd` of year `year` ('27)."""
    section = out.split(f"## {year} ")[1].split('\n## ')[0]
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip('|').split('|')]
        if cells[0] == row:
            return int(cells[rnd])
    raise AssertionError(f'no row {row} under {year}:\n{out}')


sys.path.insert(0, os.path.join(os.path.dirname(SCRIPT), os.pardir, 'eval-player'))
from base import curve  # noqa: E402
_, V = curve(456)


class TestPickPrices(unittest.TestCase):
    def test_a_cell_with_no_crowd_band_prices_at_its_dynatyze_rank(self):
        root = setup([(2028, 2, 1, 169, 0)])
        self.assertEqual(price(run(root), "'28", '01', 2), round(V(169)))

    def test_a_narrow_crowd_band_averages_half_and_half_with_dynatyze_whatever_the_trade_weight(self):
        root = setup([(2027, 1, 10, 98, 0.5605), (2027, 2, 1, 128, 0)],
                     crowd_bands=[(125, '2027 Draft (Pick 9-14)')])
        out = run(root)
        self.assertEqual(price(out, "'27", '10', 1), round((V(98) + V(125)) / 2))
        self.assertEqual(price(out, "'27", '01', 2), round((V(128) + V(125)) / 2))

    def test_a_band_as_wide_as_one_of_our_rounds_blends_and_one_pick_wider_does_not(self):
        root = setup([(2027, 2, 3, 142, 0), (2028, 2, 3, 142, 0)],
                     crowd_bands=[(183, '2027 Draft (Pick 15-26)'), (183, '2028 Draft (Pick 15-27)')])
        out = run(root)
        self.assertEqual(price(out, "'27", '03', 2), round((V(142) + V(183)) / 2))
        self.assertEqual(price(out, "'28", '03', 2), round(V(142)))

    def test_a_crowd_blend_that_lifts_a_pick_above_an_earlier_one_is_capped(self):
        root = setup([(2027, 1, 1, 60, 0.5605), (2027, 1, 2, 64, 0.5605)], crowd_bands=[(5, '2027 Draft (Pick 2)')])
        self.assertEqual(price(run(root), "'27", '02', 1), round(V(60)))

    def test_a_crowd_band_wider_than_one_of_our_rounds_is_ignored(self):
        root = setup([(2027, 3, 12, 315, 0)], crowd_bands=[(211, '2027 Draft (Pick 31-44)')])
        self.assertEqual(price(run(root), "'27", '12', 3), round(V(315)))

    def test_crowd_pick_rows_price_only_the_class_they_name(self):
        root = setup([(2028, 1, 1, 70, 0.4753)], crowd_bands=[(22, '2027 Draft (Pick 1)')])
        self.assertEqual(price(run(root), "'28", '01', 1), round(V(70)))

    def test_a_class_loading_notice_drops_the_crowd(self):
        root = setup([(2027, 1, 1, 28, 0.5605)], crowd_bands=[(22, '2027 Draft (Pick 1)')],
                     notice='The 2027 draft class is being loaded into the voting system')
        self.assertEqual(price(run(root), "'27", '01', 1), round(V(28)))

    def test_no_pick_prices_above_an_earlier_ordinal_of_the_same_draft(self):
        root = setup([(2027, 3, 11, 306, 0), (2027, 3, 12, 315, 0), (2027, 4, 1, 296, 0)])
        out = run(root)
        self.assertEqual(price(out, "'27", '12', 3), round(V(315)))
        self.assertEqual(price(out, "'27", '01', 4), round(V(315)))

    def test_a_slot_range_prices_at_the_mean_of_its_slots_in_every_round(self):
        root = setup([])
        out = run(root, '1.05-1.07')
        for rnd in (1, 2, 3, 4):
            slots = [price(out, "'29", f'{s:02d}', rnd) for s in (5, 6, 7)]
            self.assertAlmostEqual(price(out, "'29", '05–07', rnd), sum(slots) / 3, delta=1)
        self.assertAlmostEqual(price(out, "'28", '01–12', 2),
                               sum(price(out, "'28", f'{s:02d}', 2) for s in range(1, 13)) / 12, delta=1)

    def test_a_4th_never_takes_a_crowd_band_even_a_narrow_one(self):
        root = setup([(2027, 4, 1, 316, 0)], crowd_bands=[(440, '2027 Draft (Pick 37-40)')])
        self.assertEqual(price(run(root), "'27", '01', 4), round(V(316)))

    def test_each_draft_names_the_crowd_bands_it_blended_the_trade_weights_and_the_capped_picks(self):
        root = setup([(2027, 1, s, 20 + 8 * s, 0.5605) for s in range(1, 13)] + [(2027, 4, 1, 296, 0)],
                     crowd_bands=[(22, '2027 Draft (Pick 1)'), (125, '2027 Draft (Pick 9-14)'),
                                  (183, '2027 Draft (Pick 15-30)')])
        section = run(root).split("## '27 ")[1].split('\n## ')[0]
        basis = [line for line in section.splitlines() if line.startswith(('crowd', 'w ', 'capped'))]
        self.assertEqual(basis, ['crowd 50/50: 1.01 Pick 1 · 1.09–2.02 Pick 9-14',
                                 'w R1 market (w 0.56) · R2 template · R3 template · R4 template',
                                 'capped at an earlier ordinal: 4.01'])


if __name__ == '__main__':
    unittest.main()
