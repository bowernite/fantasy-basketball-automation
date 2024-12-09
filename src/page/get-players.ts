// NOTES
// - Assumes we're on `fantasy stats` page

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
export type PlayerStatus = "(active)" | "DTD" | "OUT" | "Q" | "OFS";
export type PlayerOpponentInfo = {
  avgPointsAllowed: number;
  avgPointsAllowedRank: number;
};

export const getPlayers = async () => {
  const players = await Promise.all(
    Array.from(rows).map(async (row) => {
      const playerName = row.querySelector(".player-text")?.textContent;
      if (!playerName) {
        console.warn("Empty row found; skipping");
        return;
      }
      const playerStatus =
        row.querySelector(".injury")?.textContent || "(active)";
      const fantasyPointsElements = row.querySelectorAll(".fp");
      const last5Avg =
        Number(fantasyPointsElements[1]?.textContent ?? 0) || undefined;
      const last10Avg =
        Number(fantasyPointsElements[2]?.textContent ?? 0) || undefined;
      const seasonAvg = Number(
        fantasyPointsElements[fantasyPointsElements.length - 2]?.textContent
      );
      const seasonTotal = Number(
        fantasyPointsElements[fantasyPointsElements.length - 1]?.textContent
      );
      const gamesPlayed = seasonTotal / seasonAvg;
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
      // console.log("🟣 opp:", opponentInfo);
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
        last10Avg,
        seasonAvg,
        // seasonTotal,
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

async function getPlayerOpponentInfo(
  todaysGameElement: Element,
  playerName: string
) {
  const opponentInfoElement = todaysGameElement?.querySelector("a");
  let opponentInfoContent: string | undefined | null;
  if (opponentInfoElement && todaysGameElement) {
    opponentInfoElement.dispatchEvent(
      new MouseEvent("mouseover", {
        bubbles: true,
        cancelable: true,
        view: window,
      })
    );
    await new Promise((resolve) => setTimeout(resolve, 100));
    const tooltip = todaysGameElement.querySelector(".tooltip");
    opponentInfoContent = tooltip?.textContent;
    opponentInfoElement.dispatchEvent(
      new MouseEvent("mouseout", {
        bubbles: true,
        cancelable: true,
        view: window,
      })
    );
  }

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
