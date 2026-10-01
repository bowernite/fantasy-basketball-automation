import { describe, expect, it } from "vitest";
import { matchOutNews } from "./untagged-out-match";

// Tue Oct 20, 7:30p ET
const tuesdayTip = "2026-10-20T23:30:00Z";
// Mon Oct 19, 2p ET
const mondayAfternoon = "2026-10-19T18:00:00Z";

describe("matchOutNews", () => {
  it("reads a headline saying the player is out on the tip's weekday as OUT", () => {
    const news = { headline: "Josh Giddey Out Tuesday", body: "", postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)).toEqual({ status: "OUT", sentence: "Josh Giddey Out Tuesday" });
  });

  it("reads a body sentence ruling the player out of the tip's game as OUT", () => {
    const news = {
      headline: "Josh Giddey Injury Update",
      body: "Giddey (ankle) went through shootaround. Giddey has been ruled out for Tuesday's game against the Bulls. He'll be re-evaluated later this week.",
      postedAt: mondayAfternoon,
    };

    expect(matchOutNews(news, tuesdayTip)).toEqual({ status: "OUT", sentence: "Giddey has been ruled out for Tuesday's game against the Bulls." });
  });

  it("ignores a player ruled out of a game on another day", () => {
    const news = { headline: "Josh Giddey Injury Update", body: "Giddey was ruled out of Monday's game against the Bulls.", postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it("ignores a sentence that also names another day, since the status may belong to it", () => {
    const news = {
      headline: "Josh Giddey Injury Update",
      body: "Giddey was ruled out of Monday's game against the Bulls and is questionable for Tuesday.",
      postedAt: mondayAfternoon,
    };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it.each([
    "Giddey hasn't been ruled out for Tuesday's game.",
    "Giddey has not been ruled out for Tuesday's game.",
    "Giddey was never ruled out for Tuesday’s game.",
    "Giddey is no longer ruled out for Tuesday's game.",
  ])("ignores a negated ruling out: %s", (body) => {
    const news = { headline: "Josh Giddey Injury Update", body, postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it.each(["Giddey won't play tonight against the Bulls.", "Giddey will not play today."])(
    "reads tonight/today in news posted on tip day as the tip's game: %s",
    (body) => {
      const news = { headline: "Josh Giddey Injury Update", body, postedAt: "2026-10-20T18:00:00Z" };

      expect(matchOutNews(news, tuesdayTip)).toEqual({ status: "OUT", sentence: body });
    },
  );

  it("ignores tonight in news posted the day before tip", () => {
    const news = { headline: "Josh Giddey Injury Update", body: "Giddey won't play tonight against the Bulls.", postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it("ignores tonight in news posted before the 6a ET day boundary on tip day", () => {
    const news = { headline: "Josh Giddey Injury Update", body: "Giddey won't play tonight against the Bulls.", postedAt: "2026-10-20T09:30:00Z" };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it("reads tomorrow in news posted the day before tip as the tip's game", () => {
    const news = { headline: "Josh Giddey Injury Update", body: "Giddey won't play tomorrow against the Bulls.", postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)?.status).toBe("OUT");
  });

  it("ignores tomorrow in news posted on tip day", () => {
    const news = { headline: "Josh Giddey Injury Update", body: "Giddey won't play tomorrow against the Bulls.", postedAt: "2026-10-20T18:00:00Z" };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it("ignores news posted more than 36 h before tip", () => {
    const news = { headline: "Josh Giddey Out Tuesday", body: "", postedAt: "2026-10-19T11:29:00Z" };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it("ignores news posted after tip", () => {
    const news = { headline: "Josh Giddey Out Tuesday", body: "", postedAt: "2026-10-20T23:31:00Z" };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });
});
