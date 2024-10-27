import { playerData } from "./src/selectors";

let numPlayersSelected = 0;

const ALTERNATE_COLOR = "rgba(0, 255, 255, 0.3)";
const OUTLINE_COLOR = "rgb(0, 200, 255)";
const SELECTED_COLOR = "rgba(0, 255, 0, 0.3)";
const WARNING_COLOR = "rgba(255, 0, 0, 0.3)";

// Set all players to Bench first
playerData.forEach((player) => {
  player.setPositionDropdown.value = "0";
  const changeEvent = new Event("change", { bubbles: true });
  player.setPositionDropdown.dispatchEvent(changeEvent);
});

// TODO: Handle TAXI, IR players properly. Right now it puts them on the bench.

const playersToStart = playerData
  // TODO: Handle probable, questionable, etc.
  .filter((player) => player.playerStatus === "active")
  // TODO: turn back on
  // .filter((player) => player.todaysGame)
  .sort((a, b) => {
    const weightedScoreA = 0.75 * a.seasonAvg + 0.25 * a.last5Avg;
    const weightedScoreB = 0.75 * b.seasonAvg + 0.25 * b.last5Avg;
    return weightedScoreB - weightedScoreA;
  })
  .map((player, index) => {
    if (numPlayersSelected >= 9) {
      return;
    }

    const positionOptions = Array.from(player.setPositionDropdown.options)
      .map((option) => ({ position: option.text, value: option.value }))
      .filter(
        (option) =>
          option.position.toLowerCase() !== "bench" && option.value !== "0"
      );
    console.log(
      `Available positions for ${player.playerName}:`,
      positionOptions
    );

    if (positionOptions.length > 0) {
      const lowestValueOption = positionOptions.reduce((lowest, current) =>
        Number(current.value) < Number(lowest.value) ? current : lowest
      );
      player.setPositionDropdown.value = lowestValueOption.value;

      // Trigger change event to ensure any listeners are notified
      const changeEvent = new Event("change", { bubbles: true });
      player.setPositionDropdown.dispatchEvent(changeEvent);
      numPlayersSelected++;

      console.log(
        `Set ${player.playerName} to position: ${lowestValueOption.position}`
      );

      if (index >= 10) {
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

    return player;
  });

console.table(playersToStart);
