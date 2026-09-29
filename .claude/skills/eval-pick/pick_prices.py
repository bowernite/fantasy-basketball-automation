# Future-pick VALUE table (`future-picks.md` owns the rule) off the dated snapshots. Reads, never fetches.
#
#   python3 .claude/skills/eval-pick/pick_prices.py 1.05-1.11 1.03-1.09   # slot ranges to average, any round
#
# Guard, offline: python3 .claude/skills/eval-pick/test_pick_prices.py
import argparse, csv, glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, os.pardir, 'eval-player'))
from base import ROSTER_SIZE, TEAMS, curve  # noqa: E402

SNAPSHOTS = os.path.join(HERE, os.pardir, os.pardir, os.pardir, 'strategy', 'board-snapshots')
ROUNDS, SLOTS = 4, 12
ROUND_NAMES = ('1st', '2nd', '3rd', '4th')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--snapshots', default=SNAPSHOTS)
    ap.add_argument('ranges', nargs='*', type=slot_range, help='R.SS-R.SS, e.g. 1.05-1.11; the round is ignored')
    args = ap.parse_args()
    ranges = [(1, SLOTS)] + [r for r in args.ranges if r != (1, SLOTS)]
    D = TEAMS * ROSTER_SIZE
    _, V = curve(D)
    dyn_path, cells = dynatyze_cells(args.snapshots)
    crowd_stamp, bands = crowd_bands(args.snapshots)
    print(f'DYNATYZE {os.path.basename(dyn_path)} · CROWD {crowd_stamp} · D {D}')
    for year in sorted({y for y, _, _ in cells}):
        prices, used, capped = draft_prices(V, cells, bands, year)
        print(f"\n## '{year % 100:02d} (Sept {year} draft)\n")
        print('| slot | ' + ' | '.join(ROUND_NAMES) + ' |')
        print('|---' * (ROUNDS + 1) + '|')
        for s in range(1, SLOTS + 1):
            print(table_row(f'{s:02d}', [prices[r, s] for r in range(1, ROUNDS + 1)]))
        for lo, hi in ranges:
            means = [sum(prices[r, s] for s in range(lo, hi + 1)) / (hi - lo + 1) for r in range(1, ROUNDS + 1)]
            print(table_row(f'{lo:02d}–{hi:02d}', means))
        print()
        print('crowd 50/50: ' + (' · '.join(f"{span(ords)} {name}" for name, ords in used.items()) or 'none'))
        print('w ' + ' · '.join(f'R{r} {weight_label(cells, year, r)}' for r in range(1, ROUNDS + 1)))
        print('capped at an earlier ordinal: ' + (', '.join(label(o) for o in capped) or 'none'))


def draft_prices(V, cells, bands, year):
    """-> {(round, slot): VALUE}, {crowd band: [ordinals blended]}, [capped ordinals]

    VALUE = V(Dynatyze rank), averaged 50/50 in V with the crowd band holding the ordinal when that band
    names this class, spans at most one of our rounds and the pick is not a 4th; then capped at every
    earlier ordinal's VALUE"""
    prices, used, capped, cap = {}, {}, [], float('inf')
    for rnd in range(1, ROUNDS + 1):
        for slot in range(1, SLOTS + 1):
            ordinal = (rnd - 1) * SLOTS + slot
            raw = V(cells[year, rnd, slot][0])
            band = next((b for b in bands if b['year'] == year and b['hi'] - b['lo'] + 1 <= SLOTS
                         and b['lo'] <= ordinal <= b['hi']), None)
            if band and rnd < ROUNDS:
                raw = (raw + V(band['rank'])) / 2
                used.setdefault(band['name'], []).append(ordinal)
            if raw > cap:
                capped.append(ordinal)
            cap = min(cap, raw)
            prices[rnd, slot] = cap
    return prices, used, capped


def weight_label(cells, year, rnd):
    weights = sorted({cells[year, rnd, s][1] for s in range(1, SLOTS + 1)})
    return ' / '.join('template' if w == 0 else f'market (w {w:.2g})' for w in weights)


def table_row(first, values):
    return f'| {first} | ' + ' | '.join(str(round(v)) for v in values) + ' |'


def label(ordinal):
    return f'{(ordinal - 1) // SLOTS + 1}.{(ordinal - 1) % SLOTS + 1:02d}'


def span(ordinals):
    return label(ordinals[0]) if len(ordinals) == 1 else f'{label(ordinals[0])}–{label(ordinals[-1])}'


def slot_range(text):
    m = re.fullmatch(r'(\d)\.(\d\d)-(\d)\.(\d\d)', text)
    lo, hi = (int(m.group(2)), int(m.group(4))) if m and m.group(1) == m.group(3) else (0, 0)
    if not 1 <= lo <= hi <= SLOTS:
        raise argparse.ArgumentTypeError(f'{text!r}: want R.SS-R.SS, one round, slots 01-{SLOTS} in order')
    return lo, hi


def crowd_bands(root):
    """-> (board stamp, [{year, lo, hi, rank, name}]), lo/hi in the NBA's 60-slot space; no bands while the
    class-loading notice shows"""
    with open(os.path.join(root, 'hashtag-basketball', 'manifest.csv')) as f:
        crowd = next((r for r in csv.DictReader(f) if r['board'] == 'crowd-keeper'), None)
    if crowd is None:
        sys.exit(f'NO CROWD ROW in {root}/hashtag-basketball/manifest.csv')
    if crowd['class_loading_notice'].strip():
        return f"{crowd['board_updated']} (class-loading notice: dropped)", []
    with open(os.path.join(root, 'hashtag-basketball', 'crowd-keeper.csv')) as f:
        rows = [r for r in csv.DictReader(f) if r['team'] == 'DRA']
    bands = []
    for r in rows:
        m = re.fullmatch(r'(\d{4}) Draft \(Pick (\d+)(?:-(\d+))?\)', r['player'])
        if not m:
            sys.exit(f"UNREADABLE CROWD PICK ROW {r['player']!r}")
        lo = int(m.group(2))
        bands.append({'year': int(m.group(1)), 'lo': lo, 'hi': int(m.group(3) or lo), 'rank': int(r['rank']),
                      'name': r['player'].split('(')[1].rstrip(')')})
    return crowd['board_updated'], bands


def dynatyze_cells(root):
    """Newest pick board -> (path, {(year, round, slot): (rank, w)})"""
    paths = sorted(glob.glob(os.path.join(root, 'dynatyze', 'pick-board-*.tsv')))
    if not paths:
        sys.exit(f'NO SNAPSHOT — no pick-board-*.tsv in {root}/dynatyze')
    with open(paths[-1]) as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    cells = {(int(r['year']), int(r['round']), int(r['slot'])): (int(r['rank']), float(r['w'])) for r in rows}
    missing = [f"'{y % 100:02d} {r}.{s:02d}" for y in {y for y, _, _ in cells}
               for r in range(1, ROUNDS + 1) for s in range(1, SLOTS + 1) if (y, r, s) not in cells]
    if missing:
        sys.exit(f'INCOMPLETE {os.path.basename(paths[-1])}: missing ' + ', '.join(missing))
    return paths[-1], cells


if __name__ == '__main__':
    main()
