// NOTES
// - Assumes we're on `fantasy stats` page

import {
  stylePlayerAsAlternate,
  stylePlayerAsStarted,
  stylePlayerAsUnableToStart,
} from "./styling";

let tables = document.querySelectorAll("table");
if (tables.length !== 1) {
  throw new Error("Expected exactly one table");
}
let table = tables[0];

let rows = table.querySelectorAll("tr");
if (rows.length === 0) {
  throw new Error("Expected at least one row");
}

export const players = Array.from(rows)
  .map((row) => {
    const playerName = row.querySelector(".player-text")?.textContent;
    if (!playerName) {
      console.warn("Empty row found; skipping");
      return;
    }
    const playerStatus =
      row.querySelector(".injury")?.textContent || "(active)";
    const fantasyPointsElements = row.querySelectorAll(".fp");
    const last5Avg = Number(fantasyPointsElements[1]?.textContent ?? 0);
    const seasonAvg = Number(fantasyPointsElements[2]?.textContent ?? 0);
    const seasonTotal = Number(fantasyPointsElements[3]?.textContent ?? 0);
    const gamesPlayed = seasonTotal / seasonAvg;
    const todaysGame = row.querySelector(".pro-opp-matchup")?.textContent;
    const position = row.querySelector(".position")?.textContent;
    const setPositionDropdown =
      row.querySelector<HTMLSelectElement>(".form-control");
    const isTaxi = row.textContent?.includes("TAXI");
    const isIr = row.textContent?.includes("IR");

    if (
      playerStatus !== "DTD" &&
      playerStatus !== "OUT" &&
      playerStatus !== "Q" &&
      playerStatus !== "OFS" &&
      playerStatus !== "(active)"
    ) {
      alert(`Unknown player status: ${playerStatus}`);
    }

    return {
      playerName,
      playerStatus: playerStatus as PlayerStatus,
      last5Avg,
      seasonAvg,
      // seasonTotal,
      gamesPlayed,
      todaysGame,
      position,
      setPositionDropdown,
      isTaxi,
      isIr,
      row,
    };
  })
  .filter((player) => player !== undefined);

export type Player = (typeof players)[number];

export type PlayerStatus = "(active)" | "DTD" | "OUT" | "Q" | "OFS";

export function startPlayer(
  player: Player,
  { isAlternate = false }: { isAlternate?: boolean } = {}
) {
  if (!player.setPositionDropdown) {
    const errorMessage = `Tried to start ${player.playerName} without a dropdown; this player is likely LOCKED.`;
    alert(`WARNING: ${errorMessage}`);
    return false;
  }

  const positionOptions = Array.from(player.setPositionDropdown.options)
    .map((option) => ({ position: option.text, value: option.value }))
    .filter(
      (option) =>
        option.position.toLowerCase() !== "bench" && option.value !== "0"
    );

  if (positionOptions.length > 0) {
    // First try to find preferred positions in order
    const preferredPositions = ["PF", "C", "SF", "F", "SG", "PG"];
    for (const preferredPosition of preferredPositions) {
      const preferredOption = positionOptions.find(
        (option) => option.position === preferredPosition
      );
      if (preferredOption) {
        setPlayerPosition(player, preferredOption.value);
        console.log(
          `Set ${player.playerName} to preferred position: ${preferredOption.position}`
        );
        if (isAlternate) {
          stylePlayerAsAlternate(player);
        } else {
          stylePlayerAsStarted(player);
        }
        return true;
      }
    }

    // Fall back to lowest value option if no preferred positions found
    const lowestValueOption = positionOptions.reduce((lowest, current) =>
      Number(current.value) < Number(lowest.value) ? current : lowest
    );
    setPlayerPosition(player, lowestValueOption.value);

    console.log(
      `Set ${player.playerName} to position: ${lowestValueOption.position}`
    );

    if (isAlternate) {
      stylePlayerAsAlternate(player);
    } else {
      stylePlayerAsStarted(player);
    }

    return true;
  } else {
    stylePlayerAsUnableToStart(player);
    console.error(`No position options available for ${player.playerName}`);
    return false;
  }
}

console.table(players);

export const setPlayerPosition = (player: Player, position: string) => {
  if (!player.setPositionDropdown) {
    throw new Error(
      "Tried to set a player's position without a dropdown; this player is likely LOCKED."
    );
  }
  player.setPositionDropdown.value = position;
  const changeEvent = new Event("change", { bubbles: true });
  player.setPositionDropdown.dispatchEvent(changeEvent);
};

// Set all players to Bench first
export function setAllPlayersToBench() {
  players
    .filter((player) => player.setPositionDropdown)
    .filter((player) => !player.isTaxi && !player.isIr)
    .forEach((player) => {
      setPlayerPosition(player, "0");
    });
}
