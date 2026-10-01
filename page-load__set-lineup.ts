import { getPlayers } from "./src/page/get-players";
import { randomPageStylings } from "./src/page/page-manipulation";
import { addSaveLineupButton, addSetLineupButton } from "./src/page/overlay/lineup-actions";
import { insertPlayerScores } from "./src/page/overlay/score-rail";
import { refinePlayerStatus } from "./src/page/overlay/status-tag";
import { injectOverlayStyles } from "./src/page/overlay/styles";
import { hasEditableLineup } from "./src/page/page-querying";
import { prioritizePlayers } from "./src/prioritization/prioritization";
import {
  goToNextDay,
  goToPreviousDay,
  saveLineup,
} from "./src/lineup/lineup-dom-actions";

// Run by the save shortcut, whose errors only reach the console
(window as any).saveLineup = () => {
  try {
    saveLineup();
  } catch (error) {
    alert(error);
    throw error;
  }
};
(window as any).goToPreviousDay = goToPreviousDay;
(window as any).goToNextDay = goToNextDay;

injectOverlayStyles();
pageLoad();
randomPageStylings();

async function pageLoad() {
  try {
    if (hasEditableLineup()) {
      addSaveLineupButton();
      addSetLineupButton();
    }

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
