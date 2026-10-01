import { getPlayers } from "./src/page/get-players";
import { randomPageStylings } from "./src/page/page-manipulation";
import { addLineupActions, runSaveLineup, runSetLineup } from "./src/page/overlay/lineup-actions";
import { insertPlayerScores } from "./src/page/overlay/score-rail";
import { refinePlayerStatus } from "./src/page/overlay/status-tag";
import { injectOverlayStyles } from "./src/page/overlay/styles";
import { hasEditableLineup } from "./src/page/page-querying";
import { prioritizePlayers } from "./src/prioritization/prioritization";
import { goToNextDay, goToPreviousDay } from "./src/lineup/lineup-dom-actions";
import { setProblemHandler } from "./src/lineup/report-problem";
import { showNotice } from "./src/page/overlay/notice";

setProblemHandler((message) => showNotice({ kind: "error", message }));

(window as any).runSetLineup = runSetLineup;
(window as any).saveLineup = runSaveLineup;
(window as any).goToPreviousDay = goToPreviousDay;
(window as any).goToNextDay = goToNextDay;

injectOverlayStyles();
pageLoad();
randomPageStylings();

async function pageLoad() {
  try {
    if (hasEditableLineup()) {
      addLineupActions();
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
    showNotice({
      kind: "error",
      message: `Couldn't read the roster page; the lineup wasn't changed. ${error instanceof Error ? error.message : error}`,
      action: { label: "Reload page", onClick: () => location.reload() },
    });
    throw error;
  }
}
