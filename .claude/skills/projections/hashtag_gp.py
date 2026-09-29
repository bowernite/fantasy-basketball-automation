"""Hashtag Basketball projected GP. One of two feeds `project_gp` averages when present.

    python3 .claude/skills/projections/hashtag_gp.py refresh
"""
import html as htmlmod
import json
import os
import re
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sleeper

SNAPSHOT = os.path.join(HERE, os.pardir, os.pardir, os.pardir, "strategy",
                        "board-snapshots", "projections",
                        "hashtag-gp-2026.json")
URL = "https://hashtagbasketball.com/fantasy-basketball-projections"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
SHOW = "900"


def load():
    with open(SNAPSHOT) as f:
        return json.load(f)["rows"]


def index(rows):
    out = {}
    for row in rows:
        key = sleeper.norm(row["name"])
        if key in out:
            raise ValueError("names collide on %r -- disambiguate by team" % key)
        out[key] = float(row["gp"])
    return out


def lookup(name, idx):
    return idx.get(sleeper.norm(name))


def sel(h, ctrl):
    block = re.search(
        r'<select[^>]*id="ContentPlaceHolder1_' + ctrl + r'"[^>]*>([\s\S]*?)</select>',
        h)
    if not block:
        return None, None
    m = (re.search(r'<option[^>]*selected[^>]*value="([^"]*)"[^>]*>([^<]*)',
                   block.group(1))
         or re.search(r'<option[^>]*value="([^"]*)"[^>]*selected[^>]*>([^<]*)',
                      block.group(1)))
    return (m.group(1), m.group(2).strip()) if m else (None, None)


def hid(h, name):
    m = re.search(r'name="' + name + r'"[^>]*value="([^"]*)"', h)
    return htmlmod.unescape(m.group(1)) if m else ""


def parse(page):
    title = re.search(r"<title>([^<]*)</title>", page)
    title = title.group(1) if title else ""
    if "2026-27" not in title:
        raise ValueError("WRONG SEASON: %s" % title)
    duration, label = sel(page, "DDDURATION")
    if duration is None:
        raise ValueError("no DDDURATION control")
    if "STREAM" in label.upper() or "SHORT TERM" in label.upper():
        raise ValueError("STREAM/short-term board is not season GP: %s" % label)
    rows = []
    gp_i = team_i = None
    for tr in re.findall(r"<tr[\s\S]*?</tr>", page):
        ths = [re.sub(r"<[^>]+>", "", c).strip()
               for c in re.findall(r"<th[^>]*>([\s\S]*?)</th>", tr)]
        if "GP" in ths:
            gp_i = ths.index("GP")
            team_i = ths.index("TEAM") if "TEAM" in ths else None
            continue
        name = re.search(
            r'class="d-none d-sm-inline"[^>]*>([^<]+)</a>', tr)
        cells = [re.sub(r"<[^>]+>", "", c).strip()
                 for c in re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr)]
        if not name or gp_i is None or gp_i >= len(cells):
            continue
        row = {"name": name.group(1).strip(), "gp": float(cells[gp_i])}
        if team_i is not None and team_i < len(cells):
            row["team"] = cells[team_i]
        rows.append(row)
    if not rows:
        raise ValueError("NO PLAYER ROWS")
    upd = re.search(r"Updated:</strong>\s*([^<]*)", page)
    return {"season": "2026-27",
            "source": "hashtag basketball projections",
            "title": title,
            "duration": duration,
            "duration_label": label,
            "updated": upd.group(1).strip() if upd else "",
            "rows": rows}


def fetch(data=None):
    hdrs = {"User-Agent": UA, "Referer": URL}
    if data:
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    return urllib.request.urlopen(
        urllib.request.Request(URL, data=data, headers=hdrs), timeout=90
    ).read().decode("utf-8", "replace")


def pull():
    page = fetch()
    body = {"__EVENTTARGET": "ctl00$ContentPlaceHolder1$DDSHOW",
            "__EVENTARGUMENT": "", "__LASTFOCUS": "",
            "__VIEWSTATE": hid(page, "__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": hid(page, "__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": hid(page, "__EVENTVALIDATION"),
            "ctl00$ContentPlaceHolder1$DDSHOW": SHOW}
    duration, _ = sel(page, "DDDURATION")
    if duration is not None:
        body["ctl00$ContentPlaceHolder1$DDDURATION"] = duration
    page = fetch(urllib.parse.urlencode(body).encode())
    show, _ = sel(page, "DDSHOW")
    if show != SHOW:
        raise ValueError("DDSHOW asked %s, page shows %s -- DISCARD" % (SHOW, show))
    parsed = parse(page)
    if len(parsed["rows"]) < 100:
        raise ValueError("only %d rows -- DDSHOW=%s did not stick"
                         % (len(parsed["rows"]), SHOW))
    return parsed


def snapshot(parsed):
    rows = parsed["rows"]
    return {"season": parsed["season"],
            "source": parsed["source"],
            "duration": parsed["duration"],
            "duration_label": parsed["duration_label"],
            "updated": parsed["updated"],
            "depth": len(rows),
            "rows": rows}


def refresh():
    snap = snapshot(pull())
    os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
    with open(SNAPSHOT, "w") as f:
        json.dump(snap, f, indent=1)
    print("wrote %d rows (%s) -> %s"
          % (snap["depth"], snap["duration_label"], os.path.relpath(SNAPSHOT)))
    return snap["rows"]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "refresh"
    if cmd == "refresh":
        refresh()
    else:
        sys.exit(__doc__)
