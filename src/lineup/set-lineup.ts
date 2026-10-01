import { getSaveLineupButton, lineupHasChanges } from "../page/page-querying";
import { getPlayers } from "../page/get-players";
import {
  stylePlayerAsPossiblyInjured,
  stylePlayerAsUnableToStart,
} from "../page/overlay/row-states";
import { verifyPage } from "../sanity-checks";
import { setOptimalLineup } from "./set-optimal-lineup";

export async function setLineup() {
  verifyPage();
  if (!getSaveLineupButton()) {
    throw new Error("No Save Lineup button on the page; you may be logged out");
  }

  console.clear();

  const players = await getPlayers();

  players.forEach((player) => {
    if (player.isTaxi || player.isIr) {
      stylePlayerAsUnableToStart(player);
      return;
    }
    const isInjured = player.playerStatus === "DTD";
    if (isInjured && player.todaysGame) {
      stylePlayerAsPossiblyInjured(player);
    }
  });

  setOptimalLineup(players);

  if (lineupHasChanges()) {
    // saveLineup();
  }
}
