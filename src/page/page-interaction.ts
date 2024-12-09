import { getSaveLineupButton, type Player } from "./page-querying";
import {
  stylePlayerAsAlternate,
  stylePlayerAsStarted,
  stylePlayerAsUnableToStart,
} from "../styling";

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
