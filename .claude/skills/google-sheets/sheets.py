"""Read public (link-view) Google Sheets as CSV rows. Stdlib only. See google-sheets.md."""
import csv
import io
import time
import urllib.request

BASE = 'https://docs.google.com/spreadsheets/d/'


class SheetError(Exception):
    pass


def read(src, timeout=10):
    """Rows of a CSV URL or local file. Raises SheetError on an error body instead of CSV."""
    if src.startswith('http'):
        with urllib.request.urlopen(src, timeout=timeout) as r:
            body = r.read().decode('utf-8')
    else:
        with open(src, encoding='utf-8') as f:
            body = f.read()
    head = body.lstrip()[:15].lower()
    if head.startswith('{') or head.startswith('<'):
        raise SheetError(body[:200])
    return list(csv.reader(io.StringIO(body)))


def export_url(sheet_id, gid=0, rng=None):
    return f'{BASE}{sheet_id}/export?format=csv&gid={gid}' + (f'&range={rng}' if rng else '')


def poll(fetch, every, key=lambda rows: rows):
    """Yield (rows, None) when key(rows) changes and (None, err) once per failure streak."""
    last = object()
    while True:
        try:
            rows, err = fetch(), None
            mark = key(rows)
        except Exception as e:  # network, HTTP, SheetError: all mean "no fresh read"
            rows, err, mark = None, e, 'error'
        if mark != last:
            last = mark
            yield rows, err
        time.sleep(every)
