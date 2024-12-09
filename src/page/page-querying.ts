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

export function getStatTypeDropdown() {
  // 1: average/total. 2: season, fantasy, daily, last 5, etc. 3: previous year. 4: year selector
  const dropdownTriggers = document.querySelectorAll<HTMLAnchorElement>(
    ".btn-toolbar a.dropdown-toggle"
  );
  let statTypeDropdown: HTMLAnchorElement | undefined;
  dropdownTriggers.forEach((dropdownTrigger) => {
    if (statTypeDropdown) return;
    const dropdownMenu = dropdownTrigger.nextElementSibling;
    if (dropdownMenu?.textContent?.toLowerCase().includes("fantasy stats")) {
      statTypeDropdown = dropdownTrigger;
    }
  });

  return statTypeDropdown;
}

export function lineupHasChanges() {
  return (
    document.body.textContent
      ?.toLowerCase()
      .includes("click save lineup to save your changes".toLowerCase()) ?? false
  );
}

export function getSaveLineupButton() {
  const buttons = Array.from(
    document.querySelectorAll<HTMLButtonElement>("button[type='submit']")
  );
  const saveButton = buttons.find((button) =>
    button.textContent?.toLowerCase().includes("save lineup")
  );
  return saveButton;
}

export function getPageDate() {
  const allButtons = document.querySelectorAll("a.btn[data-toggle='dropdown']");
  const buttonsWithDates = Array.from(allButtons).filter((button) => {
    const text = button.textContent?.toLowerCase().trim() ?? "";
    return text.match(/\d{1,2}\/\d{1,2}(?:\/\d{2})?/) || text === "today";
  });
  if (buttonsWithDates.length !== 1) {
    console.error(
      `Tried to get page date but found ${buttonsWithDates.length} date buttons`,
      buttonsWithDates
    );
    throw new Error("Tried to get page date but found multiple date buttons");
  }
  const dateText = buttonsWithDates[0].textContent?.toLowerCase().trim() ?? "";
  if (dateText === "today") {
    return new Date(new Date().setHours(0, 0, 0, 0));
  }
  const dateMatch = dateText.match(/(\d{1,2}\/\d{1,2})(?:\/\d{2})?/);
  if (!dateMatch) {
    console.error("Could not find date in button text");
    throw new Error("Could not find date in button text");
  }
  const [month, day] = dateMatch[1].split("/").map(Number);
  return new Date(new Date().getFullYear(), month - 1, day);
}
