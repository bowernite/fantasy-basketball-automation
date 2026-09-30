import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import fantasyStatsPage from "../lineup/fixtures/teampage-logged-in-fantasy-stats.html?raw";
import loggedOutPage from "../lineup/fixtures/teampage.html?raw";
import seasonStatsPage from "../lineup/fixtures/teampage-logged-in.html?raw";
import signedInRoster from "../lineup/fixtures/fetch-roster-week1-signed-in.json";
import { decideLineup } from "./decide-lineup";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-10-20T14:00:00Z"));
});
afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("decideLineup", () => {
  it("fills all 9 starting slots and returns the whole lineup form as a POST body", async () => {
    const decision = await decideLineup(fantasyStatsPage);

    if (!decision.ok) throw new Error(decision.errors.join("\n"));
    expect(decision.formAction).toBe("/nba/leagues/30579/teams/161025");
    const form = new URLSearchParams(decision.body);
    expect(form.get("teamId")).toBe("161025");
    expect(form.get("week")).toBe("1");
    const statuses = [...form].filter(([name]) => name.startsWith("status"));
    expect(statuses).toHaveLength(38);
    const starterSlots = statuses.map(([, value]) => value).filter((value) => value !== "0");
    expect(starterSlots.sort()).toEqual(["1", "16", "2", "28", "3", "31", "31", "4", "8"]);
  });

  it("lists who starts where, for the run log", async () => {
    const decision = await decideLineup(fantasyStatsPage);

    if (!decision.ok) throw new Error(decision.errors.join("\n"));
    expect(decision.starters).toMatchInlineSnapshot(`
      [
        {
          "player": "Cade Cunningham",
          "slot": "PG",
        },
        {
          "player": "Anfernee Simons",
          "slot": "SG",
        },
        {
          "player": "De'Aaron Fox",
          "slot": "G",
        },
        {
          "player": "Devin Vassell",
          "slot": "SF",
        },
        {
          "player": "Adem Bona",
          "slot": "PF",
        },
        {
          "player": "John Collins",
          "slot": "C",
        },
        {
          "player": "Neemias Queta",
          "slot": "F/C",
        },
        {
          "player": "Andre Drummond",
          "slot": "ANY",
        },
        {
          "player": "Josh Giddey",
          "slot": "ANY",
        },
      ]
    `);
  });

  it("keeps the extension's debug output (whole player objects) out of the Worker logs", async () => {
    const debugOutput = [vi.spyOn(console, "log"), vi.spyOn(console, "table"), vi.spyOn(console, "clear")];

    await decideLineup(fantasyStatsPage);

    for (const spy of debugOutput) expect(spy).not.toHaveBeenCalled();
  });

  it("refuses a lineup that leaves a starting slot empty while an eligible player sits on the bench", async () => {
    const pageWithRenamedSlot = fantasyStatsPage.replaceAll(">F/C</option>", ">FC</option>");

    const decision = await decideLineup(pageWithRenamedSlot);

    expect(decision).toEqual({ ok: false, errors: [expect.stringContaining("F/C slot is empty")] });
  });

  it("refuses a page whose starting slots it can't read, since it can't check the lineup", async () => {
    const pageWithoutSlots = fantasyStatsPage.replace('"allPositions"', '"renamedPositions"');

    const decision = await decideLineup(pageWithoutSlots);

    expect(decision).toEqual({ ok: false, errors: ["No starting slots (allPositions) in the page data; can't check the lineup"] });
  });

  it("never reuses an earlier page's player news and matchups", async () => {
    const pageWithoutTooltips = fantasyStatsPage.replace('"tooltips":[', '"tooltips":[],"renamedTooltips":[');
    await decideLineup(fantasyStatsPage);

    const decision = await decideLineup(pageWithoutTooltips);

    expect(decision.ok).toBe(false);
  });

  it("refuses a page that isn't the fantasy stats view", async () => {
    const decision = await decideLineup(seasonStatsPage);

    expect(decision).toEqual({ ok: false, errors: ["Not on the fantasy stats page; aborting"] });
  });

  it("refuses a logged-out page, which has no lineup form", async () => {
    const decision = await decideLineup(loggedOutPage);

    expect(decision).toEqual({ ok: false, errors: ["No lineup form on the page; the session may be logged out"] });
  });

  describe("cross-checked against the signed-in API roster for the same day", () => {
    it("goes ahead when the page and the API roster agree", async () => {
      const decision = await decideLineup(fantasyStatsPage, signedInRoster);

      expect(decision.ok).toBe(true);
    });

    it("refuses when the page has a player the API roster doesn't", async () => {
      const roster = structuredClone(signedInRoster);
      const postSlot = roster.groups[1]!.slots.find((slot) => slot.leaguePlayer?.proPlayer.nameFull === "Quinten Post")!;
      delete (postSlot as { leaguePlayer?: unknown }).leaguePlayer;

      const decision = await decideLineup(fantasyStatsPage, roster);

      expect(decision).toEqual({ ok: false, errors: [expect.stringMatching(/page and API disagree.*Quinten Post/i)] });
    });
  
    it("refuses when the API roster has a player the page doesn't", async () => {
      const roster = structuredClone(signedInRoster);
      const benchSlots = roster.groups[1]!.slots;
      const newPlayer = { ...benchSlots[0]!.leaguePlayer!, proPlayer: { ...benchSlots[0]!.leaguePlayer!.proPlayer, id: 999999, nameFull: "Just Signed" } };
      benchSlots.push({ ...benchSlots[0]!, leaguePlayer: newPlayer });

      const decision = await decideLineup(fantasyStatsPage, roster);

      expect(decision).toEqual({ ok: false, errors: [expect.stringMatching(/page and API disagree.*Just Signed/i)] });
    });
  });
});
