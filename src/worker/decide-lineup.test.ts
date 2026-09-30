import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import fantasyStatsPage from "../lineup/fixtures/teampage-logged-in-fantasy-stats.html?raw";
import loggedOutPage from "../lineup/fixtures/teampage.html?raw";
import seasonStatsPage from "../lineup/fixtures/teampage-logged-in.html?raw";
import signedInRoster from "../lineup/fixtures/fetch-roster-week1-signed-in.json";
import { type ApiRoster, decideLineup } from "./decide-lineup";

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

  it("lists who moves from the page's current lineup, for the run log", async () => {
    const decision = await decideLineup(fantasyStatsPage);

    if (!decision.ok) throw new Error(decision.errors.join("\n"));
    expect(decision.changes).toMatchInlineSnapshot(`
      [
        {
          "from": "C",
          "player": "Naz Reid",
          "to": "Bench",
        },
        {
          "from": "F/C",
          "player": "John Collins",
          "to": "C",
        },
        {
          "from": "ANY",
          "player": "Neemias Queta",
          "to": "F/C",
        },
        {
          "from": "Bench",
          "player": "Josh Giddey",
          "to": "ANY",
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

  // Guessed locked-row markup (no select, the slot as a label), as the logged-out page shows every row. The cross-check against the API roster catches a wrong guess
  it("refuses a lineup that also starts someone in a locked starter's slot", async () => {
    const pageWithCadeLockedAtPG = fantasyStatsPage.replace(
      /<select class="form-control" name="status2147">.*?<\/select>/,
      '<span class="label label-success label-block"><span class="position">PG</span></span>',
    );

    const decision = await decideLineup(pageWithCadeLockedAtPG);

    expect(decision).toEqual({ ok: false, errors: [expect.stringContaining("PG slot is over-filled")] });
  });

  it("refuses a lineup where a player's select has no Bench option to fall back to", async () => {
    const pageWithoutPostBench = fantasyStatsPage.replace(
      '<select class="form-control" name="status2619"><option value="16">C</option><option value="28">F/C</option><option value="31">ANY</option><option value="0" selected="selected">Bench</option></select>',
      '<select class="form-control" name="status2619"><option value="16">C</option><option value="28">F/C</option><option value="31">ANY</option></select>',
    );

    const decision = await decideLineup(pageWithoutPostBench);

    expect(decision).toEqual({ ok: false, errors: ["Quinten Post has no slot chosen"] });
  });

  it("refuses a page whose starting slots it can't read, since it can't check the lineup", async () => {
    const pageWithoutSlots = fantasyStatsPage.replace('"allPositions"', '"renamedPositions"');

    const decision = await decideLineup(pageWithoutSlots);

    expect(decision).toEqual({ ok: false, errors: ["No starting slots (allPositions) in the page data; can't check the lineup"] });
  });

  it("has nothing to warn about on a page with all its data", async () => {
    const decision = await decideLineup(fantasyStatsPage);

    expect(decision).toMatchObject({ ok: true, warnings: [] });
  });

  it("still sets the lineup when the page has no matchups, and warns about it", async () => {
    const pageWithoutTooltips = fantasyStatsPage.replace('"tooltips":[', '"tooltips":[],"renamedTooltips":[');
    await decideLineup(fantasyStatsPage);

    const decision = await decideLineup(pageWithoutTooltips);

    expect(decision).toMatchObject({ ok: true, warnings: expect.arrayContaining([expect.stringContaining("Cade Cunningham")]) });
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
      const roster: ApiRoster = structuredClone(signedInRoster);
      roster.groups[1]!.slots.push({ position: { label: "BN" }, leaguePlayer: { proPlayer: { id: 999999, nameFull: "Just Signed" }, eligibleFor: [{ label: "BN" }] } });

      const decision = await decideLineup(fantasyStatsPage, roster);

      expect(decision).toEqual({ ok: false, errors: [expect.stringMatching(/page and API disagree.*Just Signed/i)] });
    });
  
    it("refuses when a player's slot choices on the page don't match his API eligibility", async () => {
      const pageMissingQuetaFC = fantasyStatsPage.replace(
        '<select class="form-control" name="status2168"><option value="16">C</option><option value="28">F/C</option>',
        '<select class="form-control" name="status2168"><option value="16">C</option>',
      );

      const decision = await decideLineup(pageMissingQuetaFC, signedInRoster);

      expect(decision).toEqual({ ok: false, errors: [expect.stringMatching(/page and API disagree.*Neemias Queta.*F\/C/i)] });
    });
  
    it("refuses when the page and the API roster have a player in different slots", async () => {
      const pageWithQuetaOnBench = fantasyStatsPage.replace(
        '<option value="31" selected="selected">ANY</option><option value="0">Bench</option></select></td></tr><tr class="last">',
        '<option value="31">ANY</option><option value="0" selected="selected">Bench</option></select></td></tr><tr class="last">',
      );

      const decision = await decideLineup(pageWithQuetaOnBench, signedInRoster);

      expect(decision).toEqual({ ok: false, errors: [expect.stringMatching(/page and API disagree.*Neemias Queta is in BN on the page but ANY/i)] });
    });
  
    it("counts a locked player (no select) as on the page", async () => {
      const pageWithPostLockedOnBench = fantasyStatsPage.replace(
        /<select class="form-control" name="status2619">.*?<\/select>/,
        '<span class="label label-danger label-block"><span class="text-muted">BN</span></span>',
      );

      const decision = await decideLineup(pageWithPostLockedOnBench, signedInRoster);

      expect(decision.ok).toBe(true);
    });

    it("refuses when a locked player's slot on the page doesn't match the API roster", async () => {
      const pageWithPostLockedAtC = fantasyStatsPage.replace(
        /<select class="form-control" name="status2619">.*?<\/select>/,
        '<span class="label label-success label-block"><span class="position">C</span></span>',
      );

      const decision = await decideLineup(pageWithPostLockedAtC, signedInRoster);

      expect(decision).toEqual({ ok: false, errors: ["Page and API disagree: Quinten Post (locked) is in C on the page but BN in the API"] });
    });

    it("refuses an API roster for a different day than the page", async () => {
      const nextDayRoster = { ...signedInRoster, lineupPeriod: { ...signedInRoster.lineupPeriod, ordinal: 2 } };

      const decision = await decideLineup(fantasyStatsPage, nextDayRoster);

      expect(decision).toEqual({ ok: false, errors: ["Page and API disagree: the page is day 1 but the API roster is day 2"] });
    });
  });
});
