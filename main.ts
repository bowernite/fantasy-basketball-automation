import {
  setAllPlayersToBench,
  startPlayer,
} from "./src/page/page-interaction.ts";
import { lineupHasChanges } from "./src/page/page-querying.ts";
import { getPlayers } from "./src/page/get-players.ts";
import {
  stylePlayerAsPossiblyInjured,
  stylePlayerAsUnableToStart,
} from "./src/page/page-manipulation.ts";
import { verifyPage } from "./src/sanity-checks.ts";
import { prioritizePlayers } from "./src/prioritization/prioritization.ts";

async function setLineup() {
  try {
    if (!verifyPage()) {
      return;
    }

    console.clear();

    const players = await getPlayers();
    setAllPlayersToBench(players);

    let numPlayersStarted = 0;

    prioritizePlayers(players).forEach(({ player, score, debugInfo }) => {
      // For now, this is done on page load
      // insertPlayerPredictedScore(player, score, { debugInfo });
      // if (player.refinedPlayerStatus) {
      //   insertRefinedPlayerStatus(player, player.refinedPlayerStatus);
      // }

      if (!player.setPositionDropdown) {
        return;
      }

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
  } catch (error) {
    console.error(error);
    alert(error);
    throw error;
  }
}

setLineup();
