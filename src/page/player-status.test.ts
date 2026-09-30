import { afterEach, expect, setSystemTime, test } from "bun:test";
import type { TimeAgo } from "../types";
import { parsePlayerNews } from "./player-status";

// Inputs mirror what the page's tooltip data yields for a news item: tags stripped, so the
// headline, the timestamp (e.g. "Wed 9/30/26 9:05 AM", Eastern) and the body run together, and
// no separate timestamp text is passed. Shape copied from the saved page's real news tooltips.
function newsTooltipText(headline: string, timestamp: string, body: string) {
  return `${headline}${timestamp}${body} rotoballer.com`;
}

function ageInHours(timeAgo: TimeAgo | undefined) {
  if (!timeAgo) return undefined;
  const hoursPerUnit = { minutes: 1 / 60, hours: 1, days: 24 };
  return timeAgo.value * hoursPerUnit[timeAgo.unit];
}

afterEach(() => setSystemTime());

test.each([
  ["Jalen Suggs (ankle) is listed as questionable for Tuesday's game against Boston.", "Q"],
  ["Suggs (ankle) is doubtful for Tuesday's matchup with the Celtics.", "D"],
  ["Suggs (ankle) is probable for Tuesday's game against Boston.", "P"],
  ["Suggs (ankle) has been ruled out for Tuesday's game against Boston.", "OUT"],
])("reads the status from the news text: %s", (body, status) => {
  const news = newsTooltipText("Jalen Suggs Injury Update", "Mon 10/19/26 5:12 PM", body);

  expect(parsePlayerNews(news, undefined)?.injuryStatus).toBe(status);
});

test("a player who fouled out isn't read as ruled out", () => {
  const news = newsTooltipText(
    "Suggs Scores 18 in Loss",
    "Mon 10/19/26 11:02 PM",
    "Jalen Suggs fouled out of Monday's loss to Boston after 24 minutes."
  );

  expect(parsePlayerNews(news, undefined)?.injuryStatus).toBeUndefined();
});

test("an earlier 'sat out' doesn't override the news' current status", () => {
  const news = newsTooltipText(
    "Suggs Misses Practice",
    "Mon 10/19/26 5:12 PM",
    "Jalen Suggs (ankle) sat out Monday's practice but is listed as probable for Tuesday's game against Boston."
  );

  expect(parsePlayerNews(news, undefined)?.injuryStatus).toBe("P");
});

// The tooltip text glues the headline to the timestamp ("ProbableMon 10/19/26")
test("reads a status that only appears at the end of the headline", () => {
  const news = newsTooltipText(
    "Jalen Suggs Probable",
    "Mon 10/19/26 5:12 PM",
    "Jalen Suggs (ankle) is expected to play Tuesday against Boston, per coach Jamahl Mosley."
  );

  expect(parsePlayerNews(news, undefined)?.injuryStatus).toBe("P");
});

test("reads the news age from the page's timestamp", () => {
  setSystemTime(new Date("2026-09-30T19:37:00Z")); // Wed 9/30 3:37p ET
  const news = newsTooltipText(
    "Jalen Suggs Questionable",
    "Mon 9/28/26 9:37 AM",
    "Jalen Suggs (ankle) is questionable for Wednesday's preseason game against Miami."
  );

  const age = ageInHours(parsePlayerNews(news, undefined)?.timeAgo);

  expect(age).toBeGreaterThanOrEqual(48);
  expect(age).toBeLessThan(72);
});

test("reads a singular news age ('1 hour ago') the same as a plural one", () => {
  const result = parsePlayerNews("Jalen Suggs (ankle) has been ruled out Tuesday.", "1 hour ago");

  expect(result?.timeAgo).toEqual({ value: 1, unit: "hours" });
});
