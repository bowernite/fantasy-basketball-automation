import unittest
from tests.harness import *

class RosterScopedReports(unittest.TestCase):
    def test_an_our_roster_report_refuses_a_counterparty_file(self):
        for name in sorted(sim.OURS_ONLY):
            with self.subTest(report=name):
                p = sim_process("--roster", THEIR_ROSTER, name)
                self.assertNotEqual(p.returncode, 0)
                for served in set(sim.REPORTS) - sim.OURS_ONLY:
                    self.assertIn(served, p.stdout + p.stderr)

    def test_the_roster_free_report_measures_the_same_thing_for_every_team(self):
        for name in sorted(sim.ROSTER_FREE):
            with self.subTest(report=name):
                self.assertEqual(render(name), render(name, THEIR_ROSTER))

    def test_a_roster_the_labels_do_not_carry_is_headed_by_its_own_filename(self):
        self.assertEqual(roster_mod.label("roster-999999-%s.json"
                                          % fetch_data.SEASON_TAG),
                         "roster-999999-%s.json" % fetch_data.SEASON_TAG)

    def test_naming_no_report_at_all_refuses_the_one_it_falls_back_to(self):
        p = sim_process("--roster", THEIR_ROSTER)
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("CALIBRATION", p.stdout)
        self.assertIn("calibration", p.stdout + p.stderr)

    def test_a_served_report_runs_on_a_counterparty_from_the_shell(self):
        p = sim_process("--roster", THEIR_ROSTER, "nights")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(THEIR_ROSTER, p.stdout)
        self.assertIn("NIGHTS", p.stdout)

    def test_the_flag_joined_to_its_file_by_an_equals_sign_still_loads_it(self):
        p = sim_process("--roster=%s" % THEIR_ROSTER, "nights")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(THEIR_ROSTER, p.stdout)
        self.assertIn("NIGHTS", p.stdout)

    def test_the_flag_with_nothing_after_the_equals_sign_says_what_it_wanted(self):
        p = sim_process("--roster=", "nights")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("--roster", p.stdout + p.stderr)

    def test_a_roster_file_that_is_not_there_is_refused_before_any_table(self):
        p = sim_process("--roster", "no-such-team.json", "players")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertNotIn("wins lost if swapped", p.stdout)
        self.assertIn("no-such-team.json", p.stdout + p.stderr)

    def test_the_readme_names_the_reports_the_flag_actually_refuses(self):
        text = one_line(read_text(os.path.join(sim.HERE, "README.md")))
        refused = re.search(r"serves every report but ((?:\*\*)?(?:`\w+` ?)+)",
                            text)
        self.assertIsNotNone(refused, "the README stopped naming them")
        self.assertEqual(set(re.findall(r"`(\w+)`", refused.group(1))),
                         sim.OURS_ONLY)

    def test_the_module_docstring_names_the_reports_the_flag_refuses(self):
        text = one_line(sim.__doc__)
        refused = re.search(r"refuse it: ([^.]+)\.", text)
        self.assertIsNotNone(refused, "the docstring stopped naming them")
        self.assertEqual(set(re.findall(r"\w+", refused.group(1))), sim.OURS_ONLY)

    def test_no_skill_carries_its_own_copy_of_the_report_list(self):
        for path in glob.glob(skills_path("*", "*.md")):
            with self.subTest(skill=os.path.basename(os.path.dirname(path))):
                text = one_line(read_text(path))
                named = [n for n in sim.OURS_ONLY if "`%s`" % n in text]
                self.assertLess(len(named), len(sim.OURS_ONLY), named)

    def test_every_report_the_skills_and_pages_cite_is_a_real_one(self):
        pages = [os.path.join(sim.HERE, n) for n in
                 ("README.md", "method.md", "findings.md")]
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
        p = sim_process("--roster")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("Traceback", p.stderr)
        self.assertIn("--roster", p.stdout + p.stderr)

    def test_the_positions_premium_is_explained_by_the_loaded_roster(self):
        out = render("positions", THEIR_ROSTER)
        pure_g = sum(1 for q in sim.basis(THEIR_ROSTER)
                     if set(q["elig"]) <= {"PG", "SG"})
        self.assertIn("%d pure PG/SG" % pure_g, out)

    def test_the_light_night_premise_is_the_loaded_rosters_own(self):
        flat = one_line(render("schedules", THEIR_ROSTER))
        full = sim.basis(THEIR_ROSTER)
        n_fa = len(sim.auction_slots(full))
        moved_a, moved_b = (sim.steer(full, ["BKN"] * n_fa),
                            sim.steer(full, ["CHI"] * n_fa))
        kept = [p["tm"] for p, x, y in zip(full, moved_a, moved_b)
                if p["tm"] == x["tm"] == y["tm"]]
        self.assertIn("the other %d stay where they are on %d NBA teams, and %d "
                      "of the %d light nights are already reached"
                      % (len(kept),
                         sum(1 for t in set(kept) if not sim.unsigned(t)),
                         sim.coverage(kept), len(sim.light_nights())), flat)

    def test_the_group_r_note_agrees_with_the_table_it_explains(self):
        out = render("replacement", THEIR_ROSTER)
        R = {lab: float(re.search(r"^ +%s +([\d.]+)" % lab, out, re.M).group(1))
             for lab in ("guard", "forward", "center")}
        note = re.search(r"guard ([-+]\d+\.\d), center ([-+]\d+\.\d)", out)
        self.assertIsNotNone(note, out)
        self.assertAlmostEqual(float(note.group(1)),
                               R["guard"] - R["forward"], delta=0.11)
        self.assertAlmostEqual(float(note.group(2)),
                               R["center"] - R["forward"], delta=0.11)
        padded = sim.basis(THEIR_ROSTER)
        for g, elig in sim.GROUPS.items():
            with self.subTest(group=g):
                self.assertIn("%s %d/%d" % (g, sim.pure_bodies(padded, elig),
                                            sim.group_slots(elig)), out)
        top = re.search(r"highest R (\w+)", out)
        self.assertIsNotNone(top, out)
        self.assertEqual(top.group(1), max(R, key=R.get), out)
        crowd = {g: sim.pure_bodies(padded, e) / sim.group_slots(e)
                 for g, e in sim.GROUPS.items()}
        byR = sorted(R, key=lambda g: -R[g])
        orders = all(crowd[a] > crowd[b] for a, b in zip(byR, byR[1:]))
        self.assertIn("crowding %s the three"
                      % ("orders" if orders else "does NOT order"), out)
