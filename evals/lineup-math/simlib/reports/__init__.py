"""The fixed report names the CLI knows, and which of them are ours alone.

Every table in `findings.md` is one of these. Add the report before the table.
"""
from .calibration import report_calibration
from .deals import report_breakevens, report_scenarios
from .durability import report_durability
from .formula import report_formula, report_positions, report_replacement
from .market import report_gp, report_market
from .nights import report_nights
from .playoffs import report_playoffs, report_weeks
from .schedules import report_schedules
from .tables import report_extras, report_players

from ..data import REAL_MATCHUPS, SCORED

# The three units every table here is denominated in, above every one of them.
# `+2.01` on a row said nothing about whether it was a season, a week or a
# matchup, and the denominator lived only in `sim.py`'s module docstring and in
# findings.md -- two files a reader in a terminal does not have open.
UNITS = ("units: `wins` = extra wins over a %d-matchup regular season · `PF` = "
         "fantasy points\n       over the %d scored periods · `rate` = FPts per "
         "game PLAYED, not per night."
         % (REAL_MATCHUPS, len(SCORED)))


# `playoffs` is denominated in none of the three: a bracket week pays in title
# probability and its `W` columns are one period's points. Its own legend, in
# the same place above the same table, because a legend defining three units
# the table below does not carry is worse than none -- and this is the one
# table whose standing rule is that its number is never read in wins.
OWN_UNITS = {
    "playoffs": "units: `Delta P(title)` = percentage points of title "
                "probability\n       · `W20`-`W23` = EXPECTED fantasy points "
                "in that bracket period.",
    "weeks": "units: `W20`-`W23` = EXPECTED fantasy points in that bracket "
             "period.",
}


def _labelled(name, fn):
    """One legend above every report, from one place. Left to each report, the
    units were on six of fourteen and worded differently on each."""
    def run():
        print(OWN_UNITS.get(name, UNITS))
        return fn()
    run.__name__, run.__doc__ = fn.__name__, fn.__doc__
    return run


REPORTS = {name: _labelled(name, fn) for name, fn in (
    ("calibration", report_calibration), ("nights", report_nights),
    ("scenarios", report_scenarios), ("breakevens", report_breakevens),
    ("replacement", report_replacement), ("positions", report_positions),
    ("formula", report_formula), ("durability", report_durability),
    ("extras", report_extras), ("players", report_players),
    ("market", report_market), ("gp", report_gp),
    ("schedules", report_schedules), ("playoffs", report_playoffs),
    ("weeks", report_weeks))}

# One line per report, for `sim.py --help`. The CLI is the only place a caller
# meets these names, so the description has to arrive with them: a bare list of
# fourteen words sends the reader to README.md to find out which one answers his
# question, and the two files then drift.
BLURB = {
    "calibration": "NBA calendar, sim vs reality, PF -> wins and its band",
    "nights": "where the 9-slot cap bites, by night type",
    "scenarios": "the consolidation ladder: N-for-1 shapes, priced",
    "breakevens": "N-for-1 break-even incoming rate + backfill bracket",
    "replacement": "replacement level per slot group, and the formula's shape",
    "positions": "what an added body of each eligibility is worth",
    "formula": "does (rate - R) x GP predict what the sim measures, and for whom",
    "durability": "what our format pays for GP, against a board's elasticity",
    "extras": "the Sept '26 expansion and the projection's own PF delta",
    "players": "per-player Delta w, vs a replacement 68-GP body of his slot group",
    "market": "board rank <-> FPts/G, and how much of a GP season carries forward",
    "gp": "expected GP: what predicts it, and what does not",
    "schedules": "what steering the Sept '26 auction on the NBA calendar buys",
    "playoffs": "W20-W23 and seed-banded Delta P(title) per player",
    "weeks": "W20-W23 per player, closed form -- no bracket Monte Carlo",
}

# Reads the board and the pool and no roster at all, so its table is identical
# whatever `--roster` says. A header naming a team over it attributes to that
# team a measurement of nobody.
ROSTER_FREE = {"market"}

# The two that run for minutes rather than seconds, so a caller can tell a slow
# report from a hung one before he kills it.
SLOW = {"breakevens": "~3 min", "schedules": "~3 min"}

# Built on OUR player names or OUR real weekly scores, so they answer nothing
# about another team: `scenarios`/`breakevens` trade `deals.FILLER`, `durability`
# reshapes `durability.SUBJECT`, `calibration` divides by our standings PF. Named
# by constant rather than by player, which drifts. `--roster` refuses them.
OURS_ONLY = {"calibration", "scenarios", "breakevens", "durability"}
