import { getPlayers } from "./src/page/get-players";
import {
  addSaveLineupButton,
  addSetLineupButton,
  insertPlayerScores,
  randomPageStylings,
  refinePlayerStatus,
} from "./src/page/page-manipulation";
import { prioritizePlayers } from "./src/prioritization/prioritization";
import { saveLineup } from "./src/lineup/lineup-dom-actions";

(window as any).saveLineup = saveLineup;

pageLoad();
randomPageStylings();

async function pageLoad() {
  addSaveLineupButton();
  addSetLineupButton();

  try {
    const players = await getPlayers();
    prioritizePlayers(players).forEach(
      ({ player, predictedScore, weightedScore, debugInfo }) => {
        insertPlayerScores({
          player,
          weightedScore,
          predictedScore: player.todaysGame ? predictedScore : 0,
          debugInfo,
        });
        refinePlayerStatus(player);
      }
    );
  } catch (error) {
    console.error(error);
    alert(error);
    throw error;
  }
}
