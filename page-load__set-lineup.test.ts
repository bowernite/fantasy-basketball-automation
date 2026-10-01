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
import { reportProblem } from "./src/lineup/report-problem";

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

function button(name: string) {
  return Array.from(document.querySelectorAll("button")).find((b) => b.textContent!.trim() === name);
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
  expect(button("Set lineup") != null).toBe(false);
  expect(button("Save lineup") != null).toBe(false);
});

test("Set lineup and Save lineup sit together at the start of the toolbar above the roster", async () => {
  loadLineupPage();

  await runContentScript();

  const toolbar = document.querySelector("#body-top .btn-toolbar")!;
  const group = toolbar.firstElementChild!;
  expect(Array.from(group.querySelectorAll("button"), (b) => b.textContent!.trim())).toEqual(["Set lineup", "Save lineup"]);
  expect(group.nextElementSibling!.textContent).toBe("Roster for");
});

test("the lineup button icons are 16px", async () => {
  loadLineupPage();

  await runContentScript();

  const icon = getComputedStyle(button("Set lineup")!.querySelector("svg")!);
  expect([icon.width, icon.height]).toEqual(["16px", "16px"]);
});

test("running the page script again doesn't add a second set of lineup buttons", async () => {
  loadLineupPage();

  await runContentScript();
  await runContentScript();

  expect(Array.from(document.querySelectorAll("button")).filter((b) => b.textContent!.trim() === "Set lineup")).toHaveLength(1);
});

test("if Fleaflicker reworks that toolbar, the lineup buttons go at the top of the roster area", async () => {
  loadLineupPage();
  document.querySelector("#body-top .button-bar")!.className = "action-bar";

  await runContentScript();

  const rosterArea = document.getElementById("body-center-main")!;
  expect(rosterArea.firstElementChild!.querySelector("button")!.textContent!.trim()).toBe("Set lineup");
});

test("clicking Set lineup starts 9 legal starters, one per league slot", async () => {
  loadLineupPage();
  givePlayerGame("Josh Giddey", "LAL");
  givePlayerGame("Miles Bridges", "LAL");
  givePlayerGame("Jakob Poeltl", "CHI");
  for (const select of document.querySelectorAll("select")) select.value = "0";
  await runContentScript();

  button("Set lineup")!.click();
  for (let waited = 0; Object.keys(startedLineup()).length < 9 && waited < 3000; waited += 10) await Bun.sleep(10);

  expect(alerts).toEqual([]);
  expect(Object.values(startedLineup()).sort()).toEqual(["ANY", "ANY", "C", "F/C", "G", "PF", "PG", "SF", "SG"]);
});

test("Set lineup shows it's busy until the lineup is set, then hands the lead to Save lineup", async () => {
  loadLineupPage();
  await runContentScript();
  const setButton = button("Set lineup")!;

  setButton.click();

  expect(setButton.disabled).toBe(true);
  expect(setButton.getAttribute("aria-busy")).toBe("true");
  expect(setButton.textContent!.trim()).toMatchInlineSnapshot(`"Setting lineup…"`);

  for (let waited = 0; setButton.disabled && waited < 3000; waited += 10) await Bun.sleep(10);

  expect(setButton.disabled).toBe(false);
  expect(setButton.hasAttribute("aria-busy")).toBe(false);
  expect(setButton.textContent!.trim()).toBe("Set lineup");
  expect(button("Save lineup")!.classList.contains("btn-primary")).toBe(true);
  expect(setButton.classList.contains("btn-primary")).toBe(false);
  expect(document.querySelector("[role=status]")!.textContent).toMatchInlineSnapshot(`"Lineup set. Review the highlighted rows, then save."`);
  expect(alerts).toEqual([]);
});

test("the Set lineup shortcut shows the same busy button as clicking it", async () => {
  loadLineupPage();
  await runContentScript();
  const setButton = button("Set lineup")!;

  (window as any).runSetLineup(); // Cmd+Shift+U

  expect(setButton.disabled).toBe(true);
  expect(setButton.textContent!.trim()).toBe("Setting lineup…");
  for (let waited = 0; setButton.disabled && waited < 3000; waited += 10) await Bun.sleep(10);
  expect(document.querySelector("[role=status]")!.textContent).toBe("Lineup set. Review the highlighted rows, then save.");
});

test("a problem found while working on the lineup shows on the page instead of a popup", async () => {
  loadLineupPage();
  await runContentScript();

  reportProblem("Tried to start Naz Reid without a dropdown");

  expect(document.querySelector("[role=alert]")!.textContent).toBe("Tried to start Naz Reid without a dropdown");
  expect(alerts).toEqual([]);
});

