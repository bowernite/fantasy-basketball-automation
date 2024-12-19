// NOTES
// - Assumes we're on `fantasy stats` page

import { parseNumberString } from "../utils/parse-number-string";

let tables = document.querySelectorAll("table");
if (tables.length !== 1) {
  throw new Error("Expected exactly one table");
}
let table = tables[0];
let rows = table.querySelectorAll("tr");
if (rows.length === 0) {
  throw new Error("Expected at least one row");
}

export type Player = Awaited<ReturnType<typeof getPlayers>>[number];
export type PlayerStatus = "(active)" | "DTD" | "P" | "Q" | "D" | "OUT" | "OFS";
export type PlayerOpponentInfo = {
  avgPointsAllowed: number;
  avgPointsAllowedRank: number;
};
export type TimeAgo = {
  value: number;
  unit: "days" | "hours" | "minutes";
};

export const PLAYER_STATUS_SELECTOR = ".injury";

export const getPlayers = async () => {
  const players = await Promise.all(
    Array.from(rows).map(async (row) => {
      const playerName = row.querySelector(".player-text")?.textContent;
      if (!playerName) {
        return;
      }
      let playerStatus =
        row.querySelector(PLAYER_STATUS_SELECTOR)?.textContent?.split(" ")[0] ||
        "(active)";
      const fantasyPointsElements = row.querySelectorAll(".fp");
      const last5Avg = parseNumberString(fantasyPointsElements[1]?.textContent);
      const last10Avg = parseNumberString(
        fantasyPointsElements[2]?.textContent
      );
      const seasonAvg = parseNumberString(
        fantasyPointsElements[fantasyPointsElements.length - 2]?.textContent
      );
      const seasonTotal = parseNumberString(
        fantasyPointsElements[fantasyPointsElements.length - 1]?.textContent
      );
      const gamesPlayed =
        seasonTotal && seasonAvg ? seasonTotal / seasonAvg : null;
      const position = row.querySelector(".position")?.textContent;
      const setPositionDropdown =
        row.querySelector<HTMLSelectElement>(".form-control");
      const isTaxi = setPositionDropdown?.selectedOptions[0]?.text === "TAXI";
      const isIr = setPositionDropdown?.selectedOptions[0]?.text === "IR";

      const todaysGameElement = row.querySelector(".pro-opp-matchup");
      const todaysGame = todaysGameElement?.textContent;
      const opponentInfo = todaysGameElement
        ? await getPlayerOpponentInfo(todaysGameElement, playerName)
        : undefined;

      const newsTrigger = row.querySelector(".fa-file-text");
      const { fullString: news, element: newsElement } = newsTrigger
        ? await getTooltipContent(newsTrigger)
        : { fullString: undefined, element: undefined };
      const timeAgoString =
        newsElement?.querySelector("relative-time")?.textContent;
      const refinedPlayerStatus =
        news && playerStatus !== "(active)"
          ? parsePlayerNews(news, timeAgoString)
          : undefined;
      console.log(`🟣 ${playerName} refinedPlayerStatus:`, refinedPlayerStatus);

      return {
        playerName,
        playerStatus: playerStatus as PlayerStatus,
        refinedPlayerStatus,
        last5Avg,
        last10Avg,
        seasonAvg,
        seasonTotal,
        gamesPlayed,
        todaysGame,
        position,
        setPositionDropdown,
        isTaxi,
        isIr,
        opponentInfo,
        row,
      };
    })
  );

  return players.filter(
    (player): player is NonNullable<typeof player> => player !== undefined
  );
};

export function getPlayerNameCell(player: Player) {
  return player.row.querySelector<HTMLTableCellElement>("td:first-child");
}
export function getPlayerNameEl(player: Player) {
  const cell = getPlayerNameCell(player);
  if (!cell) return;
  return cell.querySelector<HTMLElement>(".player");
}

async function getPlayerOpponentInfo(
  todaysGameElement: Element,
  playerName: string
) {
  const opponentInfoElement = todaysGameElement?.querySelector("a");
  let opponentInfoContent: string | undefined | null;
  if (!opponentInfoElement) {
    console.warn(`Failed to get opponent info for ${playerName}.`, {
      todaysGameElement,
      opponentInfoElement,
    });
    return undefined;
  }
  const opponentInfoTooltip = await getTooltipContent(opponentInfoElement);
  opponentInfoContent = opponentInfoTooltip?.fullString;

  // "Vs opposing Cs per game:Pts: 24.67 (6th)Reb: 20.67 (t-15th)Ast: 7 (19th)Default FPts: 43.78 (12th)"
  const positionMatch = opponentInfoContent?.match(
    /Vs opposing (\w+)s per game/
  );
  const position = positionMatch?.[1];

  const defaultFptsMatch = opponentInfoContent?.match(
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
    console.warn(
      `Failed to parse opponent info for ${playerName}. Tooltip content: ${
        opponentInfoContent ?? "No content"
      }`
    );
    return undefined;
  }

  return {
    avgPointsAllowed,
    defenseRank,
    position,
  };
}

function parsePlayerNews(
  news: string,
  timeAgoString: string | null | undefined
) {
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

/********************************************************************
 * Utils
 *******************************************************************/
async function getTooltipContent(trigger: Element) {
  trigger.dispatchEvent(
    new MouseEvent("mouseover", {
      bubbles: true,
      cancelable: true,
      view: window,
    })
  );
  await new Promise((resolve) => setTimeout(resolve, 100));

  const tooltip = trigger.parentElement?.querySelector(".tooltip");
  const tooltipContent = tooltip?.textContent;

  trigger.dispatchEvent(
    new MouseEvent("mouseout", {
      bubbles: true,
      cancelable: true,
      view: window,
    })
  );

  return {
    fullString: tooltipContent,
    element: tooltip,
  };
}
