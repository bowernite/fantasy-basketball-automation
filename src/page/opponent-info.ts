import { getTooltipContent } from "./tooltip";
import { getTooltipContentFromMapText } from "./page-data";
import type { PlayerOpponentInfo } from "../types";

export function getPlayerOpponentInfoFromPageData(
  todaysGameElement: Element,
  playerName: string
): PlayerOpponentInfo | undefined {
  const opponentInfoElement = todaysGameElement?.querySelector("a");
  if (!opponentInfoElement) {
    return undefined;
  }

  const tooltipContent = getTooltipContentFromMapText(opponentInfoElement);
  if (!tooltipContent?.fullString) return undefined;

  return parseOpponentInfo(tooltipContent.fullString, playerName);
}

export function parseOpponentInfo(
  content: string,
  playerName: string
): PlayerOpponentInfo | undefined {
  const positionMatch = content.match(/Vs opposing (\w+)s per game/);
  const position = positionMatch?.[1];

  const defaultFptsMatch = content.match(
    /Default FPts: (\d+\.?\d*) \((\d+)(?:st|nd|rd|th)\)/
  );
  const avgPointsAllowed = parseFloat(defaultFptsMatch?.[1] ?? "0");
  const defenseRank = parseInt(defaultFptsMatch?.[2] ?? "0", 10);

  const isInvalid =
    isNaN(avgPointsAllowed) ||
    isNaN(defenseRank) ||
    !avgPointsAllowed ||
    !defenseRank;

  if (isInvalid) {
    return undefined;
  }

  return {
    avgPointsAllowed,
    avgPointsAllowedRank: defenseRank,
    defenseRank,
    position,
  };
}

export async function getPlayerOpponentInfoFromDOM(
  todaysGameElement: Element,
  playerName: string
): Promise<PlayerOpponentInfo | undefined> {
  const opponentInfoElement = todaysGameElement?.querySelector("a");
  if (!opponentInfoElement) {
    console.warn(
      `Failed to get opponent info element for ${playerName} (fallback).`
    );
    return undefined;
  }

  const opponentInfoTooltip = await getTooltipContent(opponentInfoElement);
  const opponentInfoContent = opponentInfoTooltip?.fullString;

  if (!opponentInfoContent) {
    console.warn(
      `Failed to scrape tooltip content for ${playerName} (fallback).`
    );
    return undefined;
  }

  const result = parseOpponentInfo(opponentInfoContent, playerName);
  if (!result) {
    console.warn(
      `Failed to parse opponent info for ${playerName} (fallback). Tooltip content: ${
        opponentInfoContent ?? "No content"
      }`
    );
  }
  return result;
}

export async function getOpponentInfo(
  row: HTMLTableRowElement,
  playerName: string
) {
  const todaysGameElement = row.querySelector(".pro-opp-matchup");
  if (!todaysGameElement) return undefined;

  const opponentInfo = getPlayerOpponentInfoFromPageData(
    todaysGameElement,
    playerName
  );
  if (opponentInfo) return opponentInfo;

  console.warn(`Falling back to DOM scrape for ${playerName} opponent info`);
  return await getPlayerOpponentInfoFromDOM(todaysGameElement, playerName);
}
