---
description: Google Sheets — use whenever an agent or tool reads a public (link-view) Google Sheet or polls one for changes
---

Read only: never write to a Sheet you don't own.

## Helper

`sheets.py` (stdlib, `python3`):

- `read(src)` gives CSV rows from a URL or a local file. It raises `SheetError` when the body is an error page, not CSV.
- `export_url(sheet_id, gid=0, rng=None)`
- `poll(fetch, every, key)` yields `(rows, None)` when `key(rows)` changes and `(None, err)` once per failure streak. `key` limits what counts as a change.

Tests: `python3 .claude/skills/google-sheets/test_sheets.py`

## Endpoints

| Form | URL tail | Median | Use |
|---|---|---:|---|
| export | `/export?format=csv&gid=<gid>` | ~300 ms | default: literal cell text, every row |
| gviz | `/gviz/tq?tqx=out:csv&gid=<gid>&range=<A1>&headers=0` | ~150 ms | one-off cell or name lookups (`&tq=select A where A contains 'X'`) |
| xlsx | `/export?format=xlsx` | slower | formulas, strikethrough and tab names (`openpyxl` via `uv run`, see `dizzle-dynasty`) |

A range doesn't make the export faster; the server renders the whole sheet either way.

## Quirks

- Export 307-redirects, so follow redirects (`urllib` and `curl -L` do).
- Errors come back as bodies, not CSV. A bad `gid` on export gives HTTP 400 with an HTML page. A bad `tq` on gviz gives HTTP 200 with JSON `{"status":"error"}`. `read` sniffs both.
- gviz infers a type per column and blanks cells that don't fit, e.g. a `$12` typed as text in a numeric column. Never poll through gviz for data you act on.
- gviz and ranged export drop blank rows. Row numbers shift, so anchor on label cells, not row indices.
- CSV has formatted values: currency reads `$12` or `$12.00`, and `3.10` can read `3.1`. Cells can carry zero-width spaces and curly apostrophes.
- CSV can't show strikethrough or formulas. Use xlsx once to learn which cells are formulas.
- There's no ETag or 304. Every poll is a full live render.

## Polling

- Poll with export every 2–5 s. 1 s works too; no throttling was seen at 1 read per 2–4 s over 5 min.
- Set `key` to the region a real change touches, so edits elsewhere don't fire.
- Run the poller as a `Monitor` in the main session: stdout prints only on change, one line per event; timings go to stderr. A subagent costs a model turn per poll and can't push; `loop` has a 1-minute floor.
- Monitors expire after 30 min, so re-arm on expiry. The poller must be restart-safe: keep state in files and diff against them on start.
- If the Sheet can't be reached: File > Download > CSV, then point the poller's `src` at the file.
