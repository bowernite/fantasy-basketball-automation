import type { ScoreWeightingDebugInfo } from "../prioritization/score-weighting";
import { interpolateColors } from "../utils/interpolate-colors";
import {
  getPlayerNameCell,
  getPlayerNameEl,
  PLAYER_STATUS_SELECTOR,
  type Player,
  type PlayerStatus,
  type TimeAgo,
} from "./get-players";
import { saveLineup } from "./page-interaction";
import { applyStyles, SAVE_LINEUP_STYLES, STYLES } from "./styles";

/********************************************************************
 * Starting player
 *******************************************************************/
const GREEN_HIGHLIGHT = "rgba(0, 255, 0, 0.3)";
export const stylePlayerAsStarted = (player: Player) => {
  setRowBackgroundColor(player.row, GREEN_HIGHLIGHT);
};

/********************************************************************
 * Unable to start player
 *******************************************************************/
const GRAY = "rgb(128, 128, 128)";
export const stylePlayerAsUnableToStart = (player: Player) => {
  player.row.style.outline = `2px solid ${GRAY}`;
};

/********************************************************************
 * Possibly injured player
 *******************************************************************/
const ORANGE_HIGHLIGHT = "rgba(255, 165, 0, 0.3)";
const ORANGE_OUTLINE = "rgb(255, 165, 0)";
export const stylePlayerAsPossiblyInjured = (player: Player) => {
  setRowBackgroundColor(player.row, ORANGE_HIGHLIGHT);
  player.row.style.outline = `2px solid ${ORANGE_OUTLINE}`;
};

/********************************************************************
 * Alternate player
 *******************************************************************/
const BLUE_OUTLINE = "rgb(0, 200, 255)";
export const stylePlayerAsAlternate = (player: Player) => {
  stylePlayerAsStarted(player);
  player.row.style.outline = `2px solid ${BLUE_OUTLINE}`;
};

export const insertPlayerPredictedScore = (
  player: Player,
  score: number,
  { debugInfo }: { debugInfo: ScoreWeightingDebugInfo }
) => {
  const { injuryMultiplier, opponentAdjustmentDiff } = debugInfo;
  const cell = getPlayerNameCell(player);
  if (!cell) return;

  let scoreDiv = cell.querySelector<HTMLDivElement>(
    "div[data-predicted-score]"
  );
  if (scoreDiv) {
    scoreDiv.textContent = score.toFixed(1);
  } else {
    applyStyles(cell, STYLES.playerNameCell);

    const nameEl = getPlayerNameEl(player);
    if (nameEl) {
      applyStyles(nameEl, STYLES.playerName);
    }

    scoreDiv = document.createElement("div");
    scoreDiv.setAttribute("data-predicted-score", "");

    // Calculate background color based on score
    const minScore = 15;
    const maxScore = 50;
    const normalizedScore = Math.min(Math.max(score, minScore), maxScore);
    const percentage = (normalizedScore - minScore) / (maxScore - minScore);
    let backgroundColor = interpolateColors(
      {
        start: "rgb(64, 64, 64)", // Dark gray
        end: "rgb(0, 0, 139)", // Deep blue
        stops: [
          { color: "rgb(204, 150, 0)", percentage: 0.2 }, // Darker yellow
          { color: "rgb(0, 100, 0)", percentage: 0.6 }, // Deep green
        ],
      },
      percentage
    );

    applyStyles(scoreDiv, {
      ...STYLES.predictedScore,
      "background-color": backgroundColor,
    });
    const hasGameToday = !!player.todaysGame;
    if (hasGameToday) {
      applyStyles(scoreDiv, STYLES.predictedScoreWithGameToday);

      const isDtd = player.playerStatus === "DTD";
      if (isDtd) {
        applyStyles(scoreDiv, STYLES.predictedScoreWithGameTodayAndDtd);
      }
    }
    scoreDiv.textContent = score.toFixed(1);

    const hasSeasonProjectionAvg = debugInfo.seasonProjectionAvg != null;
    if (!hasSeasonProjectionAvg && debugInfo.seasonProjectionWeight > 0.2) {
      applyStyles(scoreDiv, STYLES.predictedScoreWithNoSeasonProjection);
      scoreDiv.title = `No preseason projection available, and we're weighting a guess of ~20 at ${(
        debugInfo.seasonProjectionWeight * 100
      ).toFixed(0)}%`;
      scoreDiv.textContent = `${score.toFixed(1)} ⚠️`;
    }

    cell.insertBefore(scoreDiv, cell.firstChild);
  }

  scoreDiv.title = "";
  scoreDiv.title =
    opponentAdjustmentDiff == null
      ? "Opponent adjustment: (none)\n"
      : `Opponent adjustment: ${
          opponentAdjustmentDiff > 0 ? "+" : ""
        }${opponentAdjustmentDiff.toFixed(1)}\n`;
  scoreDiv.title += `Injury multiplier: ${
    injuryMultiplier !== 1
      ? (injuryMultiplier * 100).toFixed(0) + "%"
      : "(none)"
  }`;
  if (scoreDiv.title === "") {
    scoreDiv.title = "(no adjustments)";
  }
};

export function refinePlayerStatus(player: Player) {
  const { refinedPlayerStatus: { injuryStatus: status, timeAgo } = {} } =
    player;
  const cell = getPlayerNameCell(player);
  if (!cell) return;

  const statusEl = player.row.querySelector<HTMLDivElement>(
    PLAYER_STATUS_SELECTOR
  );
  if (!statusEl) return;

  // Moves the element to the end of the cell
  cell.appendChild(statusEl);
  applyStyles(statusEl, STYLES.playerStatus);

  if (!status) return;

  statusEl.textContent = status;
  applyStyles(statusEl, STYLES.playerStatusRefined);
  if (status === "P") applyStyles(statusEl, STYLES.playerStatusProbable);
  else if (status === "D") applyStyles(statusEl, STYLES.playerStatusDoubtful);
  else if (status === "OUT") applyStyles(statusEl, STYLES.playerStatusOut);

  if (timeAgo) {
    statusEl.textContent += ` (${timeAgo.value}${timeAgo.unit.charAt(0)})`;
  }

  const sparkleEl = document.createElement("span");
  sparkleEl.textContent = "✨";
  applyStyles(sparkleEl, STYLES.playerStatusSparkle);
  statusEl.prepend(sparkleEl);
}

export function addSaveLineupButton() {
  const style = document.createElement("style");
  style.textContent = SAVE_LINEUP_STYLES;
  document.head.appendChild(style);

  const button = document.createElement("button");
  button.className = "save-lineup-button";

  const innerButton = document.createElement("div");
  innerButton.className = "save-lineup-button__inner";
  innerButton.textContent = "Save Lineup";

  button.appendChild(innerButton);
  document.body.appendChild(button);

  button.addEventListener("click", () => {
    saveLineup();
  });
}

/********************************************************************
 * Utils
 *******************************************************************/

const setRowBackgroundColor = (row: HTMLTableRowElement, color: string) => {
  const cells = row.querySelectorAll("td");
  cells.forEach((cell) => {
    cell.style.backgroundColor = color;
  });
};
