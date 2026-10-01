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

  it.each([
    "Giddey has been ruled out for the Oct. 20 game vs. the Bulls.",
    "Giddey has been ruled out for the Oct 20th game against the Bulls.",
    "Giddey has been ruled out for the October 20 game against the Bulls.",
    "Giddey has been ruled out for the 10/20 game against the Bulls.",
  ])("reads the tip's date as the tip's game: %s", (sentence) => {
    const news = { headline: "Josh Giddey Injury Update", body: `Giddey tweaked his ankle at practice. ${sentence} He'll be re-evaluated next week.`, postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)).toEqual({ status: "OUT", sentence });
  });

  it.each(["Giddey has been ruled out for the Oct. 19 game.", "Giddey has been ruled out for the 10/19 game.", "Giddey has been ruled out for the Oct. 2 game."])(
    "ignores another date: %s",
    (body) => {
      const news = { headline: "Josh Giddey Injury Update", body, postedAt: mondayAfternoon };

      expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
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

  it.each(["Giddey will be out for Tuesday's game.", "Giddey will be out against the Bulls on Tuesday."])(
    "reads out for/against the tip's game as OUT: %s",
    (body) => {
      const news = { headline: "Josh Giddey Injury Update", body, postedAt: mondayAfternoon };

      expect(matchOutNews(news, tuesdayTip)?.status).toBe("OUT");
    },
  );

  it.each([
    "Giddey closed out the win with a pair of free throws Tuesday.",
    "Giddey closed out Tuesday's shootaround with extra conditioning work.",
    "Giddey sat out Tuesday's shootaround but is expected to play.",
    "Giddey sits out for Tuesday's walkthrough as a precaution.",
    "Giddey fouled out against the Bulls on Tuesday.",
    "Giddey moved out of the starting lineup Tuesday and played 28 minutes.",
  ])("ignores other meanings of out: %s", (body) => {
    const news = { headline: "Josh Giddey Injury Update", body, postedAt: "2026-10-20T14:00:00Z" };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it("ignores a player out of his walking boot", () => {
    const news = { headline: "Josh Giddey Injury Update", body: "Giddey is out of his walking boot, expected to play Friday.", postedAt: "2026-10-23T14:00:00Z" };

    expect(matchOutNews(news, "2026-10-23T23:30:00Z")).toBeUndefined();
  });

  it("ignores out for a day more than four words away", () => {
    const news = { headline: "Josh Giddey Injury Update", body: "Giddey was out for a long stretch of last season but returns Tuesday.", postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it("reads doubtful for the tip's game as D", () => {
    const news = { headline: "Josh Giddey Injury Update", body: "Giddey is doubtful for Wednesday's game against the Bulls.", postedAt: "2026-10-20T18:00:00Z" };

    expect(matchOutNews(news, "2026-10-21T23:30:00Z")).toEqual({ status: "D", sentence: "Giddey is doubtful for Wednesday's game against the Bulls." });
  });

  it("reads OUT over D when one sentence says both", () => {
    const news = { headline: "Josh Giddey Injury Update", body: "Giddey was doubtful but has been ruled out for Tuesday.", postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)?.status).toBe("OUT");
  });

  it("ignores doubtful for a game on another day", () => {
    const news = { headline: "Josh Giddey Injury Update", body: "Giddey is doubtful for Monday's game.", postedAt: "2026-10-19T12:00:00Z" };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it.each(["Josh Giddey Out Tue.", "Josh Giddey Out Tues. vs. Bulls"])("reads an abbreviated tip weekday: %s", (headline) => {
    const news = { headline, body: "", postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)?.status).toBe("OUT");
  });

  it("ignores an abbreviated other weekday", () => {
    const news = { headline: "Josh Giddey Ruled Out Mon., Questionable Tue.", body: "", postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it.each([
    "Giddey could be ruled out for Tuesday's game.",
    "Giddey might not play Tuesday.",
    "Giddey may be ruled out Tuesday if the swelling persists.",
    "Giddey won't play Tuesday unless his ankle loosens up.",
    "Giddey is likely to be ruled out for Tuesday's game.",
    "Giddey was upgraded from doubtful to questionable for Tuesday's game.",
  ])("ignores a hedged status: %s", (body) => {
    const news = { headline: "Josh Giddey Injury Update", body, postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it.each([
    "With LaMelo Ball (ankle) ruled out for Tuesday's game, Giddey will run the offense.",
    "Ball has been ruled out for Tuesday's game, so Giddey should see more minutes.",
    "Giddey will start Tuesday in place of Ball, who has been ruled out.",
    "Giddey will see extra usage Tuesday in the absence of Ball, who won't play.",
  ])("ignores a teammate's absence that only affects the player: %s", (body) => {
    const news = { headline: "Josh Giddey Injury Update", body, postedAt: mondayAfternoon };

    expect(matchOutNews(news, tuesdayTip)).toBeUndefined();
  });

  it.each(["...", "…"])("ignores a body sentence cut off with %s, since the cut text may reverse it", (ellipsis) => {
    const news = {
      headline: "Josh Giddey Injury Update",
      body: `Giddey went through shootaround. He has been ruled out for Tuesday's game, though the Bulls have since reversed cou${ellipsis}`,
      postedAt: mondayAfternoon,
    };

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
