from .calibration import report_calibration
from .deals import report_breakevens, report_scenarios
from .durability import report_durability
from .formula import report_formula, report_positions, report_replacement
from .league_curve import report_league_curve
from .market import report_gp, report_market
from .nights import report_nights
from .playoffs import report_playoffs, report_weeks
from .schedules import report_schedules
from .tables import report_extras, report_players
from .title import report_title
from .horizon import report_horizon


REPORTS = {
    "calibration": report_calibration, "nights": report_nights,
    "scenarios": report_scenarios, "breakevens": report_breakevens,
    "replacement": report_replacement, "positions": report_positions,
    "formula": report_formula, "league-curve": report_league_curve,
    "durability": report_durability,
    "extras": report_extras, "players": report_players,
    "market": report_market, "gp": report_gp,
    "schedules": report_schedules, "playoffs": report_playoffs,
    "weeks": report_weeks,     "title": report_title, "horizon": report_horizon,
}

BLURB = {
    "calibration": "NBA calendar, sim vs reality, PF -> wins and its band",
    "nights": "where the 9-slot cap bites, by night type",
    "scenarios": "the consolidation ladder: N-for-1 shapes, priced",
    "breakevens": "N-for-1 break-even incoming rate + backfill bracket",
    "replacement": "replacement level per slot group, and the formula's shape",
    "positions": "what an added body of each eligibility is worth",
    "formula": "does the league curve predict what the sim measures",
    "league-curve": "re-cut the 12-roster 38th-body table formula Δw interpolates",
    "durability": "what our format pays for GP, against a board's elasticity",
    "extras": "the Sept '26 expansion and the projection's own PF delta",
    "players": "per-player Delta w, vs a replacement 68-GP body of his slot group",
    "market": "board rank <-> FPts/G, and how much of a GP season carries forward",
    "gp": "expected GP: what predicts it, and what does not",
    "schedules": "what steering the Sept '26 auction on the NBA calendar buys",
    "playoffs": "W20-W23 and seed-conditional P(title|seed) per player "
                "(not the eval Delta P(title) column)",
    "weeks": "W20-W23 per player, closed form -- no bracket Monte Carlo",
    "title": "the whole season simulated: standings -> seeds -> bracket -> "
             "P(title)",
    "horizon": "naive Y1-Y3 PF ranks: pool age-bucket rate drift, same rosters",
}

# Reads the board and the pool, not the roster, so its table doesn't change
# under `--roster`
ROSTER_FREE = {"market"}

# rounded up from an 18-core box; `engine.run` shards trials across cores, so a
# smaller box runs slower than this
SLOW = {"breakevens": "~4s", "schedules": "~8s", "league-curve": "~15s"}

# Named by constant, not by player (`deals.FILLER`, `durability.SUBJECT`,
# `calibration`'s standings PF) -- built on OUR names/scores, so `--roster`
# refuses them
OURS_ONLY = {"calibration", "scenarios", "breakevens", "durability"}
