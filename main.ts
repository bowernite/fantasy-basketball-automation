import { setAllPlayersToBench, startPlayer } from "./src/page-interaction.ts";
import { getPlayers, type Player } from "./src/page-querying.ts";
import { getPlayerPredictedScore } from "./src/score-weighting.ts";
import { stylePlayerAsPossiblyInjured, stylePlayerAsUnableToStart } from "./src/styling.ts";
import { verifyPage } from "./src/sanity-checks.ts";

(async () => {
  if (!verifyPage()) {
    return;
  }

  const players = await getPlayers();
  console.table(players);
  setAllPlayersToBench(players);

  const backupPlayers: Player[] = [];

  const topPlayers = players
    .filter(
      (player) =>
        player.playerStatus === "(active)" || player.playerStatus === "DTD"
    )
    .filter((player) => player.setPositionDropdown)
    .filter((player) => player.todaysGame)
    .sort((a, b) => {
      return getPlayerPredictedScore(b) - getPlayerPredictedScore(a);
    });
  let numPlayersStarted = 0;
  topPlayers.forEach((player, index) => {
    if (numPlayersStarted >= 9) {
      return;
    }

    if (player.isTaxi || player.isIr) {
      stylePlayerAsUnableToStart(player);
      return;
    }
    if (player.playerStatus === "DTD") {
      backupPlayers.push(player);
      stylePlayerAsPossiblyInjured(player);
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
  remainingBackupPlayers.forEach(({ playerName, playerStatus }) => {
    // alert(
    //   `⚠️ Would have started ${playerName}, but they're ${playerStatus}; check their status now, or check back before game time`
    // );
  });
})();
