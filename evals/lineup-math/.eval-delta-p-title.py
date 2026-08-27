"""ΔP(title) column: ours on roster, Brian's incoming onto ours."""
import sim

BRIAN = "roster-161018-2025-26.json"

full = sim.basis()
ours = sim.our_roster()
print("player_title %d names ..." % len(ours), flush=True)
got = sim.player_title(full, [p["n"] for p in ours])
print("OURS")
for p in ours:
    m, sd, _ = got[p["n"]]
    print("%s\t%+.4f\t%.4f" % (p["n"], m, sd))

print("incoming_title Brian ...", flush=True)
brian = sim.our_roster(BRIAN)
inc = sim.incoming_title(full, brian)
print("BRIAN_INCOMING")
for p in brian:
    m, sd, _ = inc[p["n"]]
    print("%s\t%+.4f\t%.4f" % (p["n"], m, sd))

print("roster P(title) ...", flush=True)
odds = sim.full_season()[sim.ROSTER]
print("P_TITLE\t%.4f" % odds.title)
print("PF\t%.0f" % odds.pf)
print("WINS\t%.1f" % odds.wins)
