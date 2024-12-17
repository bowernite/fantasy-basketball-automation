import { getPlayers } from "./src/page/get-players";
import {
  addSaveLineupButton,
  insertPlayerPredictedScore,
} from "./src/page/page-manipulation";
import { prioritizePlayers } from "./src/prioritization";

addSaveLineupButton();

(async () => {
  try {
    const players = await getPlayers();
    prioritizePlayers(players).forEach(({ player, score, debugInfo }) => {
      insertPlayerPredictedScore(player, score, { debugInfo });
    });
  } catch (error) {
    console.error(error);
    alert(error);
    throw error;
  }
})();
