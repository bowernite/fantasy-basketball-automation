import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, afterEach, beforeAll, expect, setSystemTime, test } from "bun:test";
import { NO_PROJECTION_RATE, PLAYER_DATA } from "../data/player-data";
import type { Player, PlayerStatus, TimeAgo } from "../types";
import { prioritizePlayers } from "./prioritization";
import { getPlayerPredictedScore } from "./score-weighting";

beforeAll(() => GlobalRegistrator.register());
afterAll(() => GlobalRegistrator.unregister());
afterEach(() => setSystemTime());

const MID_SEASON_NOON = new Date(2026, 0, 15, 12, 0, 0);
const OFFSEASON_NOON = new Date(2026, 8, 30, 12, 0, 0);

/** Renders the lineup page's date dropdown, e.g. "Today" or "1/18" */
function setup({ now = MID_SEASON_NOON, viewedDay = "Today" } = {}) {
  setSystemTime(now);
  document.body.innerHTML = `<a class="btn" data-toggle="dropdown">${viewedDay}</a>`;
}

function makePlayer(overrides: Partial<Player> = {}): Player {
  return {
    playerName: "Unprojected Player",
    playerStatus: "(active)",
    refinedPlayerStatus: undefined,
    last5Avg: 30,
    last10Avg: 30,
    seasonAvg: 30,
    seasonTotal: 600,
    gamesPlayed: 20,
    todaysGame: "BOS",
    position: "PG",
    setPositionDropdown: null,
    isTaxi: false,
    isIr: false,
    opponentInfo: undefined,
    row: document.createElement("tr"),
    ...overrides,
  };
}

function withInjury(status: PlayerStatus, timeAgo: TimeAgo | undefined) {
  return makePlayer({
    playerStatus: status,
    refinedPlayerStatus: { injuryStatus: status, timeAgo },
  });
}

function score(player: Player) {
  return getPlayerPredictedScore(player)[0];
}

test("before any games are played, a player is scored at their projection", () => {
  setup();
  const noStats = { gamesPlayed: 0, last5Avg: null, last10Avg: null, seasonAvg: null };

  expect(score(makePlayer({ ...noStats, playerName: "Nikola Jokić" }))).toBeCloseTo(
    PLAYER_DATA["Nikola Jokić"].projectedSeasonAvg
  );
  expect(score(makePlayer({ ...noStats, playerName: "Unknown Rookie" }))).toBeCloseTo(
    NO_PROJECTION_RATE
  );
});

test("a veteran sample of games is scored on production alone, not the projection", () => {
  setup();

  expect(score(makePlayer({ playerName: "Nikola Jokić", gamesPlayed: 40 }))).toBeCloseTo(30);
  expect(score(makePlayer({ playerName: "Unknown Rookie", gamesPlayed: 40 }))).toBeCloseTo(30);
});

test("a few games in, the score sits between projection and production", () => {
  setup();
  const projection = PLAYER_DATA["Nikola Jokić"].projectedSeasonAvg;

  const s = score(makePlayer({ playerName: "Nikola Jokić", gamesPlayed: 6 }));

  expect(s).toBeGreaterThan(30);
  expect(s).toBeLessThan(projection);
});

test("recent form counts more than season average", () => {
  setup();

  const slumping = score(makePlayer({ seasonAvg: 40, last10Avg: 20, last5Avg: 20 }));
  const surging = score(makePlayer({ seasonAvg: 20, last10Avg: 40, last5Avg: 40 }));

  expect(surging).toBeGreaterThan(slumping);
});

test("a player with only a season average is scored from it alone", () => {
  setup();

  expect(score(makePlayer({ seasonAvg: 25, last10Avg: null, last5Avg: null }))).toBeCloseTo(25);
});

test("a weak opposing defense raises the score and a strong one lowers it", () => {
  setup();
  const vs = (defenseRank: number) =>
    makePlayer({ opponentInfo: { avgPointsAllowed: 0, avgPointsAllowedRank: defenseRank, defenseRank } });

  const noOpponentInfo = score(makePlayer());

  expect(score(vs(30))).toBeGreaterThan(noOpponentInfo);
  expect(score(vs(1))).toBeLessThan(noOpponentInfo);
  expect(score(vs(1))).toBeGreaterThan(0);
});

