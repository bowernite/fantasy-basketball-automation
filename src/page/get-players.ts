// NOTES
// - Assumes we're on `fantasy stats` page

import { parseNumberString } from "../utils/parse-number-string";
import { getPlayersTable } from "./page-querying";
import { getTooltipPageData } from "./page-data";
import { getOpponentInfo } from "./opponent-info";
import { getPlayerStatusInfo } from "./player-status";
import type { Player } from "../types";

export const getPlayers = async (): Promise<Player[]> => {
  const table = getPlayersTable();
  const rows = Array.from(table.querySelectorAll("tr"));
  if (!rows.length) {
    throw new Error("Expected at least one row");
  }

  // Initialize the tooltip map once
  getTooltipPageData();

  const players = await Promise.all(rows.map(processPlayerRow));
  return players.filter((p): p is Player => p !== undefined);
};

async function processPlayerRow(
  row: HTMLTableRowElement
): Promise<Player | undefined> {
  const playerName = row.querySelector(".player-text")?.textContent;
  if (!playerName) return undefined;

  const fantasyPoints = extractFantasyPoints(row);
  const basicInfo = extractBasicInfo(row);
  const opponentInfo = await getOpponentInfo(row, playerName);
  const { playerStatus, refinedPlayerStatus } = await getPlayerStatusInfo(
    row,
    playerName
  );

  return {
    playerName,
    playerStatus,
    refinedPlayerStatus,
    ...fantasyPoints,
    ...basicInfo,
    opponentInfo,
    row,
  };
}

function extractFantasyPoints(row: HTMLTableRowElement) {
  const fpElements = row.querySelectorAll(".fp");
  const last5Avg = parseNumberString(fpElements[1]?.textContent);
  const last10Avg = parseNumberString(fpElements[2]?.textContent);
  const seasonAvg = parseNumberString(
    fpElements[fpElements.length - 2]?.textContent
  );
  const seasonTotal = parseNumberString(
    fpElements[fpElements.length - 1]?.textContent
  );
  const gamesPlayed = seasonTotal && seasonAvg ? seasonTotal / seasonAvg : null;

  return { last5Avg, last10Avg, seasonAvg, seasonTotal, gamesPlayed };
}

function extractBasicInfo(row: HTMLTableRowElement) {
  const position = row.querySelector(".position")?.textContent;
  const setPositionDropdown =
    row.querySelector<HTMLSelectElement>(".form-control");
  const selectedText = setPositionDropdown?.selectedOptions[0]?.text;
  const todaysGameElement = row.querySelector(".pro-opp-matchup");

  return {
    position,
    setPositionDropdown,
    isTaxi: selectedText === "TAXI",
    isIr: selectedText === "IR",
    todaysGame: todaysGameElement?.textContent,
  };
}
