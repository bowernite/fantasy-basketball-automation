import { getPlayers } from "./src/page/get-players";
import {
  addSaveLineupButton,
  insertPlayerPredictedScore,
  refinePlayerStatus,
} from "./src/page/page-manipulation";
import { prioritizePlayers } from "./src/prioritization/prioritization";

const inBrowser = typeof window !== "undefined";
if (inBrowser) {
  pageLoad();
}

async function pageLoad() {
  addSaveLineupButton();
  try {
    const players = await getPlayers();
    prioritizePlayers(players).forEach(({ player, score, debugInfo }) => {
      insertPlayerPredictedScore(player, score, { debugInfo });
      refinePlayerStatus(player);
    });
  } catch (error) {
    console.error(error);
    alert(error);
    throw error;
  }
}
