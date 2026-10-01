import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, beforeEach, expect, setSystemTime, spyOn, test } from "bun:test";
import { givePlayerGame, givePlayerNews, playerRows, loadLineupPage, PAGE_URL, playerRow } from "./src/lineup/fixtures/lineup-page";
import { HAPPY_DOM_SETTINGS, recordAlerts, runContentScript } from "./src/lineup/fixtures/content-script";

beforeAll(() => GlobalRegistrator.register({ url: PAGE_URL, settings: HAPPY_DOM_SETTINGS }));
afterAll(() => {
  setSystemTime();
  GlobalRegistrator.unregister();
});

let alerts: string[];
beforeEach(() => {
  setSystemTime(new Date("2026-10-20T14:00:00Z"));
  for (const method of ["log", "table", "clear", "warn"] as const) spyOn(console, method).mockImplementation(() => {});
  alerts = recordAlerts();
});

function scoreBadge(name: string) {
  return playerRow(name).querySelector<HTMLElement>("[data-predicted-score]")!;
}

function isShown(el: HTMLElement) {
  return getComputedStyle(el).visibility !== "hidden";
}

// The popover the score group points to via `aria-describedby`, one "label value" string per row
function popoverRows(name: string) {
  const score = playerRow(name).querySelector<HTMLElement>("[aria-describedby]")!;
  expect(score.tabIndex).toBe(0);
  expect(score.hasAttribute("title")).toBe(false);
  const popover = document.getElementById(score.getAttribute("aria-describedby")!)!;
  expect(popover.getAttribute("role")).toBe("tooltip");
  return Array.from(popover.children, (row) => Array.from(row.children, (cell) => cell.textContent).join(" "));
}

function todayText(name: string) {
  return playerRow(name).querySelector(".ffx-score__today")!.textContent!;
}

function todayBar(name: string) {
  return playerRow(name).querySelector<HTMLElement>(".ffx-rail__bar");
}

const BONA_PROBABLE_NEWS =
  '<div class="news-text"><h5>Adem Bona Probable Tuesday</h5>' +
  '<em><relative-time datetime="2026-10-20T12:00:00Z">Tue 10/20/26 8:00 AM</relative-time></em>' +
  "<p>Philadelphia 76ers center Adem Bona (knee) is probable for Tuesday's game against the Knicks.</p></div>";

test("on load, a player with a game gets today's projection as a bar; a player without one gets a dash and no bar", async () => {
  loadLineupPage();

  await runContentScript();

  expect(alerts).toEqual([]);
  const cadeToday = parseFloat(todayText("Cade Cunningham"));
  expect(cadeToday).toBeGreaterThan(0);
  expect(parseFloat(todayBar("Cade Cunningham")!.style.width)).toBeCloseTo(Math.min(cadeToday, 60) * 2, 0);
  expect(todayText("Naz Reid")).toBe("–");
  expect(todayBar("Naz Reid")).toBeNull();
  expect(todayText("Kyrie Irving")).toBe("–"); // out for season, no game
});

test("hovering or focusing a score describes today's projection, season value, and opponent and injury adjustments", async () => {
  loadLineupPage();

  await runContentScript();

  expect(popoverRows("Cade Cunningham")).toMatchInlineSnapshot(`
    [
      "Today 35.4",
      "Season 47.6",
      "Opponent -1.7",
    ]
  `);
  expect(popoverRows("Adem Bona")).toMatchInlineSnapshot(`
    [
      "Today 0.0",
      "Season 17.0",
      "Opponent -1.2",
      "Injury ×0",
    ]
  `);
});

// Another owner's team page matches the saved page as-is: same table and date picker, no slot selects
test("on another owner's team page, shows the scores", async () => {
  loadLineupPage({ loggedIn: false });

  await runContentScript();

  expect(alerts).toEqual([]);
  expect(parseFloat(todayText("Cade Cunningham"))).toBeGreaterThan(0);
});

test("injury news that upgrades an OUT player scores him", async () => {
  loadLineupPage();
  givePlayerNews("Adem Bona", BONA_PROBABLE_NEWS);

  await runContentScript();

  expect(parseFloat(todayText("Adem Bona"))).toBeGreaterThan(0);
});
