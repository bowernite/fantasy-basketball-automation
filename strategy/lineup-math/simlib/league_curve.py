"""Roster-agnostic fielded PF: mean 38th-body curve across all 12 rosters.

Re-cut with `sim.py league-curve` when the calendar or the twelve files move.
"""
CURVE_RATE = (0, 5, 8, 11, 14, 17, 20, 23, 26, 30, 35, 40, 48)
CURVE_PF60 = (0, 12, 19, 35, 61, 104, 168, 255, 358, 522, 738, 955, 1304)
CURVE_SLOPE = 43.1
CURVE_GP = 60


def league_pf(rate, gp):
    if rate <= 0 or gp <= 0:
        return 0.0
    if rate >= CURVE_RATE[-1]:
        v = CURVE_PF60[-1] + (rate - CURVE_RATE[-1]) * CURVE_SLOPE
    else:
        i = 0
        while i < len(CURVE_RATE) - 1 and CURVE_RATE[i + 1] <= rate:
            i += 1
        r0, r1 = CURVE_RATE[i], CURVE_RATE[i + 1]
        v0, v1 = CURVE_PF60[i], CURVE_PF60[i + 1]
        v = v0 + (v1 - v0) * (rate - r0) / (r1 - r0)
    return v * gp / CURVE_GP