test("for today's games, fresher and more serious injury statuses score lower", () => {
  setup();
  const reportedThisMorning: TimeAgo = { value: 3, unit: "hours" };

  const healthy = score(makePlayer());
  const probable = score(withInjury("P", reportedThisMorning));
  const questionable = score(withInjury("Q", reportedThisMorning));
  const dayToDay = score(withInjury("DTD", reportedThisMorning));
  const doubtful = score(withInjury("D", reportedThisMorning));
  const out = score(withInjury("OUT", reportedThisMorning));
  const outForSeason = score(withInjury("OFS", { value: 20, unit: "days" }));

  expect(probable).toBeLessThan(healthy);
  expect(questionable).toBeLessThan(probable);
  expect(dayToDay).toBe(questionable);
  expect(doubtful).toBeLessThan(questionable);
  expect(doubtful).toBeGreaterThan(0);
  expect(out).toBe(0);
  expect(outForSeason).toBe(0);
});

test("an OUT status with no news timestamp zeroes the player for today", () => {
  setup();

  expect(score(makePlayer({ playerStatus: "OUT" }))).toBe(0);
});

test("a questionable tag doesn't discount a game several days out", () => {
  setup({ viewedDay: "1/19" });

  const healthy = score(makePlayer());
  const questionable = score(withInjury("Q", { value: 30, unit: "minutes" }));

  expect(questionable).toBe(healthy);
});

test("a player ruled OUT today is discounted but not zeroed for a game days out", () => {
  setup({ viewedDay: "1/17" });

  const healthy = score(makePlayer());
  const out = score(withInjury("OUT", { value: 2, unit: "hours" }));

  expect(out).toBeGreaterThan(0);
  expect(out).toBeLessThan(healthy);
});

test("a player still listed OUT today scores far below a healthy one, even if the injury news is old", () => {
  setup();

  const healthy = score(makePlayer());
  const outForAWeek = score(withInjury("OUT", { value: 7, unit: "days" }));

  expect(outForAWeek).toBeLessThan(healthy / 2);
});

test("a player still tagged OUT isn't cleared by old news of a lesser status, but is by fresh news", () => {
  setup();
  const taggedOutWithNews = (injuryStatus: PlayerStatus, timeAgo: TimeAgo) =>
    makePlayer({ playerStatus: "OUT", refinedPlayerStatus: { injuryStatus, timeAgo } });

  const healthy = score(makePlayer());

  expect(score(taggedOutWithNews("P", { value: 5, unit: "days" }))).toBe(0);
  expect(score(taggedOutWithNews("P", { value: 2, unit: "hours" }))).toBeGreaterThan(healthy / 2);
});

test("players with a game today rank ahead of those without, then by predicted score", () => {
  setup();

  const ranked = prioritizePlayers([
    makePlayer({ playerName: "Star, no game", seasonAvg: 60, last10Avg: 60, last5Avg: 60, todaysGame: null }),
    makePlayer({ playerName: "Role player", seasonAvg: 15, last10Avg: 15, last5Avg: 15 }),
    makePlayer({ playerName: "Starter", seasonAvg: 35, last10Avg: 35, last5Avg: 35 }),
    makePlayer({ playerName: "Injured starter", playerStatus: "OUT" }),
    makePlayer({ playerName: "Bench, no game", seasonAvg: 10, last10Avg: 10, last5Avg: 10, todaysGame: "" }),
  ]);

  expect(ranked.map((r) => r.player.playerName)).toEqual([
    "Starter",
    "Role player",
    "Injured starter",
    "Star, no game",
    "Bench, no game",
  ]);
});

test("in the offseason, the displayed weighted score is the projection, not last season's stats", () => {
  const player = () => makePlayer({ playerName: "Bam Adebayo", seasonAvg: 20, last10Avg: 20, last5Avg: 20 });

  setup({ now: OFFSEASON_NOON });
  const [{ weightedScore: offseason }] = prioritizePlayers([player()]);
  setup({ now: MID_SEASON_NOON });
  const [{ weightedScore: inSeason }] = prioritizePlayers([player()]);

  expect(offseason).toBeCloseTo(PLAYER_DATA["Bam Adebayo"].projectedSeasonAvg);
  expect(inSeason).toBeCloseTo(20);
});
