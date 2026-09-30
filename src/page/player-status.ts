import { PLAYER_STATUS_SELECTOR } from "./page-querying";
import { getTooltipContent } from "./tooltip";
import { getTooltipContentFromPageData } from "./page-data";
import { easternTimeToDate, parseYearFromSuffix } from "../utils/date-utils";
import type { PlayerStatus, TimeAgo } from "../types";

// As shown on news items, in US Eastern, e.g. "Mon 9/28/26 9:37 AM"
const NEWS_TIMESTAMP = /(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{1,2})\/(\d{1,2})\/(\d{2}) (\d{1,2}):(\d{2}) ([AP])M/;

export function getPlayerStatusFromRow(
  row: HTMLTableRowElement
): PlayerStatus {
  const statusText = row
    .querySelector(PLAYER_STATUS_SELECTOR)
    ?.textContent?.split(" ")[0];
  return (statusText as PlayerStatus) || "(active)";
}

export function getPlayerNewsFromPageData(
  newsTrigger: Element
): { news: string; newsElement: Element } | undefined {
  const tooltipContent = getTooltipContentFromPageData(newsTrigger);

  if (tooltipContent?.fullString) {
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = tooltipContent.fullString;
    return {
      news: tooltipContent.fullString,
      newsElement: tempDiv,
    };
  }

  return undefined;
}

export async function getPlayerNewsFromDOM(
  newsTrigger: Element
): Promise<{ news: string | undefined; newsElement: Element | undefined }> {
  const domContent = await getTooltipContent(newsTrigger);
  return {
    news: domContent.fullString ?? undefined,
    newsElement: domContent.element ?? undefined,
  };
}

export function parsePlayerNews(
  news: string,
  timeAgoString: string | null | undefined
):
  | { injuryStatus: PlayerStatus; timeAgo: TimeAgo | undefined }
  | undefined {
  const injuryStatusMatch = news.replace(NEWS_TIMESTAMP, " ").match(
    // "fouled out" / "sat out" describe a past game or practice, not a status
    /\b(?<!(?:fouled|sat|sits)\s+)(questionable|doubtful|probable|not available|will not play|won't play|available|will play|(?<!not\s+(?:be\s+)?a\s+)full go|(?<!(?:not|n't)\s+(?:been\s+)?)cleared to (?:play|return)|out)\b/i
  );
  const rawStatus = injuryStatusMatch?.[1]?.toLowerCase();
  const injuryStatus: PlayerStatus | undefined =
    rawStatus === "available" || rawStatus === "will play" || rawStatus === "full go" || rawStatus?.startsWith("cleared to")
      ? "(active)"
      : rawStatus === "not available" || rawStatus === "will not play" || rawStatus === "won't play"
      ? "OUT"
      : rawStatus === "questionable"
      ? "Q"
      : rawStatus === "doubtful"
      ? "D"
      : rawStatus === "probable"
      ? "P"
      : rawStatus === "out"
      ? "OUT"
      : undefined;

  if (injuryStatus === undefined) return undefined;

  let timeAgo: TimeAgo | undefined;
  if (timeAgoString?.toLowerCase().includes("yesterday")) {
    timeAgo = {
      value: 16,
      unit: "hours",
    };
  } else if (timeAgoString?.toLowerCase().includes("today")) {
    timeAgo = {
      value: 0,
      unit: "minutes",
    };
  } else {
    timeAgoString ??= news;
    const postedAt = parseNewsTimestamp(timeAgoString);
    const timeAgoMatch = timeAgoString?.match(
      /(\d+)\s+(days?|hours?|minutes?)\s+ago/i
    );
    timeAgo = postedAt
      ? getTimeSince(postedAt)
      : timeAgoMatch
      ? {
          value: parseInt(timeAgoMatch[1], 10),
          unit: timeAgoMatch[2].toLowerCase().replace(/s?$/, "s") as TimeAgo["unit"],
        }
      : undefined;
  }

  return { injuryStatus, timeAgo };
}

async function getRefinedPlayerStatusFromRow(
  row: HTMLTableRowElement,
  playerStatus: PlayerStatus,
  playerName: string
): Promise<
  | { injuryStatus: PlayerStatus; timeAgo: TimeAgo | undefined }
  | undefined
> {
  const newsTrigger = row.querySelector(".fa-file-text, .fa-file-text-o");

  if (!newsTrigger) {
    return undefined;
  }

  let news: string | undefined;
  let newsElement: Element | undefined;

  const pageDataNews = getPlayerNewsFromPageData(newsTrigger);

  if (pageDataNews) {
    news = pageDataNews.news;
    newsElement = pageDataNews.newsElement;
  } else {
    console.warn(`Falling back to DOM scrape for ${playerName} news`);
    const domNews = await getPlayerNewsFromDOM(newsTrigger);
    news = domNews.news;
    newsElement = domNews.newsElement;
  }

  if (!news || playerStatus === "(active)") {
    return undefined;
  }

  const timeAgoString =
    newsElement?.querySelector("relative-time")?.textContent;
  return parsePlayerNews(news, timeAgoString);
}

export async function getPlayerStatusInfo(
  row: HTMLTableRowElement,
  playerName: string
): Promise<{
  playerStatus: PlayerStatus;
  refinedPlayerStatus:
    | { injuryStatus: PlayerStatus; timeAgo: TimeAgo | undefined }
    | undefined;
}> {
  const playerStatus = getPlayerStatusFromRow(row);
  const refinedPlayerStatus = await getRefinedPlayerStatusFromRow(
    row,
    playerStatus,
    playerName
  );

  return {
    playerStatus,
    refinedPlayerStatus,
  };
}

function parseNewsTimestamp(text: string) {
  const match = text.match(NEWS_TIMESTAMP);
  if (!match) return undefined;
  const [, month, day, yearSuffix, hour, minute, amPm] = match;
  const hour24 = (Number(hour) % 12) + (amPm === "P" ? 12 : 0);
  const year = parseYearFromSuffix(Number(yearSuffix), new Date().getFullYear());
  return easternTimeToDate(year, Number(month), Number(day), hour24, Number(minute));
}

function getTimeSince(date: Date): TimeAgo {
  const minutes = Math.max(0, Math.floor((Date.now() - date.getTime()) / (60 * 1000)));
  if (minutes < 60) return { value: minutes, unit: "minutes" };
  const hours = Math.floor(minutes / 60);
  if (hours < 72) return { value: hours, unit: "hours" };
  return { value: Math.floor(hours / 24), unit: "days" };
}