test("clicking Set lineup off the fantasy stats view tells the user on the page, with a retry", async () => {
  loadLineupPage();
  showStatView("season stats");
  await runContentScript();

  button("Set lineup")!.click();
  for (let waited = 0; !document.querySelector("[role=alert]") && waited < 3000; waited += 10) await Bun.sleep(10);

  const notice = document.querySelector("[role=alert]")!;
  expect(notice.firstChild!.textContent).toMatchInlineSnapshot(`"Couldn't set the lineup; nothing changed. Not on the fantasy stats page; aborting"`);
  expect(notice.querySelector("button")!.textContent).toBe("Retry");
  expect(alerts).toEqual([]);
});

test("Save lineup shows it's saving and submits Fleaflicker's lineup form with the chosen slots", async () => {
  loadLineupPage();
  const submissions = recordLineupSubmissions();
  await runContentScript();
  const nazReidSlot = playerRow("Naz Reid").querySelector("select")!;
  nazReidSlot.value = "16"; // C
  const saveButton = button("Save lineup")!;

  saveButton.click();

  expect(saveButton.disabled).toBe(true);
  expect(saveButton.textContent!.trim()).toMatchInlineSnapshot(`"Saving…"`);
  expect(submissions.map((submitted) => submitted[nazReidSlot.name])).toEqual(["16"]);
});

test("if Fleaflicker's own save is gone, Save lineup says nothing was saved and can be clicked again", async () => {
  loadLineupPage();
  await runContentScript();
  document.querySelector("button[type=submit]")!.remove();
  const saveButton = button("Save lineup")!;

  saveButton.click();

  expect(document.querySelector("[role=alert]")!.textContent).toMatchInlineSnapshot(`"Couldn't save the lineup. No Save Lineup button on the page; you may be logged out. Nothing was saved"`);
  expect(saveButton.disabled).toBe(false);
  expect(saveButton.textContent!.trim()).toBe("Save lineup");
  expect(alerts).toEqual([]);
});

test("the save shortcut submits Fleaflicker's lineup form with the chosen slots", async () => {
  loadLineupPage();
  const submissions = recordLineupSubmissions();
  await runContentScript();
  const nazReidSlot = playerRow("Naz Reid").querySelector("select")!;
  nazReidSlot.value = "16"; // C

  (window as any).saveLineup(); // Cmd+Shift+I

  expect(submissions.map((submitted) => submitted[nazReidSlot.name])).toEqual(["16"]);
});

test("saving while logged out reports that nothing was saved", async () => {
  loadLineupPage({ loggedIn: false });
  await runContentScript();

  (window as any).saveLineup();

  expect(document.querySelector("[role=alert]")!.textContent).toMatchInlineSnapshot(`"Couldn't save the lineup. No Save Lineup button on the page; you may be logged out. Nothing was saved"`);
  expect(alerts).toEqual([]);
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

// Runs the built content script the way the browser does, as one classic script whose top-level
// functions become page globals; in its own process so those globals don't leak into other tests
test("Save lineup in the built extension submits Fleaflicker's lineup form", () => {
  const script = `
    import { GlobalRegistrator } from "@happy-dom/global-registrator";
    import { loadLineupPage, PAGE_URL, playerRow } from "./src/lineup/fixtures/lineup-page";
    GlobalRegistrator.register({ url: PAGE_URL, settings: ${JSON.stringify(HAPPY_DOM_SETTINGS)} });
    loadLineupPage();
    console.log = console.error = console.warn = console.table = () => {};
    const form = document.querySelector("form[method='post']");
    const submissions = [];
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      submissions.push(Object.fromEntries(new FormData(form, event.submitter)));
    });
    const build = await Bun.build({ entrypoints: ["./page-load__set-lineup.ts"] });
    (0, eval)(await build.outputs[0].text());
    await Bun.sleep(0);
    const nazReidSlot = playerRow("Naz Reid").querySelector("select");
    nazReidSlot.value = "16"; // C

    Array.from(document.querySelectorAll("button")).find((b) => b.textContent.trim() === "Save lineup").click();

    process.stdout.write(JSON.stringify(submissions.map((submitted) => submitted[nazReidSlot.name])));
  `;

  const run = Bun.spawnSync(["bun", "-e", script], { cwd: import.meta.dir });

  expect(run.stdout.toString()).toBe('["16"]');
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
    process.on("exit", () => {
      const notice = document.querySelector("[role=alert]");
      process.stdout.write(JSON.stringify({
        message: notice?.firstChild?.textContent,
        buttons: Array.from(notice?.querySelectorAll("button") ?? [], (b) => b.textContent || b.getAttribute("aria-label")),
      }));
    });
    await import("./page-load__set-lineup.ts");
  `;

  const run = Bun.spawnSync(["bun", "-e", script], { cwd: import.meta.dir });

  expect(JSON.parse(run.stdout.toString())).toMatchInlineSnapshot(`
    {
      "buttons": [
        "Reload page",
        "Dismiss",
      ],
      "message": "Couldn't read the roster page; the lineup wasn't changed. Tried to get page date but found 0 date buttons",
    }
  `);
  expect(run.stderr.toString()).toMatch(/date/i);
  expect(run.exitCode).not.toBe(0);
});
