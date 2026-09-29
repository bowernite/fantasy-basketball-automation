"""FanScout projected season GP

    python3 .claude/skills/projections/fanscout_gp.py refresh
"""
import datetime
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sleeper

SNAPSHOT = os.path.join(HERE, os.pardir, os.pardir, os.pardir, "strategy",
                        "board-snapshots", "projections",
                        "fanscout-gp-2026.json")
# `players` defaults to 150 on the site; ask for more than the board holds.
URL = "https://fanscout.pro/projections?players=1000"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
MIN_DEPTH = 400  # full board runs ~480
ROOKIES_2026_27 =("AJ Dybantsa", "Darryn Peterson", "Cameron Boozer")


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


def parse(page):
    title = re.search(r"<title>([^<]*)</title>", page)
    title = title.group(1) if title else ""
    if "2026-27" not in title.replace("\u2013", "-"):
        raise ValueError("WRONG SEASON: %s" % title)
    rows = []
    for m in re.finditer(
            r'self\.__next_f\.push\(\[1,"((?:\\.|[^"\\])*)"\]\)', page):
        chunk = json.loads('"' + m.group(1) + '"')
        if "playerName" not in chunk:
            continue
        body = chunk[chunk.find("["):]
        obj = json.loads(body)
        data = obj[3]["data"]
        for row in data:
            rows.append({"name": row["playerName"],
                         "gp": float(row["gamesPlayed"]),
                         "team": row.get("team")})
    if not rows:
        raise ValueError("NO PLAYER ROWS")
    names = {r["name"] for r in rows}
    missing = [n for n in ROOKIES_2026_27 if n not in names]
    if missing:
        raise ValueError("STALE SEASON: missing rookies %s" % missing)
    rookies = [r for r in rows if r["name"] in ROOKIES_2026_27]
    return {"season": "2026-27",
            "source": "fanscout projections",
            "title": title,
            "rookies": rookies,
            "rows": rows}


def snapshot(parsed, fetched=None):
    rows = parsed["rows"]
    if fetched is None:
        fetched = (datetime.datetime.now(datetime.timezone.utc)
                   .replace(microsecond=0).isoformat()
                   .replace("+00:00", "Z"))
    return {"season": parsed["season"],
            "source": parsed["source"],
            "url": URL,
            "title": parsed["title"],
            "fetched": fetched,
            "depth": len(rows),
            "rookies": parsed["rookies"],
            "rows": rows}


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": UA, "Referer": URL})
    return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")


def pull():
    parsed = parse(fetch())
    if len(parsed["rows"]) < MIN_DEPTH:
        raise ValueError("SHORT BOARD: %d rows, want >= %d -- is `players` in URL "
                         "still honored?" % (len(parsed["rows"]), MIN_DEPTH))
    return parsed


def refresh():
    snap = snapshot(pull())
    os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
    with open(SNAPSHOT, "w") as f:
        json.dump(snap, f, indent=1)
    print("wrote %d rows (%s) fetched %s -> %s"
          % (snap["depth"], snap["season"], snap["fetched"],
             os.path.relpath(SNAPSHOT)))
    return snap


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "refresh"
    if cmd == "refresh":
        refresh()
    else:
        sys.exit(__doc__)
