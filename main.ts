import { players, type Player } from "./src/page";
import { getPlayerWeightedScore } from "./src/score-weighting.ts";
import {
  stylePlayerAsAlternate,
  stylePlayerAsStarted,
  stylePlayerAsUnableToStart,
} from "./src/styling";

let numPlayersStarted = 0;

const setPlayerPosition = (player: Player, position: string) => {
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
players
  .filter((player) => player.setPositionDropdown)
  .filter((player) => !player.isTaxi && !player.isIr)
  .forEach((player) => {
    setPlayerPosition(player, "0");
  });

// TODO: Handle TAXI, IR players properly. Right now it puts them on the bench.

const topPlayers = players
  // TODO: Handle probable, questionable, etc.
  .filter((player) => player.playerStatus === "active")
  .filter((player) => player.setPositionDropdown)
  .filter((player) => player.todaysGame)
  .sort((a, b) => {
    return getPlayerWeightedScore(b) - getPlayerWeightedScore(a);
  });
const topPlayersWithoutGameToday = topPlayers.filter(
  (player) => !player.todaysGame
);

const playersToStart = topPlayers.map((player, index) => {
  if (numPlayersStarted >= 9) {
    return;
  }
  startPlayer(player, { isAlternate: index >= 9 });

  return player;
});

function startPlayer(
  player: Player,
  { isAlternate = false }: { isAlternate?: boolean } = {}
) {
  if (!player.setPositionDropdown) {
    throw new Error(
      "Tried to start a player without a dropdown; this player is likely LOCKED."
    );
  }

  const positionOptions = Array.from(player.setPositionDropdown.options)
    .map((option) => ({ position: option.text, value: option.value }))
    .filter(
      (option) =>
        option.position.toLowerCase() !== "bench" && option.value !== "0"
    );
  console.log(`Available positions for ${player.playerName}:`, positionOptions);

  if (positionOptions.length > 0) {
    const lowestValueOption = positionOptions.reduce((lowest, current) =>
      Number(current.value) < Number(lowest.value) ? current : lowest
    );
    setPlayerPosition(player, lowestValueOption.value);
    numPlayersStarted++;

    console.log(
      `Set ${player.playerName} to position: ${lowestValueOption.position}`
    );

    if (isAlternate) {
      stylePlayerAsAlternate(player);
    } else {
      stylePlayerAsStarted(player);
    }
  } else {
    stylePlayerAsUnableToStart(player);
    console.error(`No position options available for ${player.playerName}`);
  }
}

console.table(playersToStart);

if (numPlayersStarted < 9) {
  console.warn("Not enough players started;");
  // const playersWithoutGameToStart = topPlayersWithoutGameToday.filter(
}
