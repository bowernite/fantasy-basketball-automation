"""The 9 starting slots, and the exact max-weight matching that fills them."""
# 9 starters, per FetchLeagueRules rosterPositions (`league-info`).
SLOTS = [("PG", {"PG"}), ("SG", {"SG"}), ("G", {"PG", "SG"}),
         ("SF", {"SF"}), ("PF", {"PF"}), ("F", {"SF", "PF"}), ("C", {"C"}),
         ("ANY", {"PG", "SG", "SF", "PF", "C"}),
         ("ANY", {"PG", "SG", "SF", "PF", "C"})]


# DERIVED off SLOTS, never a second literal: the solver runs ~26k times per
# `run` and this is its innermost scan, so it reads the eligibility sets without
# re-unpacking the labelled tuple.
SLOT_POS = [e for _, e in SLOTS]


def lineup(avail):
    """avail: [(fpts, eligset, key)]. Max-weight assignment into the 9 slots.

    Exact: capacities are 1 and players are added in descending value, so
    greedy placement with Kuhn augmentation cannot be improved on.
    """
    assign = [None] * len(SLOT_POS)
    seen = set()

    def place(x):
        ex = avail[x][1]
        for si, elig in enumerate(SLOT_POS):
            if si in seen or not (ex & elig):
                continue
            seen.add(si)
            if assign[si] is None or place(assign[si]):
                assign[si] = x
                return True
        return False

    # Augmentation places exactly one more body per successful `place`, so the
    # count is the fill -- rescanning `assign` for it walks all 9 slots per
    # player for the whole of a night.
    filled = 0
    for pi in sorted(range(len(avail)), key=lambda i: -avail[i][0]):
        if filled == len(SLOT_POS):
            break
        seen.clear()
        if place(pi):
            filled += 1
    used = [a for a in assign if a is not None]
    return (sum(avail[a][0] for a in used), filled,
            [avail[a][2] for a in used])
