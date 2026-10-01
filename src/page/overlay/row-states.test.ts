import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, beforeEach, expect, setSystemTime, spyOn, test } from "bun:test";
import { giveInjuryTag, loadLineupPage, PAGE_URL, playerRow, playerRows } from "../../lineup/fixtures/lineup-page";
import { HAPPY_DOM_SETTINGS, recordAlerts } from "../../lineup/fixtures/content-script";
import { setLineup } from "../../lineup/set-lineup";
import type { Player } from "../../types";
import { stylePlayerAsAlternate } from "./row-states";
import { injectOverlayStyles } from "./styles";

beforeAll(() => GlobalRegistrator.register({ url: PAGE_URL, settings: HAPPY_DOM_SETTINGS }));
afterAll(() => {
  setSystemTime();
  GlobalRegistrator.unregister();
});

beforeEach(() => {
  setSystemTime(new Date("2026-10-20T14:00:00Z"));
  for (const method of ["log", "table", "clear", "warn"] as const) spyOn(console, method).mockImplementation(() => {});
  recordAlerts();
});

// Player name → the overlay's row-state classes, for every row that has one
function rowStates() {
  return Object.fromEntries(
    playerRows()
      .map((row) => [row.querySelector(".player-text")!.textContent, rowStateClasses(row)])
      .filter(([, classes]) => classes),
  );
}

function rowStateClasses(row: HTMLTableRowElement) {
  return Array.from(row.classList)
    .filter((name) => name.startsWith("ffx-row--"))
    .join(" ");
}

test("after Set lineup, each starter's row is marked started, with no inline styling on any row", async () => {
  loadLineupPage();

  await setLineup();

  expect(rowStates()).toMatchInlineSnapshot(`
    {
      "Adem Bona": "ffx-row--started",
      "Andre Drummond": "ffx-row--started",
      "Anfernee Simons": "ffx-row--started",
      "Cade Cunningham": "ffx-row--started",
      "De'Aaron Fox": "ffx-row--started",
      "Devin Vassell": "ffx-row--started",
      "John Collins": "ffx-row--started",
      "Josh Giddey": "ffx-row--started",
      "Neemias Queta": "ffx-row--started",
    }
  `);
  for (const row of playerRows()) {
    expect(row.getAttribute("style")).toBeNull();
    for (const cell of row.cells) expect(cell.getAttribute("style")).toBeNull();
  }
});

test("a day-to-day starter with a game today is marked both started and at risk, with no inline outline", async () => {
  loadLineupPage();
  giveInjuryTag("Cade Cunningham", "DTD");

  await setLineup();

  const row = playerRow("Cade Cunningham");
  expect(rowStateClasses(row)).toBe("ffx-row--risk ffx-row--started");
  expect(row.getAttribute("style")).toBeNull();
});

test("after Set lineup, a player on the taxi squad is marked unable to start", async () => {
  loadLineupPage();
  playerRow("Darius Garland").querySelector("select")!.innerHTML =
    '<option value="0">Bench</option><option value="99" selected="selected">TAXI</option>';

  await setLineup();

  expect(rowStateClasses(playerRow("Darius Garland"))).toBe("ffx-row--unable");
  expect(playerRow("Darius Garland").getAttribute("style")).toBeNull();
});

test("an alternate's row is marked started and alternate, and marking it again changes nothing", () => {
  loadLineupPage();
  const player = { row: playerRow("Darius Garland") } as Player;

  stylePlayerAsAlternate(player);
  stylePlayerAsAlternate(player);

  expect(rowStateClasses(player.row)).toBe("ffx-row--started ffx-row--alternate");
  expect(player.row.getAttribute("style")).toBeNull();
});

test("on the page, started rows get a blue tint, at-risk rows an orange one even when also started, and unable rows are dimmed", async () => {
  loadLineupPage();
  injectOverlayStyles();
  giveInjuryTag("Cade Cunningham", "DTD");
  playerRow("Darius Garland").querySelector("select")!.innerHTML =
    '<option value="0">Bench</option><option value="99" selected="selected">TAXI</option>';

  await setLineup();

  const firstCell = (name: string) => getComputedStyle(playerRow(name).cells[0]);
  expect(firstCell("Josh Giddey").backgroundColor).toBe("#EAF1F9");
  expect(firstCell("Cade Cunningham").backgroundColor).toBe("#FCEEE3");
  expect(firstCell("Darius Garland").opacity).toBe("0.55");
});
