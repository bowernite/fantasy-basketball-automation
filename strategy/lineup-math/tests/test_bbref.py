import unittest
from tests.harness import *

CAREER = "player,player_id,pos,ht_in_in,wt,birth_date,colleges,from,to,debut,hof\n"
ADVANCED = ("season,lg,player,player_id,age,team,pos,g,gs,mp,per,ts_percent,"
            "x3p_ar,f_tr,orb_percent,drb_percent,trb_percent,ast_percent,"
            "stl_percent,blk_percent,tov_percent,usg_percent,ows,dws,ws,ws_48,"
            "obpm,dbpm,bpm,vorp\n")
DRAFT = "season,lg,overall_pick,round,tm,player,player_id,college\n"


def adv(season, name, pid, team, g, bpm):
    return ("%d,NBA,%s,%s,25,%s,G,%d,0,1000,15,0.55,0.3,0.2,3,12,8,20,1.5,1,"
            "12,20,1,1,2,0.1,0,0,%s,0.5\n" % (season, name, pid, team, g, bpm))


def mirror(career, advanced, draft):
    d = tempfile.mkdtemp()
    for name, head, rows in (("Player Career Info.csv", CAREER, career),
                             ("Advanced.csv", ADVANCED, advanced),
                             ("Draft Pick History.csv", DRAFT, draft)):
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(head + "".join(rows))
    return d


class BBRefJoin(unittest.TestCase):
    def test_a_name_two_players_share_joins_on_the_birthday(self):
        d = mirror(
            ["Jaren Jackson,jacksja01,F,80,220,1967-10-27,Georgetown,1990,2003,x,FALSE\n",
             "Jaren Jackson Jr.,jacksja02,F,83,242,1999-09-15,Michigan State,2019,2026,x,FALSE\n"],
            [adv(2026, "Jaren Jackson Jr.", "jacksja02", "MEM", 60, 2.0)],
            ["2018,NBA,4,1,MEM,Jaren Jackson Jr.,jacksja02,Michigan State\n"])
        out = fetch_data.bbref_players(d, {"Jaren Jackson Jr.": {"born": "1999-09-15"}})
        self.assertEqual(out["Jaren Jackson Jr."]["bbref"], "jacksja02")
        self.assertEqual(out["Jaren Jackson Jr."]["pick"], 4)

    def test_bpm_is_the_games_weighted_mean_of_the_last_two_seasons_played(self):
        d = mirror(
            ["Tyrese Haliburton,halibty01,G,77,185,2000-02-29,Iowa State,2021,2025,x,FALSE\n"],
            [adv(2023, "Tyrese Haliburton", "halibty01", "IND", 56, 9.0),
             adv(2024, "Tyrese Haliburton", "halibty01", "IND", 69, 5.0),
             adv(2025, "Tyrese Haliburton", "halibty01", "IND", 73, 6.0)],
            [])
        p = fetch_data.bbref_players(d, {"Tyrese Haliburton": {"born": "2000-02-29"}})
        self.assertAlmostEqual(p["Tyrese Haliburton"]["bpm"],
                               (69 * 5.0 + 73 * 6.0) / (69 + 73), places=3)
        self.assertEqual(p["Tyrese Haliburton"]["bpm_g"], 69 + 73)

    def test_a_traded_players_season_is_his_combined_row(self):
        d = mirror(
            ["Dennis Schroder,schrode01,G,73,172,1993-09-15,,2014,2026,x,FALSE\n"],
            [adv(2026, "Dennis Schroder", "schrode01", "SAC", 20, -5.0),
             adv(2026, "Dennis Schroder", "schrode01", "2TM", 70, -1.0),
             adv(2026, "Dennis Schroder", "schrode01", "BOS", 50, 0.6)],
            [])
        p = fetch_data.bbref_players(d, {"Dennis Schröder": {"born": "1993-09-15"}})
        self.assertAlmostEqual(p["Dennis Schröder"]["bpm"], -1.0)

    def test_career_year_counts_seasons_since_debut_and_undrafted_has_no_pick(self):
        d = mirror(
            ["AJ Green,greenaj01,G,76,190,1999-09-26,Northern Iowa,2023,2026,x,FALSE\n"],
            [adv(2026, "AJ Green", "greenaj01", "MIL", 78, 0.5)], [])
        p = fetch_data.bbref_players(d, {"AJ Green": {"born": "1999-09-26"}})
        self.assertEqual(p["AJ Green"]["debut"], 2022)
        self.assertIsNone(p["AJ Green"]["pick"])

    def test_a_spelling_no_normalisation_folds_still_joins_on_birthday_and_surname(self):
        d = mirror(
            ["Egor Dёmin,demineg01,G,80,200,2006-03-03,BYU,2026,2026,x,FALSE\n",
             "Ron Holland,hollaro01,F,80,200,2005-07-07,,2025,2026,x,FALSE\n"],
            [adv(2026, "Egor Dёmin", "demineg01", "BRK", 60, -2.0)],
            ["2025,NBA,8,1,BRK,Egor Dёmin,demineg01,BYU\n"])
        p = fetch_data.bbref_players(d, {"Egor Demin": {"born": "2006-03-04"},
                                         "Ronald Holland II": {"born": "2005-07-07"}})
        self.assertEqual(p["Egor Demin"]["bbref"], "demineg01")
        self.assertEqual(p["Ronald Holland II"]["bbref"], "hollaro01")

    def test_a_name_only_one_player_carries_joins_through_a_birthday_the_sources_disagree_on(self):
        d = mirror(["Jay Huff,huffja01,C-F,85,240,1998-08-25,Virginia,2022,2026,x,FALSE\n"],
                   [], [])
        p = fetch_data.bbref_players(d, {"Jay Huff": {"born": "1997-08-24"}})
        self.assertEqual(p["Jay Huff"]["bbref"], "huffja01")

    def test_a_pool_player_the_mirror_lacks_is_left_out_rather_than_guessed(self):
        d = mirror(["AJ Green,greenaj01,G,76,190,1999-09-26,,2023,2026,x,FALSE\n"], [], [])
        p = fetch_data.bbref_players(d, {"Thomas Sorber": {"born": "2005-12-25"}})
        self.assertNotIn("Thomas Sorber", p)
