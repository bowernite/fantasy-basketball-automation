import { players, type Player } from "./src/page";

let numPlayersStarted = 0;

const ALTERNATE_COLOR = "rgba(0, 255, 255, 0.3)";
const OUTLINE_COLOR = "rgb(0, 200, 255)";
const SELECTED_COLOR = "rgba(0, 255, 0, 0.3)";
const WARNING_COLOR = "rgba(255, 0, 0, 0.3)";

const setPlayerPosition = (player: Player, position: string) => {
  player.setPositionDropdown.value = position;
  const changeEvent = new Event("change", { bubbles: true });
  player.setPositionDropdown.dispatchEvent(changeEvent);
};

// Set all players to Bench first
players.forEach((player) => {
  setPlayerPosition(player, "0");
});

// TODO: Handle TAXI, IR players properly. Right now it puts them on the bench.

const topPlayers = players
  // TODO: Handle probable, questionable, etc.
  .filter((player) => player.playerStatus === "active")
  // TODO: turn back on
  // .filter((player) => player.todaysGame)
  .sort((a, b) => {
    const weightedScoreA = 0.75 * a.seasonAvg + 0.25 * a.last5Avg;
    const weightedScoreB = 0.75 * b.seasonAvg + 0.25 * b.last5Avg;
    return weightedScoreB - weightedScoreA;
  });
const topPlayersWithoutGameToday = topPlayers.filter(
  (player) => !player.todaysGame
);

const playersToStart = topPlayers.map((player, index) => {
  if (numPlayersStarted >= 9) {
    return;
  }
  startPlayer(player, { isAlternate: index >= 10 });

  return player;
});

function startPlayer(
  player: Player,
  { isAlternate = false }: { isAlternate?: boolean } = {}
) {
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
      player.row.style.backgroundColor = ALTERNATE_COLOR;
      player.row.style.outline = `2px solid ${OUTLINE_COLOR}`;
      setTimeout(() => {
        player.row.style.backgroundColor = ALTERNATE_COLOR;
      }, 1000);
    } else {
      setTimeout(() => {
        player.row.style.backgroundColor = SELECTED_COLOR;
      }, 500);
    }
  } else {
    player.row.style.backgroundColor = WARNING_COLOR;
    console.error(`No position options available for ${player.playerName}`);
  }
}

console.table(playersToStart);

if (numPlayersStarted < 9) {
  console.warn("Not enough players started;");
  // const playersWithoutGameToStart = topPlayersWithoutGameToday.filter(
}
