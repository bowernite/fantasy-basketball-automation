import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, afterEach, beforeAll, expect, setSystemTime, test } from "bun:test";
import { givePlayerNews, loadLineupPage, PAGE_URL } from "../lineup/fixtures/lineup-page";
import { getPlayerPredictedScore } from "../prioritization/score-weighting";
import { getPlayers } from "./get-players";

beforeAll(() =>
  GlobalRegistrator.register({
    url: PAGE_URL,
    settings: { disableJavaScriptFileLoading: true, disableCSSFileLoading: true, handleDisabledFileLoadingAsSuccess: true },
  }),
);
afterAll(() => GlobalRegistrator.unregister());
afterEach(() => setSystemTime());

// On the saved page, Shaedon Sharpe's recent average shows "15.5↓" (an under-performing arrow)
test("a recent average shown with a trend arrow is read as its number", async () => {
  loadLineupPage();

  const players = await getPlayers();

  expect(players.find((p) => p.playerName === "Shaedon Sharpe")?.last5Avg).toBe(15.5);
});

// On the saved page, Zach Edey is still tagged "Out for season" (last season's injury), but his latest
// news (9/30) says he's been cleared to be a full go for the new season
test("a player tagged out for the season whose latest news clears him isn't scored as out", async () => {
  setSystemTime(new Date("2026-10-20T14:00:00Z"));
  loadLineupPage();

  const players = await getPlayers();
  const edey = players.find((p) => p.playerName === "Zach Edey")!;

  expect(edey.playerStatus).toBe("OFS");
  expect(getPlayerPredictedScore(edey)[0]).toBeGreaterThan(0);
});

// Fleaflicker renders news times in the account's timezone; the datetime attribute is always UTC
test("a news item's age comes from its UTC timestamp, whatever timezone the page renders it in", async () => {
  setSystemTime(new Date("2026-10-20T14:00:00Z"));
  loadLineupPage();
  givePlayerNews(
    "Adem Bona",
    '<div class="news-text"><h5>Adem Bona Probable Tuesday</h5>' +
      '<em><relative-time datetime="2026-10-20T12:00:00Z">Tue 10/20/26 5:00 AM</relative-time></em>' +
      "<p>Philadelphia 76ers center Adem Bona (knee) is probable for Tuesday's game against the Knicks.</p></div>",
  );

  const players = await getPlayers();

  expect(players.find((p) => p.playerName === "Adem Bona")?.refinedPlayerStatus).toEqual({ injuryStatus: "P", timeAgo: { value: 2, unit: "hours" } });
});
