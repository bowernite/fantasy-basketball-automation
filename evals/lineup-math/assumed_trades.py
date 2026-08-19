"""Assumed-through trades. Terms: `evals/Pending Trades.md`.

`fetch_data.py roster` applies these after the wire cut. Idempotent once
Fleaflicker matches. Amen is not on the wire at all until expansion.
"""

US, HENRY, MATTHEW = 161025, 161019, 160941

# (name, from, to)
MOVES = (
    ("DaRon Holmes", US, HENRY),
    ("De'Andre Hunter", HENRY, US),
    ("Amen Thompson", US, MATTHEW),
    ("Keegan Murray", MATTHEW, US),
    ("Shaedon Sharpe", MATTHEW, US),
    ("Tari Eason", MATTHEW, US),
    ("Devin Vassell", MATTHEW, US),
    ("Jonathan Kuminga", MATTHEW, US),
)

# (name, from) — gone from the league, not a move
DROPS = (("Zeke Nnaji", HENRY),)

INVOLVED = frozenset(t for _, a, b in MOVES for t in (a, b)) | {t for _, t in DROPS}


def expand_ids(ids):
    """If any requested team is in a deal, fetch every side so files cannot
    double-own a body."""
    s = {int(t) for t in ids}
    if s & INVOLVED:
        s |= INVOLVED
    return sorted(s)


def _index(rosters):
    """name -> (team holding him, row).

    The OWNER is half the answer. An incoming name resolved across the league
    by name alone comes off whoever happens to hold it, and if that is not the
    source `MOVES` names, the file being emptied is not the file being copied
    from -- two teams then own one body.
    """
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
                    "%s is on %s, not on %s where MOVES has him coming from. "
                    "Copied onto %s he stays on %s as well, so two roster "
                    "files own one body and the sim reads his level twice. "
                    "Retype the deal against the live wire (`evals/Pending "
                    "Trades.md`)." % (n, owner, incoming[n], tid, owner))
            new.append(row)
            have.add(n)
        if missing:
            print("  assumed overlay: %s not on any fetched roster: %s"
                  % (tid, ", ".join(missing)))
        if [r["n"] for r in new] != [r["n"] for r in rows]:
            changed += 1
        rosters[tid] = new
    return changed
