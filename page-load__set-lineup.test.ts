import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, beforeEach, expect, setSystemTime, spyOn, test } from "bun:test";
import {
  givePlayerGame,
  loadLineupPage,
  PAGE_URL,
  playerRow,
  showStatView,
  startedLineup,
} from "./src/lineup/fixtures/lineup-page";
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

// The extension's floating buttons are appended last, after any Fleaflicker button with the same text
function button(name: string) {
  return Array.from(document.querySelectorAll("button")).findLast((b) => b.textContent!.trim() === name);
}

// Records where the browser would navigate when a link is clicked, without leaving the page
function recordNavigations() {
  const hrefs: string[] = [];
  document.addEventListener("click", (event) => {
    const link = (event.target as Element).closest("a");
    if (!link) return;
    event.preventDefault();
    hrefs.push(link.getAttribute("href")!);
  });
  return hrefs;
}

// Captures what Fleaflicker would receive when its lineup form is submitted, without leaving the page
function recordLineupSubmissions() {
  const form = document.querySelector<HTMLFormElement>("form[method='post']")!;
  const submissions: Record<string, string>[] = [];
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    submissions.push(Object.fromEntries(new FormData(form, event.submitter)) as Record<string, string>);
  });
  return submissions;
}

// Another owner's team page matches the saved page as-is: same table and date picker, no slot selects
test("on another owner's team page, shows no lineup buttons", async () => {
  loadLineupPage({ loggedIn: false });

  await runContentScript();

  expect(alerts).toEqual([]);
  expect(button("Set Lineup") != null).toBe(false);
  expect(button("Save Lineup") != null).toBe(false);
});

test("clicking Set Lineup starts 9 legal starters, one per league slot", async () => {
  loadLineupPage();
  givePlayerGame("Josh Giddey", "LAL");
  givePlayerGame("Miles Bridges", "LAL");
  givePlayerGame("Jakob Poeltl", "CHI");
  for (const select of document.querySelectorAll("select")) select.value = "0";
  await runContentScript();

  button("Set Lineup")!.click();
  for (let waited = 0; Object.keys(startedLineup()).length < 9 && waited < 3000; waited += 10) await Bun.sleep(10);

  expect(alerts).toEqual([]);
  expect(Object.values(startedLineup()).sort()).toEqual(["ANY", "ANY", "C", "F/C", "G", "PF", "PG", "SF", "SG"]);
});

test("clicking Set Lineup off the fantasy stats view tells the user", async () => {
  loadLineupPage();
  showStatView("season stats");
  await runContentScript();

  button("Set Lineup")!.click();
  for (let waited = 0; alerts.length === 0 && waited < 3000; waited += 10) await Bun.sleep(10);

  expect(alerts).toEqual([expect.stringContaining("Not on the fantasy stats page")]);
});

test("the Save Lineup button and its shortcut submit Fleaflicker's lineup form with the chosen slots", async () => {
  loadLineupPage();
  const submissions = recordLineupSubmissions();
  await runContentScript();
  const nazReidSlot = playerRow("Naz Reid").querySelector("select")!;
  nazReidSlot.value = "16"; // C

  button("Save Lineup")!.click();
  (window as any).saveLineup(); // Cmd+Shift+I

  expect(submissions).toHaveLength(2);
  for (const submitted of submissions) expect(submitted[nazReidSlot.name]).toBe("16");
});

test("saving while logged out reports that nothing was saved", async () => {
  loadLineupPage({ loggedIn: false });
  await runContentScript();

  let thrown: unknown;
  try {
    (window as any).saveLineup();
  } catch (error) {
    thrown = error;
  }

  expect(alerts.length > 0 || thrown !== undefined).toBe(true);
});

test("the next-day shortcut opens the next day's lineup", async () => {
  loadLineupPage();
  const navigations = recordNavigations();
  await runContentScript();

  (window as any).goToNextDay();

  expect(navigations).toEqual(["/nba/leagues/30579/teams/161025?week=2"]); // Wed 10/21
});

test("the previous-day shortcut goes back a day, and on opening night stays put instead of jumping to last season", async () => {
  loadLineupPage();
  const navigations = recordNavigations();
  await runContentScript();

  (window as any).goToPreviousDay();
  expect(navigations).toEqual([]);

  // Past opening night Fleaflicker adds a back arrow before the date picker, mirroring the forward one (guessed markup)
  const datePicker = Array.from(document.querySelectorAll("a.dropdown-toggle")).find((a) =>
    a.textContent!.includes("Tue 10/20"),
  )!.parentElement!;
  datePicker.insertAdjacentHTML(
    "beforebegin",
    '<a class="btn btn-primary" href="/nba/leagues/30579/teams/161025?week=1" title="Mon 10/19"><i class="fa fa-chevron-left"></i></a>',
  );
  (window as any).goToPreviousDay();
  expect(navigations).toEqual(["/nba/leagues/30579/teams/161025?week=1"]);
});

// Runs in its own process: the content script rethrows so the failure reaches whatever runs the
// page (a headless runner sees an uncaught error), which would fail this test runner outright
test("when the page can't be read, tells the user and fails the page script loudly", () => {
  const script = `
    import { GlobalRegistrator } from "@happy-dom/global-registrator";
    import { loadLineupPage, PAGE_URL } from "./src/lineup/fixtures/lineup-page";
    GlobalRegistrator.register({ url: PAGE_URL, settings: ${JSON.stringify(HAPPY_DOM_SETTINGS)} });
    loadLineupPage();
    // Fleaflicker drops the date picker
    for (const a of document.querySelectorAll("a.dropdown-toggle")) if (a.textContent.includes("Tue 10/20")) a.remove();
    console.log = console.error = console.warn = console.table = () => {};
    window.alert = (message) => process.stdout.write("ALERT: " + message + "\\n");
    await import("./page-load__set-lineup.ts");
  `;

  const run = Bun.spawnSync(["bun", "-e", script], { cwd: import.meta.dir });

  expect(run.stdout.toString()).toMatch(/^ALERT: .*date/im);
  expect(run.stderr.toString()).toMatch(/date/i);
  expect(run.exitCode).not.toBe(0);
});
