"""Joint sim screen: Brian trade feelers."""
import sim

BRIAN = "roster-161018-2025-26.json"

DEALS = [
    # label, out_us, in_from_brian, out_brian, in_from_us
    # Brian-side 2-for-1s include Sochan as the implied cut to fit the cap.
    ("Murphy for Bane", ["Desmond Bane"], ["Trey Murphy"], ["Trey Murphy"], ["Desmond Bane"]),
    ("Herro for Bane", ["Desmond Bane"], ["Tyler Herro"], ["Tyler Herro"], ["Desmond Bane"]),
    ("Grant for Simons+Matkovic", ["Anfernee Simons", "Karlo Matković"], ["Jerami Grant"],
     ["Jerami Grant", "Jeremy Sochan"], ["Anfernee Simons", "Karlo Matković"]),
    ("Garland for Murphy", ["Darius Garland"], ["Trey Murphy"], ["Trey Murphy"], ["Darius Garland"]),
    ("Murphy for Bane+Matkovic", ["Desmond Bane", "Karlo Matković"], ["Trey Murphy"],
     ["Trey Murphy", "Jeremy Sochan"], ["Desmond Bane", "Karlo Matković"]),
    ("Murphy for Coby White", ["Coby White"], ["Trey Murphy"], ["Trey Murphy"], ["Coby White"]),
    ("Nurk for Melton+Bona", ["De'Anthony Melton", "Adem Bona"], ["Jusuf Nurkić"],
     ["Jusuf Nurkić", "Jeremy Sochan"], ["De'Anthony Melton", "Adem Bona"]),
    ("Grant for Matkovic", ["Karlo Matković"], ["Jerami Grant"], ["Jerami Grant"], ["Karlo Matković"]),
    ("Butler for Randle", ["Jimmy Butler"], ["Julius Randle"], ["Julius Randle"], ["Jimmy Butler"]),
    ("Zion for Edey+Simons", ["Zach Edey", "Anfernee Simons"], ["Zion Williamson"],
     ["Zion Williamson", "Jeremy Sochan"], ["Zach Edey", "Anfernee Simons"]),
    ("Murphy for Bane+Simons", ["Desmond Bane", "Anfernee Simons"], ["Trey Murphy"],
     ["Trey Murphy", "Jeremy Sochan"], ["Desmond Bane", "Anfernee Simons"]),
    ("Pritchard for Suggs", ["Jalen Suggs"], ["Payton Pritchard"],
     ["Payton Pritchard"], ["Jalen Suggs"]),
    ("Herro for Butler", ["Jimmy Butler"], ["Tyler Herro"], ["Tyler Herro"], ["Jimmy Butler"]),
    ("Murphy for White+Matkovic", ["Coby White", "Karlo Matković"], ["Trey Murphy"],
     ["Trey Murphy", "Jeremy Sochan"], ["Coby White", "Karlo Matković"]),
    ("Nurk for Matkovic", ["Karlo Matković"], ["Jusuf Nurkić"], ["Jusuf Nurkić"], ["Karlo Matković"]),
    ("Murphy for Bane+Melton", ["Desmond Bane", "De'Anthony Melton"], ["Trey Murphy"],
     ["Trey Murphy", "Jeremy Sochan"], ["Desmond Bane", "De'Anthony Melton"]),
]


def bodies(names, roster):
    by = {p["n"]: p for p in roster}
    missing = [n for n in names if n not in by]
    if missing:
        raise KeyError("missing on roster: %s" % ", ".join(missing))
    return [by[n] for n in names]


def side(full, out_names, in_names, from_roster, path=None):
    after = sim.swap(full, out_names, bodies(in_names, from_roster))
    base = sim.run(full, cal=sim.DELTA_W_CAL)
    deal = sim.run(after, cal=sim.DELTA_W_CAL)
    dw = sim.wins(deal, base)
    dtitle = sim.roster_title(after, full, path=path)[0]
    return dw, dtitle


def main():
    ours = sim.basis()
    theirs = sim.basis(BRIAN)
    our_proj = sim.our_roster()
    their_proj = sim.our_roster(BRIAN)

    print("label\tΔw us\tΔP(title) us\tΔw Brian\tΔP(title) Brian")
    for label, out_us, in_from_brian, out_them, in_from_us in DEALS:
        try:
            dw_us, dt_us = side(ours, out_us, in_from_brian, their_proj)
            dw_them, dt_them = side(theirs, out_them, in_from_us, our_proj, path=BRIAN)
        except (KeyError, ValueError) as e:
            print("%s\tERROR\t%s" % (label, e))
            continue
        print("%s\t%+.2f\t%+.1f%%\t%+.2f\t%+.1f%%" % (
            label, dw_us, dt_us * 100, dw_them, dt_them * 100))


if __name__ == "__main__":
    main()
