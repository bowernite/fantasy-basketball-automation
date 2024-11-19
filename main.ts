import { setAllPlayersToBench, startPlayer } from "./src/page-interaction.ts";
import { getPlayers } from "./src/page-querying.ts";
import {
  stylePlayerAsPossiblyInjured,
  stylePlayerAsUnableToStart,
} from "./src/styling.ts";
import { verifyPage } from "./src/sanity-checks.ts";
import { prioritizePlayers } from "./src/prioritization.ts";

(async () => {
  if (!verifyPage()) {
    return;
  }

  const players = await getPlayers();
  console.table(players);
  setAllPlayersToBench(players);

  let numPlayersStarted = 0;

  prioritizePlayers(players).forEach((player) => {
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
})();
