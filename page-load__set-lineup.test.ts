import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, beforeEach, expect, setSystemTime, spyOn, test } from "bun:test";
import { readFileSync } from "node:fs";
import {
  givePlayerGame,
  givePlayerNews,
  loadLineupPage,
  PAGE_URL,
  playerRow,
  startedLineup,
} from "./src/lineup/fixtures/lineup-page";

const HAPPY_DOM_SETTINGS = {
  disableJavaScriptFileLoading: true,
  disableCSSFileLoading: true,
  handleDisabledFileLoadingAsSuccess: true,
};

beforeAll(() => GlobalRegistrator.register({ url: PAGE_URL, settings: HAPPY_DOM_SETTINGS }));
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

// Each import re-runs the content script, like a fresh page load
let loads = 0;
async function runContentScript() {
  await import(`./page-load__set-lineup.ts?load=${++loads}`);
  await Bun.sleep(0);
}

// The extension's floating buttons are appended last, after any Fleaflicker button with the same text
function button(name: string) {
  return Array.from(document.querySelectorAll("button")).findLast((b) => b.textContent!.trim() === name);
}

function scoreBadge(name: string) {
  return playerRow(name).querySelector<HTMLElement>("[data-predicted-score]")!;
}

function isShown(el: HTMLElement) {
  return getComputedStyle(el).visibility !== "hidden";
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

// The real page a logged-in owner sees (same day), with Fleaflicker's own lineup form and Save Lineup button
function loadLoggedInLineupPage() {
  const html = readFileSync(`${import.meta.dir}/src/lineup/fixtures/teampage-logged-in.html`, "utf8");
  const [, head, body] = html.match(/<head>([\s\S]*)<\/head>\s*<body[^>]*>([\s\S]*)<\/body>/)!;
  document.head.innerHTML = head;
  document.body.innerHTML = body;
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

const BONA_PROBABLE_NEWS =
  '<div class="news-text"><h5>Adem Bona Probable Tuesday</h5>' +
  '<em><relative-time datetime="2026-10-20T12:00:00Z">Tue 10/20/26 8:00 AM</relative-time></em>' +
  "<p>Philadelphia 76ers center Adem Bona (knee) is probable for Tuesday's game against the Knicks.</p></div>";

test("on load, shows a predicted score for players with a game and hides it for everyone else", async () => {
  loadLineupPage();

  await runContentScript();

  expect(alerts).toEqual([]);
  expect(isShown(scoreBadge("Cade Cunningham"))).toBe(true);
  expect(parseFloat(scoreBadge("Cade Cunningham").textContent!)).toBeGreaterThan(0);
  expect(isShown(scoreBadge("Naz Reid"))).toBe(false); // no game today
  expect(isShown(scoreBadge("Adem Bona"))).toBe(false); // OUT
  expect(isShown(scoreBadge("Kyrie Irving"))).toBe(false); // out for season, no game
});

test("hovering a score explains its opponent and injury adjustments", async () => {
  loadLineupPage();

  await runContentScript();

  expect(scoreBadge("Cade Cunningham").title).toMatch(/^Opponent adjustment: [+-]\d+\.\d\nInjury multiplier: \(none\)$/);
  expect(scoreBadge("Adem Bona").title).toMatch(/\nInjury multiplier: 0%$/);
});

// Another owner's team page matches the saved page as-is: same table and date picker, no slot selects
test("on another owner's team page, shows the scores but no lineup buttons", async () => {
  loadLineupPage({ loggedIn: false });

  await runContentScript();

  expect(alerts).toEqual([]);
  expect(isShown(scoreBadge("Cade Cunningham"))).toBe(true);
  expect(parseFloat(scoreBadge("Cade Cunningham").textContent!)).toBeGreaterThan(0);
  expect(button("Set Lineup")).toBeUndefined();
  expect(button("Save Lineup")).toBeUndefined();
});

// Uses the filled news icon the app reads; the real pages only show the outlined one (pinned below)
test("injury news that upgrades an OUT player shows the new status and scores him", async () => {
  loadLineupPage();
  givePlayerNews("Adem Bona", BONA_PROBABLE_NEWS);
  playerRow("Adem Bona").querySelector(".fa-file-text-o")!.classList.replace("fa-file-text-o", "fa-file-text");

  await runContentScript();

  expect(playerRow("Adem Bona").querySelector(".injury")!.textContent).toMatchInlineSnapshot(`"✨P"`);
  expect(isShown(scoreBadge("Adem Bona"))).toBe(true);
  expect(parseFloat(scoreBadge("Adem Bona").textContent!)).toBeGreaterThan(0);
});

// Suspected bug: every news icon on both real saved pages is `fa-file-text-o` (incl. news posted hours
// before the save), but only `fa-file-text` icons are read, so news never refines a player's status
test.failing("injury news behind Fleaflicker's news icon updates the status", async () => {
  loadLineupPage();
  givePlayerNews("Adem Bona", BONA_PROBABLE_NEWS);

  await runContentScript();

  expect(playerRow("Adem Bona").querySelector(".injury")!.textContent).toBe("✨P");
  expect(isShown(scoreBadge("Adem Bona"))).toBe(true);
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

test("the Save Lineup button and its shortcut submit Fleaflicker's lineup form with the chosen slots", async () => {
  loadLoggedInLineupPage();
  const submissions = recordLineupSubmissions();
  await runContentScript();
  const nazReidSlot = playerRow("Naz Reid").querySelector("select")!;
  nazReidSlot.value = "16"; // C

  button("Save Lineup")!.click();
  (window as any).saveLineup(); // Cmd+Shift+I

  expect(submissions).toHaveLength(2);
  for (const submitted of submissions) expect(submitted[nazReidSlot.name]).toBe("16");
});

// Suspected bug: logged out (e.g. an expired session) there's no Fleaflicker save button, and saving
// silently does nothing, so a headless run would think the lineup was saved
test.failing("saving while logged out reports that nothing was saved", async () => {
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
