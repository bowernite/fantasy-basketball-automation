import { players, setAllPlayersToBench, startPlayer } from "./src/page";
import { getPlayerWeightedScore } from "./src/score-weighting.ts";

setAllPlayersToBench();

const topPlayers = players
  .filter(
    (player) =>
      player.playerStatus === "(active)" || player.playerStatus === "DTD"
  )
  .filter((player) => player.setPositionDropdown)
  .filter((player) => player.todaysGame)
  .sort((a, b) => {
    return getPlayerWeightedScore(b) - getPlayerWeightedScore(a);
  });
let numPlayersStarted = 0;
topPlayers.forEach((player, index) => {
  if (numPlayersStarted >= 9) {
    return;
  }

  if (player.playerStatus === "DTD") {
    alert(
      `WARNING: ${player.playerName} is ${player.playerStatus}; not starting this player, but you may want to check back later if they're playing`
    );
    return;
  }

  const playerStarted = startPlayer(player, { isAlternate: index >= 9 });
  if (playerStarted) {
    numPlayersStarted++;
  }
});

if (numPlayersStarted < 9) {
  console.warn("Not enough players started;");
  setTimeout(() => {
    alert(
      "WARNING: Not enough players started; you may want to pick someone up."
    );
  }, 500);
  // TODO: Start empty players? I guess it doesn't matter...
}
