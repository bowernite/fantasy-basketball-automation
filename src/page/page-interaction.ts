import {
  getNextDayButton,
  getPreviousDayButton,
  getSaveLineupButton,
} from "./page-querying";
import { type Player } from "../types";
import {
  stylePlayerAsAlternate,
  stylePlayerAsStarted,
  stylePlayerAsUnableToStart,
} from "./page-manipulation";

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
    )
    .filter((option) => option.position !== "TAXI")
    .filter((option) => option.position !== "IR");

  if (positionOptions.length > 0) {
    // First try to find preferred positions in order
    const preferredPositions = ["SG", "PG", "PF", "SF", "G", "F", "C"];
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
    return false;
  }
}

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
export function setAllPlayersToBench(players: Player[]) {
  players
    .filter((player) => player.setPositionDropdown)
    .filter((player) => !player.isTaxi && !player.isIr)
    .forEach((player) => {
      setPlayerPosition(player, "0");
    });
}

export function saveLineup() {
  const button = getSaveLineupButton();
  if (button) {
    button.click();

    // Also try submitting the form directly if button is in a form
    // const form = button.closest("form");
    // if (form) {
    //   form.submit();
    // }
  }
}

export function goToPreviousDay() {
  const button = getPreviousDayButton();
  if (button) {
    button.click();
  }
}

export function goToNextDay() {
  const button = getNextDayButton();
  if (button) {
    button.click();
  }
}
