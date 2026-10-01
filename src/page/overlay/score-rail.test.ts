import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, expect, test } from "bun:test";
import type { Player } from "../../types";
import { insertPlayerScores } from "./score-rail";

beforeAll(() => GlobalRegistrator.register());
afterAll(() => GlobalRegistrator.unregister());

function makePlayer(overrides: Partial<Player> = {}): Player {
  const row = document.createElement("tr");
  row.innerHTML = '<td><div class="player"><div class="player-name"><a class="player-text">Test Player</a></div></div></td>';
  return {
    playerName: "Test Player",
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
    row,
    ...overrides,
  };
}

type Adjustments = Parameters<typeof insertPlayerScores>[0]["debugInfo"];
const NO_ADJUSTMENTS: Adjustments = { injuryMultiplier: 1, opponentAdjustmentDiff: undefined, seasonProjectionAvg: 30, seasonProjectionWeight: 0 };

function render({
  player = makePlayer(),
  today = 30,
  season = 30 as number | null,
  debugInfo = {},
}: {
  player?: Player;
  today?: number;
  season?: number | null;
  debugInfo?: Partial<Adjustments>;
} = {}) {
  insertPlayerScores({ player, predictedScore: today, weightedScore: season, debugInfo: { ...NO_ADJUSTMENTS, ...debugInfo } });
  return player.row;
}

function barClasses(row: HTMLElement) {
  return row.querySelector(".ffx-rail__bar")!.className;
}

test("today's bar is banded sit under 20, fringe from 20, start from 30, star from 40", () => {
  const bandOf = (today: number) => barClasses(render({ today })).match(/ffx-rail__bar--(\w+)/)![1];

  expect([19.9, 20, 29.9, 30, 39.9, 40].map(bandOf)).toEqual(["sit", "fringe", "fringe", "start", "start", "star"]);
});

test("today's bar grows 2px per point and stops at 60 points with a cap notch", () => {
  const under = render({ today: 59.5 }).querySelector<HTMLElement>(".ffx-rail__bar")!;
  const over = render({ today: 72 }).querySelector<HTMLElement>(".ffx-rail__bar")!;

  expect(under.style.width).toBe("119px");
  expect(under.classList.contains("ffx-rail__bar--capped")).toBe(false);
  expect(over.style.width).toBe("120px");
  expect(over.classList.contains("ffx-rail__bar--capped")).toBe(true);
});

test("the season value is labeled above its tick, which sits 2px per point along the rail, also stopping at 60", () => {
  const row = render({ season: 47.6 });
  const capped = render({ season: 65 });

  expect(row.querySelector(".ffx-rail__tick")!.textContent).toBe("47.6");
  expect(row.querySelector(".ffx-rail")!.nextElementSibling!.className).toBe("ffx-popover");
  expect(row.querySelector<HTMLElement>(".ffx-rail__tick")!.style.left).toBe("95.2px");
  expect(capped.querySelector<HTMLElement>(".ffx-rail__tick")!.style.left).toBe("120px");
});

test("a player with no game today still gets the season tick on an empty rail", () => {
  const row = render({ player: makePlayer({ todaysGame: null }), today: 0, season: 25 });

  expect(row.querySelector(".ffx-score__today")!.textContent).toBe("–");
  expect(row.querySelector(".ffx-rail__bar")).toBeNull();
  expect(row.querySelector<HTMLElement>(".ffx-rail__tick")!.style.left).toBe("50px");
});

test("a day-to-day player's bar is hatched when he has a game today", () => {
  const dtdWithGame = render({ player: makePlayer({ playerStatus: "DTD" }) });
  const healthy = render();

  expect(dtdWithGame.querySelector(".ffx-rail__bar--dtd")).not.toBeNull();
  expect(healthy.querySelector(".ffx-rail__bar--dtd")).toBeNull();
});

test("a player scored mostly on the no-projection guess is flagged 'est', and the popover explains the guess", () => {
  const guessed = render({ debugInfo: { seasonProjectionAvg: undefined, seasonProjectionWeight: 0.5 } });
  const barelyGuessed = render({ debugInfo: { seasonProjectionAvg: undefined, seasonProjectionWeight: 0.2 } });

  expect(guessed.querySelector(".ffx-score__est")!.textContent).toBe("est");
  expect(guessed.querySelector(".ffx-popover")!.lastElementChild!.textContent).toMatchInlineSnapshot(`"No preseason projection, so a guess of ~6.0 is weighted at 50%"`);
  expect(barelyGuessed.querySelector(".ffx-score__est")).toBeNull();
  expect(barelyGuessed.querySelector(".ffx-popover")!.textContent).not.toContain("projection");
});

test("scoring a player again redraws his one rail with the new values", () => {
  const player = makePlayer();
  render({ player, today: 12, season: 20 });

  const row = render({ player, today: 35, season: 41 });

  expect(row.querySelectorAll(".ffx-score")).toHaveLength(1);
  expect(row.querySelector(".ffx-score__today")!.textContent).toBe("35.0");
  expect(row.querySelector(".ffx-score__season")!.textContent).toBe("41.0");
});
