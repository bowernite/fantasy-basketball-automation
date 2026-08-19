import unittest
from tests.harness import *

class RosterScopedReports(unittest.TestCase):
    """Half the reports are built on OUR player names, `scenarios` trading
    Suggs and `durability` re-shaping him. Pointed at another team's file those
    names match nobody, so the report prints a full table of numbers answering
    nothing, and `--roster` is advertised for any team"""

    def test_an_our_roster_report_refuses_a_counterparty_file(self):
        """It has to name the ones it DOES serve. A bare refusal on the report
        a Skill just told you to run reads as "--roster is broken", and the 9
        that work are the whole counterparty workflow"""
        for name in sorted(sim.OURS_ONLY):
            with self.subTest(report=name):
                p = sim_process("--roster", THEIR_ROSTER, name)
                self.assertNotEqual(p.returncode, 0)
                for served in set(sim.REPORTS) - sim.OURS_ONLY:
                    self.assertIn(served, p.stdout + p.stderr)

    def test_the_roster_free_report_measures_the_same_thing_for_every_team(self):
        """Its header says it read no roster, which is a claim about the table
        under it: if `market` ever starts reading one, the header is the last
        place that shows, and a board table gets quoted as a team's"""
        for name in sorted(sim.ROSTER_FREE):
            with self.subTest(report=name):
                self.assertEqual(render(name), render(name, THEIR_ROSTER))

    def test_a_roster_the_labels_do_not_carry_is_headed_by_its_own_filename(self):
        """`--roster` takes any path, and the id -> name map only covers the
        twelve. A header that insisted on a name would take out every report in
        the run, including on a tree cut before the map existed"""
        self.assertEqual(roster_mod.label("roster-999999-%s.json"
                                          % fetch_data.SEASON_TAG),
                         "roster-999999-%s.json" % fetch_data.SEASON_TAG)

    def test_naming_no_report_at_all_refuses_the_one_it_falls_back_to(self):
        """`calibration` is the default, so a default applied AFTER the refusal
        hands you the exact report the refusal names, their simulated PF over
        OUR real standings PF, exit 0, under a header naming their file"""
        p = sim_process("--roster", THEIR_ROSTER)
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("CALIBRATION", p.stdout)
        self.assertIn("calibration", p.stdout + p.stderr)

    def test_a_served_report_runs_on_a_counterparty_from_the_shell(self):
        """Every other run of a SERVED report is in-process with the sample
        size shrunk, so this is the only thing showing the command as it is
        actually typed, real interpreter, real argv, exit 0, a table. The
        refusals all exit before loading anything"""
        p = sim_process("--roster", THEIR_ROSTER, "nights")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(THEIR_ROSTER, p.stdout)
        self.assertIn("NIGHTS", p.stdout)

    def test_the_flag_joined_to_its_file_by_an_equals_sign_still_loads_it(self):
        """`--roster=theirs.json` is the other half of how the flag gets typed.
        A parse matching only the bare word sends the whole token through to
        the report check, which comes back complaining about a report name, on
        a flag spelled correctly"""
        p = sim_process("--roster=%s" % THEIR_ROSTER, "nights")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(THEIR_ROSTER, p.stdout)
        self.assertIn("NIGHTS", p.stdout)

    def test_the_flag_with_nothing_after_the_equals_sign_says_what_it_wanted(self):
        """`--roster=` is one keystroke from `--roster=theirs.json`, and an
        arity guard that only counts argv is satisfied by the empty half, then
        loads the DIRECTORY the files sit in under a header saying it had a
        roster"""
        p = sim_process("--roster=", "nights")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("--roster", p.stdout + p.stderr)

    def test_a_roster_file_that_is_not_there_is_refused_before_any_table(self):
        """The commonest way to mistype this flag is a wrong path, and left as
        a traceback it comes after the roster banner and the report's own
        header, so the run reads as started. `_load` also joins against the
        DATA directory rather than the shell's cwd, so a path that exists where
        you typed it still has to be named back to you"""
        p = sim_process("--roster", "no-such-team.json", "players")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertNotIn("wins lost if swapped", p.stdout)
        self.assertIn("no-such-team.json", p.stdout + p.stderr)

    def test_the_readme_names_the_reports_the_flag_actually_refuses(self):
        """The counterparty workflow is followed out of the README, not out of
        `REPORTS`, and the refusal message above is only checked against
        whatever `OURS_ONLY` happens to hold. Move a report between the two
        sets and both stay green while the page sends the reader to run
        something that exits 1"""
        text = one_line(read_text(os.path.join(sim.HERE, "README.md")))
        refused = re.search(r"serves every report but ((?:\*\*)?(?:`\w+` ?)+)",
                            text)
        self.assertIsNotNone(refused, "the README stopped naming them")
        self.assertEqual(set(re.findall(r"`(\w+)`", refused.group(1))),
                         sim.OURS_ONLY)

    def test_the_module_docstring_names_the_reports_the_flag_refuses(self):
        """`sim.py`'s own docstring is the first thing anyone opening the file
        reads. A reader who believes it serves every report runs one of the
        four it refuses, gets exit 1, and reads the flag as broken rather than
        the sentence"""
        text = one_line(sim.__doc__)
        refused = re.search(r"refuse it: ([^.]+)\.", text)
        self.assertIsNotNone(refused, "the docstring stopped naming them")
        self.assertEqual(set(re.findall(r"\w+", refused.group(1))), sim.OURS_ONLY)

    def test_no_skill_carries_its_own_copy_of_the_report_list(self):
        """`trades` used to name the four reports `--roster` refuses. That list
        is `sim.py --help`'s to state -- a second copy in a file the command
        does not read is a copy that goes stale silently, and the skill is what
        gets loaded before a deal is priced"""
        for path in glob.glob(skills_path("*", "*.md")):
            with self.subTest(skill=os.path.basename(os.path.dirname(path))):
                text = one_line(read_text(path))
                named = [n for n in sim.OURS_ONLY if "`%s`" % n in text]
                self.assertLess(len(named), len(sim.OURS_ONLY), named)

    def test_every_report_the_skills_and_pages_cite_is_a_real_one(self):
        """`Eval Definitions`, `eval-team`, `eval-player` and `trades` all send
        a reader to a named `sim.py` run. A citation to a report the registry
        does not carry exits 1 on the command a skill just mandated"""
        pages = [os.path.join(sim.HERE, n) for n in
                 ("README.md", "method.md", "findings.md", "tldr.md")]
        pages += glob.glob(skills_path("*", "*.md"))
        pages += glob.glob(os.path.join(sim.HERE, os.pardir, "*.md"))
        cited = collections.Counter()
        for path in pages:
            for name in re.findall(r"sim\.py ([a-z]\w*)", read_text(path)):
                cited[name] += 1
                with self.subTest(page=os.path.basename(path), report=name):
                    self.assertIn(name, sim.REPORTS)
        self.assertIn("playoffs", cited)

    def test_roster_with_no_file_after_it_says_what_it_wanted(self):
        """Every other CLI error here exits with a written explanation. A
        traceback on the flag a Skill was just told to pass reads as a broken
        flag rather than as a command missing its argument"""
        p = sim_process("--roster")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("--roster", p.stdout + p.stderr)

    def test_the_positions_premium_is_explained_by_the_loaded_roster(self):
        """A pure-guard count typed into the `positions` header describes
        whatever roster produced the table. It has to come off the roster the
        bodies were ADDED to, the padded 38, not the live file, which is 4
        guards short of it here"""
        out = render("positions", THEIR_ROSTER)
        pure_g = sum(1 for q in sim.basis(THEIR_ROSTER)
                     if set(q["elig"]) <= {"PG", "SG"})
        self.assertIn("%d pure PG/SG" % pure_g, out)

    def test_the_light_night_premise_is_the_loaded_rosters_own(self):
        """What steering the auction buys is entirely a function of which light
        nights the OTHER 31 bodies already reach. Ours reach 31 of the 32,
        which is why the headline sits at the 0.1-win floor at all, so a report
        quoting our spread while pricing his auction hands a counterparty our
        ceiling and every table under it still prints"""
        flat = one_line(render("schedules", THEIR_ROSTER))
        full = sim.basis(THEIR_ROSTER)
        moved_a, moved_b = sim.steer(full, ["BKN"] * 7), sim.steer(full, ["CHI"] * 7)
        kept = [p["tm"] for p, x, y in zip(full, moved_a, moved_b)
                if p["tm"] == x["tm"] == y["tm"]]
        self.assertIn("the other %d stay where they are, and %d of the %d "
                      "light nights are already reached"
                      % (len(kept), sim.coverage(kept), len(sim.light_nights())),
                      flat)
        self.assertIn("spread of %d NBA teams"
                      % sum(1 for t in set(kept) if not sim.unsigned(t)), flat)

    def test_the_group_r_note_agrees_with_the_table_it_explains(self):
        """A report served for any team cannot explain its numbers with OUR
        roster's shape. Against a counterparty whose guard R is BELOW his
        forward R, a fixed guard sentence offers a body count as proof of the
        opposite of what the numbers say.

        Two things have to hold. The counts come off the roster R was FITTED
        on, the padded 38 rather than the live file, which is a different shape
        and 4-8 bodies short per group. And crowding is offered as an
        explanation only where it actually orders the three R's, since on our
        own padded roster guards and centers are equally crowded while center R
        is the higher"""
        out = render("replacement", THEIR_ROSTER)
        R = {lab: float(re.search(r"^ +%s +([\d.]+)" % lab, out, re.M).group(1))
             for lab in ("guard", "forward", "center")}
        note = re.search(r"guard ([-+]\d+\.\d), center ([-+]\d+\.\d)", out)
        self.assertIsNotNone(note, out)
        # The note is a 1-dp difference; `R` is the difference of two 1-dp
        # table cells. Each cell is up to 0.05 off, so 0.1 is the bound and it
        # has to be INCLUSIVE -- a gap of exactly 0.1 is a float 0.10000000009
        self.assertAlmostEqual(float(note.group(1)),
                               R["guard"] - R["forward"], delta=0.11)
        self.assertAlmostEqual(float(note.group(2)),
                               R["center"] - R["forward"], delta=0.11)
        padded = sim.basis(THEIR_ROSTER)
        for g, elig in sim.GROUPS.items():
            with self.subTest(group=g):
                self.assertIn("%s %d/%d" % (g, sim.pure_bodies(padded, elig),
                                            sim.group_slots(elig)), out)
        top = re.search(r"[Hh]ighest R is (\w+)", out)
        self.assertIsNotNone(top, out)
        self.assertEqual(top.group(1), max(R, key=R.get), out)
        crowd = {g: sim.pure_bodies(padded, e) / sim.group_slots(e)
                 for g, e in sim.GROUPS.items()}
        byR = sorted(R, key=lambda g: -R[g])
        orders = all(crowd[a] > crowd[b] for a, b in zip(byR, byR[1:]))
        self.assertIn("rowding %s the three here"
                      % ("orders" if orders else "does NOT order"), out)
