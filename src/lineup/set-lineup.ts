import { setAllPlayersToBench } from "./lineup-dom-actions";
import { lineupHasChanges } from "../page/page-querying";
import { getPlayers } from "../page/get-players";
import {
  stylePlayerAsPossiblyInjured,
  stylePlayerAsUnableToStart,
} from "../page/page-manipulation";
import { verifyPage } from "../sanity-checks";
import { setOptimalLineup } from "./set-optimal-lineup";

export async function setLineup() {
  try {
    if (!verifyPage()) {
      return;
    }

    console.clear();

    let players = await getPlayers();
    await setAllPlayersToBench(players);
    
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

