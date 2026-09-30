import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, afterEach, beforeAll, expect, setSystemTime, test } from "bun:test";
import type { Player } from "../types";
import { getPlayerPredictedScore } from "./score-weighting";

beforeAll(() => GlobalRegistrator.register());
afterAll(() => GlobalRegistrator.unregister());
afterEach(() => setSystemTime());

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

function scoreWithWarnings(player: Player) {
  setSystemTime(new Date(2026, 0, 15, 12, 0, 0));
  document.body.innerHTML = `<a class="btn" data-toggle="dropdown">Today</a>`;
  const warnings: string[] = [];
  const originalWarn = console.warn;
  console.warn = (...args) => warnings.push(args.join(" "));
  try {
    getPlayerPredictedScore(player);
  } finally {
    console.warn = originalWarn;
  }
  return warnings;
}

test("an early-season player with no projection is scored with the default rate and a warning names him", () => {
  const warnings = scoreWithWarnings(makePlayer({ gamesPlayed: 0 }));

  expect(warnings).toMatchInlineSnapshot(`
    [
      "No projection for Unprojected Player; scoring with the default 6/game",
    ]
  `);
});

test("a player with enough games played to ignore projections gets no missing-projection warning", () => {
  const warnings = scoreWithWarnings(makePlayer({ gamesPlayed: 20 }));

  expect(warnings).toEqual([]);
});

test("a projected early-season player gets no warning", () => {
  const warnings = scoreWithWarnings(
    makePlayer({ playerName: "Nikola Jokić", gamesPlayed: 0 })
  );

  expect(warnings).toEqual([]);
});
