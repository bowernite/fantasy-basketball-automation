import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, afterEach, beforeAll, beforeEach, expect, setSystemTime, spyOn, test } from "bun:test";
import { givePlayerGame, loadLineupPage, lockPlayer, PAGE_URL, slotOf, startedLineup } from "./fixtures/lineup-page";

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
afterAll(() => GlobalRegistrator.unregister());

let alerts: string[];
beforeEach(() => {
  // Morning of the fixture's day, before any tip
  setSystemTime(new Date("2026-10-20T14:00:00Z"));
  alerts = [];
  for (const method of ["log", "table", "clear", "warn"] as const) spyOn(console, method).mockImplementation(() => {});
  spyOn(window, "alert").mockImplementation((message) => void alerts.push(String(message)));
});
afterEach(() => setSystemTime());

// Problems reach the user as an alert or a rejection (a headless runner would only see the latter)
async function setLineupAndCollectProblems() {
  const { setLineup } = await import("./set-lineup");
  const errors: string[] = [];
  await setLineup().catch((error) => errors.push(String(error)));
  return [...alerts, ...errors];
}

test("on the real opening-night page, starts all 8 players who have a game and fills the 9th slot", async () => {
  loadLineupPage();
  for (const select of document.querySelectorAll("select")) select.value = "0";

  const problems = await setLineupAndCollectProblems();

  expect(problems).toEqual([]);
  expect(startedLineup()).toMatchInlineSnapshot(`
    {
      "Adem Bona": "PF",
      "Andre Drummond": "ANY",
      "Anfernee Simons": "SG",
      "Cade Cunningham": "PG",
      "De'Aaron Fox": "G",
      "Devin Vassell": "SF",
      "John Collins": "C",
      "Josh Giddey": "ANY",
      "Neemias Queta": "F/C",
    }
  `);
});

test("on a busy night, replaces the current lineup with 9 legal starters, one per league slot", async () => {
  loadLineupPage();
  givePlayerGame("Josh Giddey", "LAL");
  givePlayerGame("Darius Garland", "@MIA");
  givePlayerGame("Miles Bridges", "LAL");
  givePlayerGame("Aaron Gordon", "@MIA");
  givePlayerGame("Jakob Poeltl", "CHI");

  const problems = await setLineupAndCollectProblems();

  expect(problems).toEqual([]);
  expect(Object.values(startedLineup()).sort()).toEqual(["ANY", "ANY", "C", "F/C", "G", "PF", "PG", "SF", "SG"]);
  expect(startedLineup()).toMatchInlineSnapshot(`
    {
      "Aaron Gordon": "PF",
      "Andre Drummond": "F/C",
      "Cade Cunningham": "PG",
      "Darius Garland": "ANY",
      "De'Aaron Fox": "SG",
      "Jakob Poeltl": "ANY",
      "Josh Giddey": "G",
      "Miles Bridges": "SF",
      "Neemias Queta": "C",
    }
  `);
});

test("does not start players who are OUT when 9 healthy players have a game", async () => {
  loadLineupPage();
  // Adem Bona (a current starter) and Mark Williams are OUT; with these, 11 players have a game
  givePlayerGame("Mark Williams", "LAL");
  givePlayerGame("Jakob Poeltl", "LAL");
  givePlayerGame("Jarace Walker", "LAL");

  const problems = await setLineupAndCollectProblems();

  expect(problems).toEqual([]);
  expect(slotOf("Adem Bona")).toBe("BN");
  expect(slotOf("Mark Williams")).toBe("BN");
  expect(Object.keys(startedLineup())).toHaveLength(9);
});

// Suspected bug: the locked starter's slot is still handed out, so two players start at PG (10 starters)
test.failing("fills the other 8 slots around a locked starter, and leaves a locked bench player benched", async () => {
  loadLineupPage();
  givePlayerGame("Josh Giddey", "LAL");
  givePlayerGame("Darius Garland", "@MIA");
  givePlayerGame("Miles Bridges", "LAL");
  givePlayerGame("Jakob Poeltl", "CHI");
  // Games already tipped: Cunningham is locked in at PG, Giddey (who would otherwise start) on the bench
  lockPlayer("Cade Cunningham");
  lockPlayer("Josh Giddey");

  const problems = await setLineupAndCollectProblems();

  expect(problems).toEqual([]);
  expect(slotOf("Cade Cunningham")).toBe("PG (locked)");
  expect(slotOf("Josh Giddey")).toBe("BN (locked)");
  expect(Object.values(startedLineup()).sort()).toEqual([
    "ANY", "ANY", "C", "F/C", "G", "PF", "PG (locked)", "SF", "SG",
  ]);
});

// Suspected bug: F/C goes unfilled (8 starters) and nothing is reported
test.failing("when the page's slot options don't match the league's slots, never leaves a slot silently empty", async () => {
  // e.g. Fleaflicker relabels the F/C option
  loadLineupPage({ optionText: (slot) => (slot === "F/C" ? "FC" : slot) });
  givePlayerGame("Josh Giddey", "LAL");
  givePlayerGame("Miles Bridges", "LAL");
  givePlayerGame("Jakob Poeltl", "CHI");

  const problems = await setLineupAndCollectProblems();

  const allNineStarted = Object.keys(startedLineup()).length === 9;
  expect({ allNineStarted, problemReported: problems.length > 0 }).not.toEqual({
    allNineStarted: false,
    problemReported: false,
  });
});

test("off the fantasy stats view, reports it and leaves the lineup untouched", async () => {
  loadLineupPage();
  document.querySelector<HTMLAnchorElement>("a.dropdown-toggle")!.firstChild!.textContent = "season stats ";
  givePlayerGame("Josh Giddey", "LAL");
  givePlayerGame("Miles Bridges", "LAL");
  givePlayerGame("Jakob Poeltl", "CHI");
  const lineupBefore = startedLineup();

  const problems = await setLineupAndCollectProblems();

  expect(problems).toMatchInlineSnapshot(`
    [
      "Not on the fantasy stats page; aborting",
    ]
  `);
  expect(startedLineup()).toEqual(lineupBefore);
});
