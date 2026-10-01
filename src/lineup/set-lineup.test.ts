import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, afterEach, beforeAll, beforeEach, expect, setSystemTime, spyOn, test } from "bun:test";
import {
  giveInjuryTag,
  givePlayerGame,
  givePlayerNews,
  loadLineupPage,
  lockPlayer,
  PAGE_URL,
  playerRow,
  playerRows,
  showStatView,
  slotOf,
  startedLineup,
} from "./fixtures/lineup-page";
import { setProblemHandler } from "./report-problem";

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
  for (const method of ["log", "table", "clear", "warn", "error"] as const) {
    spyOn(console, method).mockImplementation(() => {});
  }
  spyOn(window, "alert").mockImplementation((message) => void alerts.push(String(message)));
  // Bun shares modules across test files, so a content script run elsewhere may have routed problems to the page
  setProblemHandler((message) => void alerts.push(message));
});
afterEach(() => setSystemTime());

// A rejection is the only failure signal a headless run sees; `alerts` is what a person at the page sees
async function setLineupAndGetRejection() {
  const { setLineup } = await import("./set-lineup");
  return setLineup().then(
    () => undefined,
    (error) => String(error),
  );
}

test("on the real opening-night page, starts all 8 players who have a game and fills the 9th slot", async () => {
  loadLineupPage();
  for (const select of document.querySelectorAll("select")) select.value = "0";

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(alerts).toEqual([]);
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

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(alerts).toEqual([]);
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

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(alerts).toEqual([]);
  expect(slotOf("Adem Bona")).toBe("Bench");
  expect(slotOf("Mark Williams")).toBe("Bench");
  expect(Object.keys(startedLineup())).toHaveLength(9);
});

test("fills the other 8 slots around a locked starter, and leaves a locked bench player benched", async () => {
  loadLineupPage();
  givePlayerGame("Josh Giddey", "LAL");
  givePlayerGame("Darius Garland", "@MIA");
  givePlayerGame("Miles Bridges", "LAL");
  givePlayerGame("Jakob Poeltl", "CHI");
  // Games already tipped: Cunningham is locked in at PG, Giddey (who would otherwise start) on the bench
  lockPlayer("Cade Cunningham");
  lockPlayer("Josh Giddey");

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(alerts).toEqual([]);
  expect(slotOf("Cade Cunningham")).toBe("PG (locked)");
  expect(slotOf("Josh Giddey")).toBe("BN (locked)");
  expect(Object.values(startedLineup()).sort()).toEqual([
    "ANY", "ANY", "C", "F/C", "G", "PF", "PG (locked)", "SF", "SG",
  ]);
});

test("once every starter's game has tipped, changes nothing", async () => {
  loadLineupPage();
  const lockedLineup = startedLineup();
  for (const name of Object.keys(lockedLineup)) lockPlayer(name);

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(startedLineup()).toEqual(
    Object.fromEntries(Object.entries(lockedLineup).map(([name, slot]) => [name, `${slot} (locked)`])),
  );
});

test("a day-to-day starter sits tonight when 9 healthy players have a game", async () => {
  loadLineupPage();
  giveInjuryTag("Cade Cunningham", "DTD");
  for (const name of ["Josh Giddey", "Darius Garland", "Desmond Bane", "Coby White", "Miles Bridges", "Jabari Smith", "Naz Reid"]) {
    givePlayerGame(name, "LAL");
  }

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(slotOf("Cade Cunningham")).toBe("Bench");
  expect(Object.keys(startedLineup())).toHaveLength(9);
});

test("viewing a day several days out, a day-to-day tag alone doesn't keep a player out of the lineup", async () => {
  // Viewing Tue 10/20 (the page's day) from Thu 10/15
  setSystemTime(new Date("2026-10-15T14:00:00Z"));
  loadLineupPage();
  giveInjuryTag("Cade Cunningham", "DTD");
  for (const name of ["Josh Giddey", "Darius Garland", "Desmond Bane", "Coby White", "Miles Bridges", "Jabari Smith", "Naz Reid"]) {
    givePlayerGame(name, "LAL");
  }

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(slotOf("Cade Cunningham")).not.toBe("Bench");
  expect(Object.keys(startedLineup())).toHaveLength(9);
});

test("a day-to-day star still starts over a much weaker healthy player", async () => {
  loadLineupPage();
  giveInjuryTag("Cade Cunningham", "DTD");
  givePlayerGame("Tyus Jones", "LAL");
  givePlayerGame("Jalen Green", "LAL");
  givePlayerGame("Keon Ellis", "LAL");

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(slotOf("Cade Cunningham")).not.toBe("Bench");
  expect(slotOf("Tyus Jones")).toBe("Bench");
});

