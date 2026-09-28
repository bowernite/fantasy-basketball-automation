"""Assumed-through trades. Terms: `evals/Pending Trades.md`.

`fetch_data.py roster` applies these after the wire cut. Idempotent once
Fleaflicker matches; drop a deal here once the wire shows it.
"""

US, HLINA = 161025, 161021

# (name, from, to)
MOVES = (
    ("Jalen Duren", US, HLINA),
    ("Jalen Green", HLINA, US),
    ("Toumani Camara", HLINA, US),
    ("Jabari Smith", HLINA, US),
)

# (name, from) — gone from the league, not a move
DROPS = ()

INVOLVED = frozenset(t for _, a, b in MOVES for t in (a, b)) | {t for _, t in DROPS}


def expand_ids(ids):
    """If any requested team is in a deal, fetch every side so files cannot
    double-own a body."""
    s = {int(t) for t in ids}
    if s & INVOLVED:
        s |= INVOLVED
    return sorted(s)


def _index(rosters):
    """name -> (team holding him, row) -- the owner matters: resolved by name
    alone, an incoming name could come off the wrong team's file, doubling
    ownership."""
    out = {}
    for tid, rows in rosters.items():
        for r in rows:
            out[r["n"]] = (tid, r)
    return out


def _desired(team_id, live):
    names = set(live)
    for n, src in DROPS:
        if src == team_id:
            names.discard(n)
    for n, src, dst in MOVES:
        if src == team_id:
            names.discard(n)
        if dst == team_id:
            names.add(n)
    return names


def apply_all(rosters):
    """`rosters` is `{team_id: [rows]}`. Mutates. Returns how many teams
    changed. Missing incoming names are skipped (print), not invented."""
    by_name = _index(rosters)
    changed = 0
    for tid, rows in list(rosters.items()):
        want = _desired(tid, [r["n"] for r in rows])
        incoming = {n: src for n, src, dst in MOVES if dst == tid}
        have, new, missing = set(), [], []
        for r in rows:
            if r["n"] in want and r["n"] not in have:
                new.append(r)
                have.add(r["n"])
        for n in sorted(want - have):
            found = by_name.get(n)
            if found is None:
                missing.append(n)
                continue
            owner, row = found
            if owner != incoming[n]:
                raise ValueError(
                    "%s is on %s, but MOVES has him coming from %s -- retype "
                    "the deal against the live wire (`evals/Pending "
                    "Trades.md`)." % (n, owner, incoming[n]))
            new.append(row)
            have.add(n)
        if missing:
            print("  assumed overlay: %s not on any fetched roster: %s"
                  % (tid, ", ".join(missing)))
        if [r["n"] for r in new] != [r["n"] for r in rows]:
            changed += 1
        rosters[tid] = new
    return changed
