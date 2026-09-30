import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, beforeEach, expect, setSystemTime, spyOn, test } from "bun:test";
import { givePlayerGame, loadLineupPage, PAGE_URL, playerRow, startedLineup } from "./src/lineup/fixtures/lineup-page";

beforeAll(() =>
  GlobalRegistrator.register({
    url: PAGE_URL,
    settings: {
      disableJavaScriptFileLoading: true,
      disableCSSFileLoading: true,
      handleDisabledFileLoadingAsSuccess: true,
    },
  }),
);
afterAll(() => {
  setSystemTime();
  GlobalRegistrator.unregister();
});

let alerts: string[];
beforeEach(() => {
  setSystemTime(new Date("2026-10-20T14:00:00Z"));
  alerts = [];
  for (const method of ["log", "table", "clear", "warn"] as const) spyOn(console, method).mockImplementation(() => {});
  spyOn(window, "alert").mockImplementation((message) => void alerts.push(String(message)));
});

function button(name: string) {
  return Array.from(document.querySelectorAll("button")).find((b) => b.textContent!.trim() === name);
}

function scoreShownFor(name: string) {
  // The predicted score badge is prepended to the player's name cell
  return parseFloat(playerRow(name).cells[0].textContent!);
}

test("on load, shows each player's predicted score and adds the Set Lineup / Save Lineup buttons", async () => {
  loadLineupPage();

  await import("./page-load__set-lineup.ts?load");
  await Bun.sleep(0);

  expect(alerts).toEqual([]);
  expect(button("Set Lineup")).toBeDefined();
  expect(button("Save Lineup")).toBeDefined();
  expect(scoreShownFor("Cade Cunningham")).toBeGreaterThan(0);
  expect(scoreShownFor("Naz Reid")).toBe(0); // no game today
  expect(scoreShownFor("Adem Bona")).toBe(0); // OUT
  expect(scoreShownFor("Kyrie Irving")).toBe(0); // out for season, no game
});

test("clicking Set Lineup starts 9 legal starters, one per league slot", async () => {
  loadLineupPage();
  givePlayerGame("Josh Giddey", "LAL");
  givePlayerGame("Miles Bridges", "LAL");
  givePlayerGame("Jakob Poeltl", "CHI");
  for (const select of document.querySelectorAll("select")) select.value = "0";
  await import("./page-load__set-lineup.ts?click");
  await Bun.sleep(0);

  button("Set Lineup")!.click();
  for (let waited = 0; Object.keys(startedLineup()).length < 9 && waited < 3000; waited += 10) await Bun.sleep(10);

  expect(alerts).toEqual([]);
  expect(Object.values(startedLineup()).sort()).toEqual(["ANY", "ANY", "C", "F/C", "G", "PF", "PG", "SF", "SG"]);
});
