import {
  saveLineup,
  setAllPlayersToBench,
  startPlayer,
} from "./src/page-interaction.ts";
import { getPlayers, lineupHasChanges } from "./src/page-querying.ts";
import {
  insertPlayerPredictedScore,
  stylePlayerAsPossiblyInjured,
  stylePlayerAsUnableToStart,
} from "./src/styling.ts";
import { verifyPage } from "./src/sanity-checks.ts";
import { prioritizePlayers } from "./src/prioritization.ts";

(async () => {
  if (!verifyPage()) {
    return;
  }

  console.clear();

  const players = await getPlayers();
  console.table(players);
  setAllPlayersToBench(players);

  let numPlayersStarted = 0;

  prioritizePlayers(players).forEach(({ player, score }) => {
    insertPlayerPredictedScore(player, score, {
      isDtd: player.playerStatus === "DTD",
      noGame: !player.opponentInfo,
    });

    if (numPlayersStarted >= 9) {
      return;
    }

    if (player.isTaxi || player.isIr) {
      stylePlayerAsUnableToStart(player);
      return;
    }

    const isInjured =
      player.playerStatus === "DTD" || player.playerStatus === "OUT";
    if (isInjured) {
      stylePlayerAsPossiblyInjured(player);
    }

    const playerStarted = startPlayer(player, {
      isAlternate: numPlayersStarted >= 9,
    });
    if (playerStarted) {
      numPlayersStarted++;
    }
  });

  if (lineupHasChanges()) {
    // saveLineup();
  }
})();
