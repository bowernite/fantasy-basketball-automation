import { setAllPlayersToBench } from "./src/lineup/lineup-dom-actions.ts";
import { lineupHasChanges } from "./src/page/page-querying.ts";
import { getPlayers } from "./src/page/get-players.ts";
import {
  stylePlayerAsPossiblyInjured,
  stylePlayerAsUnableToStart,
} from "./src/page/page-manipulation.ts";
import { verifyPage } from "./src/sanity-checks.ts";
import { setOptimalLineup } from "./src/lineup/set-optimal-lineup.ts";

setLineup();

async function setLineup() {
  try {
    if (!verifyPage()) {
      return;
    }

    console.clear();

    const players = await getPlayers();
    setAllPlayersToBench(players);

    players.forEach((player) => {
      if (player.isTaxi || player.isIr) {
        stylePlayerAsUnableToStart(player);
        return;
      }
      const isInjured =
        player.playerStatus === "DTD" || player.playerStatus === "OUT";
      if (isInjured) {
        stylePlayerAsPossiblyInjured(player);
      }
    });

    setOptimalLineup(players);

    if (lineupHasChanges()) {
      // saveLineup();
    }
  } catch (error) {
    console.error(error);
    alert(error);
    throw error;
  }
}
