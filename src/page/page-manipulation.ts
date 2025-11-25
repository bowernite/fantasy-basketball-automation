import type { ScoreWeightingDebugInfo } from "../prioritization/score-weighting";
import { interpolateColors } from "../utils/interpolate-colors";
import type { Player } from "../types";
import { saveLineup } from "../lineup/lineup-dom-actions";
import {
  getPlayersTable,
  getPlayerNameCell,
  getPlayerNameEl,
  PLAYER_STATUS_SELECTOR,
} from "./page-querying";
import {
  applyStyles,
  generateScoreColor,
  SAVE_LINEUP_STYLES,
  STYLES,
} from "./styles";
import { saveLineupIcon, setLineupIcon } from "../icons/icons";
import { setLineup } from "../lineup/set-lineup";

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
  console.log("stylePlayerAsUnableToStart", player);
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
  console.log("stylePlayerAsAlternate", player);
  stylePlayerAsStarted(player);
  player.row.style.outline = `2px solid ${BLUE_OUTLINE}`;
};

/********************************************************************
 * Score pills
 *******************************************************************/

export const insertPlayerScores = ({
  player,
  weightedScore,
  predictedScore,
  debugInfo,
}: {
  player: Player;
  weightedScore: number | null;
  predictedScore: number;
  debugInfo: ScoreWeightingDebugInfo;
}) => {
  const { injuryMultiplier, opponentAdjustmentDiff } = debugInfo;

  const cell = getPlayerNameCell(player);
  if (!cell) return;

  const existingContainer = cell.querySelector<HTMLDivElement>(
    "div[data-scores-container]"
  );

  const predictedScoreDiv = existingContainer
    ? updateExistingScores(existingContainer, weightedScore, predictedScore)
    : createScoresDisplay(
        cell,
        player,
        weightedScore,
        predictedScore,
        debugInfo
      );

  setScoreTooltip(
    predictedScoreDiv,
    debugInfo,
    injuryMultiplier,
    opponentAdjustmentDiff
  );
};

function updateExistingScores(
  container: HTMLDivElement,
  weightedScore: number | null,
  predictedScore: number
) {
  const baseScoreDiv = container.querySelector<HTMLDivElement>(
    "div[data-base-score]"
  )!;
  const predictedScoreDiv = container.querySelector<HTMLDivElement>(
    "div[data-predicted-score]"
  )!;

  if (weightedScore != null) {
    baseScoreDiv.textContent = weightedScore.toFixed(1);
  }
  predictedScoreDiv.textContent = predictedScore.toFixed(1);

  return predictedScoreDiv;
}

function createBaseScoreDiv(
  weightedScore: number | null,
  predictedScore: number
) {
  const baseScoreDiv = document.createElement("div");
  baseScoreDiv.setAttribute("data-base-score", "");
  const baseBackgroundColor =
    weightedScore != null
      ? generateScoreColor(weightedScore)
      : generateScoreColor(predictedScore);
  applyStyles(baseScoreDiv, {
    ...STYLES.scorePill,
    "background-color": baseBackgroundColor,
  });
  if (weightedScore != null) {
    baseScoreDiv.textContent = weightedScore.toFixed(1);
  }
  return baseScoreDiv;
}

function createSeparatorDiv() {
  const separatorDiv = document.createElement("div");
  separatorDiv.setAttribute("data-separator", "");
  separatorDiv.textContent = "/";
  applyStyles(separatorDiv, STYLES.scoreSeparator);
  return separatorDiv;
}

function createPredictedScoreDiv(predictedScore: number) {
  const predictedScoreDiv = document.createElement("div");
  predictedScoreDiv.setAttribute("data-predicted-score", "");
  const predictedScoreBgColor = generateScoreColor(predictedScore);
  applyStyles(predictedScoreDiv, {
    ...STYLES.scorePill,
    "background-color": predictedScoreBgColor,
  });
  predictedScoreDiv.textContent = predictedScore.toFixed(1) + " ✨";
  return predictedScoreDiv;
}

function applyPredictedScoreConditionalStyles(
  predictedScoreDiv: HTMLDivElement,
  player: Player,
  predictedScore: number,
  debugInfo: ScoreWeightingDebugInfo
) {
  const hasGameToday = !!player.todaysGame;
  if (hasGameToday) {
    applyStyles(predictedScoreDiv, STYLES.predictedScoreWithGameToday);

    const isDtd = player.playerStatus === "DTD";
    if (isDtd) {
      applyStyles(predictedScoreDiv, STYLES.predictedScoreWithGameTodayAndDtd);
    }
  }

  const hasSeasonProjectionAvg = debugInfo.seasonProjectionAvg != null;
  if (!hasSeasonProjectionAvg && debugInfo.seasonProjectionWeight > 0.2) {
    applyStyles(predictedScoreDiv, STYLES.predictedScoreWithNoSeasonProjection);
    predictedScoreDiv.textContent = `${predictedScore.toFixed(1)} ⚠️`;
  }
}

