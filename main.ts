import {
  players,
  setAllPlayersToBench,
  startPlayer,
  type Player,
} from "./src/page";
import { getPlayerWeightedScore } from "./src/score-weighting.ts";
import { stylePlayerAsUnableToStart } from "./src/styling.ts";

setAllPlayersToBench();

const backupPlayers: Player[] = [];

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
    backupPlayers.push(player);
    return;
  }
  if (player.isTaxi) {
    stylePlayerAsUnableToStart(player);
    return;
  }

  const playerStarted = startPlayer(player, { isAlternate: index >= 9 });
  if (playerStarted) {
    numPlayersStarted++;
  }
});

if (numPlayersStarted < 9) {
  console.warn("Not enough players started;");
  // TODO: Start empty players? I guess it doesn't matter...
  backupPlayers.forEach((player) => {
    const playerStarted = startPlayer(player);
    if (playerStarted) {
      numPlayersStarted++;
    }
  });
  backupPlayers.shift();
}

const remainingBackupPlayers = [...backupPlayers];
remainingBackupPlayers.forEach((player) => {
  alert(
    `WARNING: ${player.playerName} is ${player.playerStatus}; not starting this player, but you may want to check back later if they're playing`
  );
});

players.forEach((player) =>
  console.log(
    `Weighted score for ${player.playerName}: ${getPlayerWeightedScore(player)}`
  )
);
