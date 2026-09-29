# Offline. python3 .claude/skills/google-sheets/test_sheets.py
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sheets  # noqa: E402


def write(text):
    f = tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False)
    f.write(text)
    f.close()
    return f.name


class Read(unittest.TestCase):
    def test_csv_rows(self):
        self.assertEqual(sheets.read(write('a,b\n"1,5",\n')), [['a', 'b'], ['1,5', '']])

    def test_gviz_error_json_raises(self):
        with self.assertRaises(sheets.SheetError):
            sheets.read(write('{"version":"0.6","status":"error","errors":[{"reason":"invalid_query"}]}'))

    def test_html_error_page_raises(self):
        with self.assertRaises(sheets.SheetError):
            sheets.read(write('<!DOCTYPE html><html><body>Sorry, unable to open the file</body></html>'))


class Poll(unittest.TestCase):
    def test_yields_changes_and_one_event_per_error_streak(self):
        a, b, down = [['a']], [['b']], sheets.SheetError('down')
        feed = iter([a, a, down, down, a, a, b])

        def fetch():
            x = next(feed)
            if isinstance(x, Exception):
                raise x
            return x

        got = []
        for rows, err in sheets.poll(fetch, every=0):
            got.append(rows if err is None else 'err')
            if len(got) == 4:
                break
        self.assertEqual(got, [a, 'err', a, b])

    def test_key_limits_what_counts_as_a_change(self):
        feed = iter([[['x'], ['1']], [['x'], ['2']], [['y'], ['2']]])
        got = []
        for rows, _ in sheets.poll(lambda: next(feed), every=0, key=lambda r: r[0]):
            got.append(rows)
            if len(got) == 2:
                break
        self.assertEqual(got, [[['x'], ['1']], [['y'], ['2']]])


if __name__ == '__main__':
    unittest.main()
