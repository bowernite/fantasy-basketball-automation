import type { ScoreWeightingDebugInfo } from "../score-weighting";
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
const GRAYED_OUT = "rgb(235, 235, 235)";
const GRAY = "rgb(128, 128, 128)";
export const stylePlayerAsUnableToStart = (player: Player) => {
  // setRowBackgroundColor(player.row, GRAYED_OUT);
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

/********************************************************************
 * Predicted score
 *******************************************************************/
const MIN_SCORE = 15;
const MAX_SCORE = 50;
const PREDICTED_SCORE_TEXT = "rgb(255, 255, 255)"; // White text
const PREDICTED_SCORE_BORDER_DTD = "rgb(204, 85, 0)"; // Darker orange
const PREDICTED_SCORE_BORDER_DEFAULT = "rgb(75, 0, 130)"; // Deep purple
const LOW_SCORE_COLOR = "rgb(204, 150, 0)"; // Darker yellow
const HIGH_SCORE_COLOR = "rgb(46, 125, 50)"; // Deep green
export const insertPlayerPredictedScore = (
  player: Player,
  score: number,
  { debugInfo }: { debugInfo: ScoreWeightingDebugInfo }
) => {
  const cell = getPlayerNameCell(player);
  if (!cell) return;

  const existingScoreDiv = cell.querySelector("div[data-predicted-score]");
  if (existingScoreDiv) {
    existingScoreDiv.textContent = score.toFixed(1);
  } else {
    // Set display flex on cell to align items horizontally
    cell.style.display = "flex";
    cell.style.alignItems = "center";
    cell.style.gap = "4px";

    const nameEl = getPlayerNameEl(player);
    if (nameEl) {
      nameEl.style.marginLeft = "8px";
    }

    const scoreDiv = document.createElement("div");
    scoreDiv.setAttribute("data-predicted-score", "");

    // Calculate background color based on score
    const normalizedScore = Math.min(Math.max(score, MIN_SCORE), MAX_SCORE);
    const percentage = (normalizedScore - MIN_SCORE) / (MAX_SCORE - MIN_SCORE);
    let backgroundColor = interpolateColors(
      LOW_SCORE_COLOR,
      HIGH_SCORE_COLOR,
      percentage
    );

    scoreDiv.style.backgroundColor = backgroundColor;
    scoreDiv.style.color = PREDICTED_SCORE_TEXT;
    scoreDiv.style.fontWeight = "bold";
    scoreDiv.style.fontSize = "1.1rem";
    scoreDiv.style.padding = "4px 8px";
    scoreDiv.style.borderRadius = "999px";
    scoreDiv.style.flexShrink = "0";
    scoreDiv.style.minWidth = "46px";
    scoreDiv.style.textAlign = "center";
    const hasGameToday = !!player.todaysGame;
    if (hasGameToday) {
      const isDtd = player.playerStatus === "DTD";
      scoreDiv.style.border = `2px solid ${
        isDtd ? PREDICTED_SCORE_BORDER_DTD : PREDICTED_SCORE_BORDER_DEFAULT
      }`;
      scoreDiv.style.boxShadow = "0 2px 4px rgba(0, 0, 0, 0.2)";
    }
    scoreDiv.textContent = score.toFixed(1);

    const hasSeasonProjectionAvg = debugInfo.seasonProjectionAvg != null;
    if (!hasSeasonProjectionAvg && debugInfo.seasonProjectionWeight > 0.2) {
      scoreDiv.style.backgroundColor = "rgb(255, 0, 0)";
      scoreDiv.title = `No preseason projection available, and we're weighting a guess of ~20 at ${(
        debugInfo.seasonProjectionWeight * 100
      ).toFixed(0)}%`;
      scoreDiv.textContent = `${score.toFixed(1)} ⚠️`;
    }

    cell.insertBefore(scoreDiv, cell.firstChild);
  }
};

export function refinePlayerStatus(
  player: Player,
  status: PlayerStatus | undefined,
  timeAgo: TimeAgo | undefined
) {
  const cell = getPlayerNameCell(player);
  if (!cell) return;

  const statusEl = player.row.querySelector<HTMLDivElement>(
    PLAYER_STATUS_SELECTOR
  );
  if (!statusEl) return;

  // Moves the element to the end of the cell
  cell.appendChild(statusEl);
  statusEl.style.alignSelf = "flex-start";

  if (!status) return;

  statusEl.textContent = status;
  statusEl.style.fontWeight = "bold";
  statusEl.style.position = "relative";
  statusEl.style.display = "inline-block";
  statusEl.style.paddingRight = ".5em";

  if (timeAgo) {
    statusEl.textContent += ` (${timeAgo.value}${timeAgo.unit.charAt(0)})`;
  }

  const sparkleEl = document.createElement("span");
  sparkleEl.textContent = "✨";
  sparkleEl.style.position = "absolute";
  sparkleEl.style.top = "0";
  sparkleEl.style.right = "0";
  sparkleEl.style.fontSize = "0.8em";
  statusEl.appendChild(sparkleEl);
}

export function addSaveLineupButton() {
  const style = document.createElement("style");
  style.textContent = `
  .save-lineup-button {
    position: fixed;
    top: 6px;
    right: 210px;
    padding: 2px;
    background: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
    z-index: 9999;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    background-image: linear-gradient(45deg, #FF6B6B, #4ECDC4);
    transition: all 0.2s ease-in-out;
  }

  .save-lineup-button:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
  }

  .save-lineup-button__inner {
    background: white;
    padding: 8px 18px;
    border-radius: 6px;
  }

  .save-lineup-button__inner:hover {
    background: #f5f5f5;
  }
`;
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