function createScoresDisplay(
  cell: HTMLTableCellElement,
  player: Player,
  weightedScore: number | null,
  predictedScore: number,
  debugInfo: ScoreWeightingDebugInfo
) {
  applyStyles(cell, STYLES.playerNameCell);

  const nameEl = getPlayerNameEl(player);
  if (nameEl) {
    applyStyles(nameEl, STYLES.playerName);
  }

  const container = document.createElement("div");
  container.setAttribute("data-scores-container", "");
  applyStyles(container, STYLES.scoresContainer);

  const predictedScoreDiv = createPredictedScoreDiv(predictedScore);
  applyPredictedScoreConditionalStyles(
    predictedScoreDiv,
    player,
    predictedScore,
    debugInfo
  );

  container.appendChild(predictedScoreDiv);

  if (weightedScore != null) {
    const separatorDiv = createSeparatorDiv();
    const baseScoreDiv = createBaseScoreDiv(weightedScore, predictedScore);
    container.appendChild(separatorDiv);
    container.appendChild(baseScoreDiv);
  }

  cell.insertBefore(container, cell.firstChild);

  return predictedScoreDiv;
}

function setScoreTooltip(
  predictedScoreDiv: HTMLDivElement,
  debugInfo: ScoreWeightingDebugInfo,
  injuryMultiplier: number,
  opponentAdjustmentDiff: number | null | undefined
) {
  const hasSeasonProjectionAvg = debugInfo.seasonProjectionAvg != null;
  predictedScoreDiv.title = "";

  if (!hasSeasonProjectionAvg && debugInfo.seasonProjectionWeight > 0.2) {
    predictedScoreDiv.title = `No preseason projection available, and we're weighting a guess of ~20 at ${(
      debugInfo.seasonProjectionWeight * 100
    ).toFixed(0)}%\n`;
  }

  predictedScoreDiv.title +=
    opponentAdjustmentDiff == null
      ? "Opponent adjustment: (none)\n"
      : `Opponent adjustment: ${
          opponentAdjustmentDiff > 0 ? "+" : ""
        }${opponentAdjustmentDiff.toFixed(1)}\n`;

  predictedScoreDiv.title += `Injury multiplier: ${
    injuryMultiplier !== 1
      ? (injuryMultiplier * 100).toFixed(0) + "%"
      : "(none)"
  }`;
}

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
  if (!document.head.querySelector('style[data-button-styles]')) {
    const style = document.createElement("style");
    style.textContent = SAVE_LINEUP_STYLES;
    style.setAttribute('data-button-styles', '');
    document.head.appendChild(style);
  }

  const button = document.createElement("button");
  button.className = "save-lineup-button";

  const innerButton = document.createElement("div");
  innerButton.className = "save-lineup-button__inner";
  
  const iconDiv = document.createElement("div");
  iconDiv.className = "save-lineup-button__icon";
  iconDiv.innerHTML = saveLineupIcon;
  
  const textSpan = document.createElement("span");
  textSpan.textContent = "Save Lineup";
  
  innerButton.appendChild(iconDiv);
  innerButton.appendChild(textSpan);

  button.appendChild(innerButton);
  document.body.appendChild(button);

  button.addEventListener("click", () => {
    saveLineup();
  });
}

export async function addSetLineupButton() {
  if (!document.head.querySelector('style[data-button-styles]')) {
    const style = document.createElement("style");
    style.textContent = SAVE_LINEUP_STYLES;
    style.setAttribute('data-button-styles', '');
    document.head.appendChild(style);
  }

  const button = document.createElement("button");
  button.className = "set-lineup-button";

  const innerButton = document.createElement("div");
  innerButton.className = "set-lineup-button__inner";
  
  const iconDiv = document.createElement("div");
  iconDiv.className = "set-lineup-button__icon";
  iconDiv.innerHTML = setLineupIcon;
  
  const textSpan = document.createElement("span");
  textSpan.textContent = "Set Lineup";
  
  innerButton.appendChild(iconDiv);
  innerButton.appendChild(textSpan);

  button.appendChild(innerButton);
  document.body.appendChild(button);

  button.addEventListener("click", async () => {
    try {
      await setLineup();
    } catch (error) {
      console.error("Error setting lineup:", error);
      alert(`Error setting lineup: ${error}`);
    }
  });
}

export function randomPageStylings() {
  const playersTable = getPlayersTable();
  playersTable.style.maxWidth = "1200px";
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
