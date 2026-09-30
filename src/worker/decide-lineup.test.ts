import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import fantasyStatsPage from "../lineup/fixtures/teampage-logged-in-fantasy-stats.html?raw";
import loggedOutPage from "../lineup/fixtures/teampage.html?raw";
import seasonStatsPage from "../lineup/fixtures/teampage-logged-in.html?raw";
import { decideLineup } from "./decide-lineup";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-10-20T14:00:00Z"));
});
afterEach(() => vi.useRealTimers());

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

  it("refuses a page that isn't the fantasy stats view", async () => {
    const decision = await decideLineup(seasonStatsPage);

    expect(decision).toEqual({ ok: false, errors: ["Not on the fantasy stats page; aborting"] });
  });

  it("refuses a logged-out page, which has no lineup form", async () => {
    const decision = await decideLineup(loggedOutPage);

    expect(decision).toEqual({ ok: false, errors: ["No lineup form on the page; the session may be logged out"] });
  });
});
