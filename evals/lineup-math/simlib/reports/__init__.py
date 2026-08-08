"""The fixed report names the CLI knows, and which of them are ours alone.

Every table in `findings.md` is one of these. Add the report before the table.
"""
from .calibration import report_calibration
from .deals import report_breakevens, report_scenarios
from .durability import report_durability
from .formula import report_formula, report_positions, report_replacement
from .market import report_gp, report_market
from .nights import report_nights
from .schedules import report_schedules
from .tables import report_extras, report_players

REPORTS = {"calibration": report_calibration, "nights": report_nights,
           "scenarios": report_scenarios, "breakevens": report_breakevens,
           "replacement": report_replacement, "positions": report_positions,
           "formula": report_formula, "durability": report_durability,
           "extras": report_extras, "players": report_players,
           "market": report_market, "gp": report_gp,
           "schedules": report_schedules}

# Built on OUR player names or OUR real weekly scores, so they answer nothing
# about another team: `scenarios`/`breakevens` trade `deals.FILLER`, `durability`
# reshapes `durability.SUBJECT`, `calibration` divides by our standings PF. Named
# by constant rather than by player, which drifts. `--roster` refuses them.
OURS_ONLY = {"calibration", "scenarios", "breakevens", "durability"}
