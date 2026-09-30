import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, expect, test } from "bun:test";
import type { Player } from "../types";
import { setOptimalLineup } from "./set-optimal-lineup";

beforeAll(() => GlobalRegistrator.register());
afterAll(() => GlobalRegistrator.unregister());

const SLOT_OPTIONS_BY_POSITION: Record<string, string[]> = {
  PG: ["PG", "G", "ANY"],
  SG: ["SG", "G", "ANY"],
  SF: ["SF", "F/C", "ANY"],
  PF: ["PF", "F/C", "ANY"],
  C: ["C", "F/C", "ANY"],
};

test("starts a 4th center in the F/C slot so all 9 slots fill", () => {
  const players = setupRoster(["PG", "PG", "SG", "SF", "PF", "C", "C", "C", "C"]);

  const { numStarted } = setOptimalLineup(players);

  expect(numStarted).toBe(9);
  expect(getStartedSlots(players)).toEqual(["ANY", "ANY", "C", "F/C", "G", "PF", "PG", "SF", "SG"]);
});

function setupRoster(positions: string[]): Player[] {
  document.body.innerHTML = `<a class="btn" data-toggle="dropdown">Today</a><table></table>`;
  const table = document.querySelector("table")!;
  return positions.map((position, i) => {
    const row = table.insertRow();
    row.insertCell();
    const select = document.createElement("select");
    const slotOptions = ["BENCH", ...SLOT_OPTIONS_BY_POSITION[position]];
    slotOptions.forEach((text, value) => {
      const option = document.createElement("option");
      option.text = text;
      option.value = String(value);
      select.add(option);
    });
    select.value = "0";
    row.cells[0].appendChild(select);
    return {
      playerName: `Player ${i + 1} (${position})`,
      playerStatus: "(active)",
      refinedPlayerStatus: undefined,
      last5Avg: 30 - i,
      last10Avg: 30 - i,
      seasonAvg: 30 - i,
      seasonTotal: (30 - i) * 20,
      gamesPlayed: 20,
      todaysGame: "BOS",
      position,
      setPositionDropdown: select,
      isTaxi: false,
      isIr: false,
      opponentInfo: undefined,
      row,
    };
  });
}

function getStartedSlots(players: Player[]) {
  return players
    .map((p) => p.setPositionDropdown!.selectedOptions[0].text)
    .filter((slot) => slot !== "BENCH")
    .sort();
}
