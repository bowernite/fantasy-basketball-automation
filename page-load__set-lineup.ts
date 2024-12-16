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
    prioritizePlayers(players).forEach(({ player, score }) => {
      insertPlayerPredictedScore(player, score);
    });
  } catch (error) {
    console.error(error);
    alert(error);
    throw error;
  }
})();
