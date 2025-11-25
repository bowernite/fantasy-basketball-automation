import { PLAYER_STATUS_SELECTOR } from "./page-querying";
import { getTooltipContent } from "./tooltip";
import { getTooltipContentFromPageData } from "./page-data";
import type { PlayerStatus, TimeAgo } from "../types";

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
  const injuryStatusMatch = news.match(
    // 'fouled' is to handle 'fouled out'
    /\b(?<!fouled\s+)(questionable|doubtful|probable|available|out)\b/i
  );
  const rawStatus = injuryStatusMatch?.[1]?.toLowerCase();
  const injuryStatus: PlayerStatus | undefined =
    rawStatus === "questionable"
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
    const timeAgoMatch = timeAgoString?.match(
      /(\d+)\s+(days?|hours?|minutes?)\s+ago/i
    );
    timeAgo = timeAgoMatch
      ? {
          value: parseInt(timeAgoMatch[1], 10),
          unit: timeAgoMatch[2].toLowerCase() as "days" | "hours" | "minutes",
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
  const newsTrigger = row.querySelector(".fa-file-text");

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

