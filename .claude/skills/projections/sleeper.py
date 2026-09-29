"""RotoWire's per-game projections, off Sleeper's free API, scored to our rules.

    python3 .claude/skills/projections/sleeper.py refresh          # rewrite the snapshot
    python3 .claude/skills/projections/sleeper.py roster <path>    # projected vs last-season rate

`SKILL.md` owns when to run these and what the numbers mean.
"""
import datetime
import json
import os
import re
import sys
import unicodedata
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scoring

SEASON = "2026"                      # Sleeper labels a season by its opening year
URL = ("https://api.sleeper.com/projections/nba/%s?season_type=regular"
       "&position[]=PG&position[]=SG&position[]=SF&position[]=PF&position[]=C"
       "&order_by=pts" % SEASON)

SNAPSHOT = os.path.join(HERE, os.pardir, os.pardir, os.pardir, "evals",
                        "board-snapshots", "projections",
                        "sleeper-%s.json" % SEASON)

SUFFIXES = re.compile(r"\b(jr|sr|ii|iii|iv)\b")

# Hashtag uses Alexandre / Nicolas / Ron, pool and FanScout use Alex / Nic / Ronald
ALIASES = {
    "alexandresarr": "alexsarr",
    "nicolasclaxton": "nicclaxton",
    "ronholland": "ronaldholland",
}


def norm(name):
    """Fold a name to its join key, past the suffixes and accents the feed and
    Fleaflicker disagree about."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    key = re.sub(r"[^a-z]", "", SUFFIXES.sub("", ascii_name.lower()))
    return ALIASES.get(key, key)


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def projected_rows(rows):
    """Only the rows carrying a real stat line -- the rest are ADP or retired."""
    out = []
    for row in rows:
        stats = row.get("stats") or {}
        player = row.get("player") or {}
        if not stats.get("pts"):
            continue
        out.append({"name": ("%s %s" % (player.get("first_name", ""),
                                        player.get("last_name", ""))).strip(),
                    "team": row.get("team"),
                    "updated": row.get("updated_at", 0),
                    "stats": stats})
    return out


def snapshot(rows):
    """The file `refresh` writes -- rows plus the update stamp and depth every
    eval has to cite about a source (`Eval Template.md`)."""
    return {"season": SEASON,
            "source": "rotowire via sleeper",
            "updated": max((row["updated"] for row in rows), default=0),
            "depth": len(rows),
            "rows": rows}


def index(rows):
    """name key -> FPts/G under our scoring. Refuses a collision rather than
    letting one row win -- two players folding to one key is how a projection
    silently lands on the wrong man."""
    out = {}
    for row in rows:
        key = norm(row["name"])
        if key in out:
            raise ValueError("names collide on %r -- disambiguate by team" % key)
        out[key] = scoring.rate(scoring.line_from_sleeper(row["stats"]))
    return out


def lookup(name, idx):
    return idx.get(norm(name))


def apply(roster, idx):
    """Re-rate a roster, and hand back the names with no projection. Those keep
    last season's rate, so the caller has to publish the list -- a silent
    fallback is a stale rate wearing a fresh label."""
    out, missing = [], []
    for player in roster:
        rated = dict(player)
        projected = lookup(player["n"], idx)
        if projected is None:
            missing.append(player["n"])
        else:
            rated["avg"] = round(projected, 6)
        out.append(rated)
    return out, missing


def stamp(ms):
    """The feed's update time as a date, for an eval's header."""
    if not ms:
        return "unknown"
    return datetime.datetime.fromtimestamp(
        ms / 1000, datetime.timezone.utc).date().isoformat()


def refresh():
    snap = snapshot(projected_rows(fetch()))
    os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
    with open(SNAPSHOT, "w") as f:
        json.dump(snap, f, indent=1)
    print("wrote %d rows, feed updated %s -> %s"
          % (snap["depth"], stamp(snap["updated"]), os.path.relpath(SNAPSHOT)))
    return snap["rows"]


def load():
    with open(SNAPSHOT) as f:
        return json.load(f)["rows"]


def _roster(path):
    with open(path) as f:
        roster = json.load(f)
    rated, missing = apply(roster, index(load()))
    print("%-26s %7s %7s %7s" % ("player", "last", "proj", "delta"))
    for old, new in zip(roster, rated):
        name = old["n"][:26]
        if old["n"] in missing:
            print("%-26s %7.1f %7s  --  no projection" % (name, old["avg"], "-"))
        else:
            print("%-26s %7.1f %7.1f %+7.1f"
                  % (name, old["avg"], new["avg"], new["avg"] - old["avg"]))
    if missing:
        print("\nno projection (last season's rate stands): %s" % ", ".join(missing))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "refresh"
    if cmd == "refresh":
        refresh()
    elif cmd == "roster":
        _roster(sys.argv[2])
    else:
        sys.exit(__doc__)
