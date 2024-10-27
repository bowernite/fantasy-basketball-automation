import { playerData } from "./src/selectors";

let numPlayersSelected = 0;

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
  .map((player) => {
    if (numPlayersSelected >= 9) {
      return;
    }

    player.row.style.backgroundColor = "rgba(255, 0, 0, 0.3)";

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
    } else {
      console.error(`No position options available for ${player.playerName}`);
    }

    return player;
  });

console.table(playersToStart);
