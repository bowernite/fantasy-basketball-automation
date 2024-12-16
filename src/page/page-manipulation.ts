import { interpolateColors } from "../utils/interpolate-colors";
import type { Player, PlayerStatus, TimeAgo } from "./get-players";
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
export const insertPlayerPredictedScore = (player: Player, score: number) => {
  const cell = player.row.querySelector("td:first-child");
  if (!cell || !(cell instanceof HTMLTableCellElement)) {
    return;
  }

  const existingScoreDiv = cell.querySelector("div[data-predicted-score]");
  if (existingScoreDiv) {
    existingScoreDiv.textContent = score.toFixed(1);
  } else {
    // Set display flex on cell to align items horizontally
    cell.style.display = "flex";
    cell.style.alignItems = "center";

    const scoreDiv = document.createElement("div");
    scoreDiv.setAttribute("data-predicted-score", "");

    // Calculate background color based on score
    const normalizedScore = Math.min(Math.max(score, MIN_SCORE), MAX_SCORE);
    const percentage = (normalizedScore - MIN_SCORE) / (MAX_SCORE - MIN_SCORE);
    const backgroundColor = interpolateColors(
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
    const hasGameToday = !!player.todaysGame;
    if (hasGameToday) {
      const isDtd = player.playerStatus === "DTD";
      scoreDiv.style.border = `2px solid ${
        isDtd ? PREDICTED_SCORE_BORDER_DTD : PREDICTED_SCORE_BORDER_DEFAULT
      }`;
      scoreDiv.style.boxShadow = "0 2px 4px rgba(0, 0, 0, 0.2)";
    }
    scoreDiv.textContent = score.toFixed(1);
    cell.insertBefore(scoreDiv, cell.firstChild);
  }
};

export function insertRefinedPlayerStatus(
  player: Player,
  status: PlayerStatus,
  timeAgo: TimeAgo
) {
  const cell = player.row.querySelector("td:first-child");
  if (!cell || !(cell instanceof HTMLTableCellElement)) {
    return;
  }

  const existingStatusDiv = cell.querySelector(
    "div[data-refined-player-status]"
  );
  if (existingStatusDiv) {
    existingStatusDiv.textContent = status;
  }
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