test("benches a day-to-day player whose latest news rules him out tonight", async () => {
  loadLineupPage();
  giveInjuryTag("Cade Cunningham", "DTD");
  givePlayerNews(
    "Cade Cunningham",
    '<h5>Cade Cunningham Ruled Out Tuesday</h5><em><relative-time datetime="2026-10-20T13:05:00Z">Tue 10/20/26 9:05 AM</relative-time></em>' +
      "<p>Pistons guard Cade Cunningham (hamstring) has been ruled out for Tuesday's game against Boston.</p>",
  );
  givePlayerGame("Tyus Jones", "LAL");
  givePlayerGame("Jalen Green", "LAL");
  givePlayerGame("Keon Ellis", "LAL");

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(slotOf("Cade Cunningham")).toBe("Bench");
  expect(slotOf("Tyus Jones")).not.toBe("Bench");
});

test("with fewer players than slots, starts everyone and leaves the rest of the slots empty", async () => {
  loadLineupPage();
  const roster = ["Cade Cunningham", "Anfernee Simons", "Devin Vassell", "Adem Bona", "Naz Reid", "Josh Giddey", "Jalen Suggs"];
  for (const row of playerRows()) {
    if (!roster.includes(row.querySelector(".player-text")!.textContent!)) row.remove();
  }

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(alerts).toEqual([]);
  expect(Object.keys(startedLineup()).sort()).toEqual([...roster].sort());
});

test("with no center-eligible player on the roster, leaves C empty and fills the other 8 slots", async () => {
  loadLineupPage();
  for (const row of playerRows()) {
    if (row.querySelector(".position")!.getAttribute("title")!.includes("Center")) row.remove();
  }

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(alerts).toEqual([]);
  expect(Object.values(startedLineup()).sort()).toEqual(["ANY", "ANY", "F/C", "G", "PF", "PG", "SF", "SG"]);
});

test("a player with no projection and unreadable stats is still scored, and starts over players without a game", async () => {
  loadLineupPage();
  const row = playerRow("Josh Giddey");
  row.querySelector(".player-text")!.textContent = "Unknown Rookie";
  for (const stat of row.querySelectorAll(".fp")) stat.textContent = "—";
  givePlayerGame("Unknown Rookie", "LAL");

  expect(await setLineupAndGetRejection()).toBeUndefined();
  expect(alerts).toEqual([]);
  expect(slotOf("Unknown Rookie")).not.toBe("Bench");
  expect(Object.keys(startedLineup())).toHaveLength(9);
});

test("when the page's slot options don't match the league's slots, fills every slot or rejects", async () => {
  // e.g. Fleaflicker relabels the F/C option
  loadLineupPage({ optionText: (slot) => (slot === "F/C" ? "FC" : slot) });
  givePlayerGame("Josh Giddey", "LAL");
  givePlayerGame("Miles Bridges", "LAL");
  givePlayerGame("Jakob Poeltl", "CHI");

  const rejection = await setLineupAndGetRejection();

  if (rejection === undefined) expect(Object.keys(startedLineup())).toHaveLength(9);
});

test("off the fantasy stats view, says so and leaves the lineup untouched", async () => {
  loadLineupPage();
  showStatView("season stats");
  givePlayerGame("Josh Giddey", "LAL");
  givePlayerGame("Miles Bridges", "LAL");
  givePlayerGame("Jakob Poeltl", "CHI");
  const lineupBefore = startedLineup();

  const rejection = await setLineupAndGetRejection();

  expect([...alerts, rejection].filter(Boolean)).toMatchInlineSnapshot(`
    [
      "Error: Not on the fantasy stats page; aborting",
    ]
  `);
  expect(startedLineup()).toEqual(lineupBefore);
});

test("off the fantasy stats view, rejects", async () => {
  loadLineupPage();
  showStatView("season stats");

  expect(await setLineupAndGetRejection()).toMatch(/fantasy stats/i);
});

test("when logged out, rejects", async () => {
  loadLineupPage({ loggedIn: false });
  givePlayerGame("Josh Giddey", "LAL");

  expect(await setLineupAndGetRejection()).toBeDefined();
});

test("when the viewed day can't be read off the page, rejects", async () => {
  loadLineupPage();
  for (const button of document.querySelectorAll("a.btn[data-toggle='dropdown']")) {
    if (button.textContent!.includes("10/20")) button.remove();
  }

  expect(await setLineupAndGetRejection()).toMatch(/date/);
});

test("when the viewed day can't be read off the page, leaves the lineup as it was", async () => {
  loadLineupPage();
  for (const button of document.querySelectorAll("a.btn[data-toggle='dropdown']")) {
    if (button.textContent!.includes("10/20")) button.remove();
  }
  const lineupBefore = startedLineup();

  await setLineupAndGetRejection();

  expect(startedLineup()).toEqual(lineupBefore);
});
