import type { ScoreWeightingDebugInfo } from "../../prioritization/score-weighting";
import { NO_PROJECTION_RATE } from "../../data/player-data";
import type { Player } from "../../types";
import { getPlayerNameCell } from "../page-querying";

export const SCORE_RAIL_CSS = "";

const PX_PER_POINT = 2;
const RAIL_MAX_POINTS = 60;

let popoverCount = 0;

type ScoreAdjustments = Pick<
  ScoreWeightingDebugInfo,
  "injuryMultiplier" | "opponentAdjustmentDiff" | "seasonProjectionAvg" | "seasonProjectionWeight"
>;

export const insertPlayerScores = ({
  player,
  weightedScore,
  predictedScore,
  debugInfo,
}: {
  player: Player;
  weightedScore: number | null;
  predictedScore: number;
  debugInfo: ScoreAdjustments;
}) => {
  const cell = getPlayerNameCell(player);
  if (!cell) return;

  const hasGameToday = !!player.todaysGame;

  const score = element("div", "ffx-score");
  score.setAttribute("data-scores-container", "");
  score.tabIndex = 0;
  score.append(element("span", "ffx-score__today", hasGameToday ? predictedScore.toFixed(1) : "–"));
  if (isMostlyGuessed(debugInfo)) score.append(element("span", "ffx-score__est", "est"));

  const rail = element("span", "ffx-rail");
  if (hasGameToday) {
    const bar = element("span", `ffx-rail__bar ffx-rail__bar--${band(predictedScore)}`);
    bar.style.width = `${railOffset(predictedScore)}px`;
    bar.classList.toggle("ffx-rail__bar--capped", predictedScore > RAIL_MAX_POINTS);
    bar.classList.toggle("ffx-rail__bar--dtd", player.playerStatus === "DTD");
    rail.append(bar);
  }
  if (weightedScore != null) {
    const tick = element("span", "ffx-rail__tick");
    tick.style.left = `${railOffset(weightedScore)}px`;
    rail.append(tick);
  }
  score.append(rail);
  if (weightedScore != null) score.append(element("span", "ffx-score__season", weightedScore.toFixed(1)));

  const popover = createPopover({ today: hasGameToday ? predictedScore : null, season: weightedScore, debugInfo });
  score.setAttribute("aria-describedby", popover.id);
  score.append(popover);

  const existing = cell.querySelector("[data-scores-container]");
  if (existing) existing.replaceWith(score);
  else cell.insertBefore(score, cell.firstChild);
};

// Never class it `tooltip`: Fleaflicker's news reader looks for `.tooltip` in the row
function createPopover({
  today,
  season,
  debugInfo,
}: {
  today: number | null;
  season: number | null;
  debugInfo: ScoreAdjustments;
}) {
  const { opponentAdjustmentDiff, injuryMultiplier, seasonProjectionWeight } = debugInfo;
  const popover = element("div", "ffx-popover");
  popover.id = `ffx-score-popover-${++popoverCount}`;
  popover.setAttribute("role", "tooltip");

  const rows: [string, string][] = [
    ["Today", today == null ? "No game" : today.toFixed(1)],
    ["Season", season == null ? "–" : season.toFixed(1)],
    ["Opponent", opponentAdjustmentDiff == null ? "none" : signed(opponentAdjustmentDiff)],
  ];
  if (injuryMultiplier !== 1) rows.push(["Injury", `×${Number(injuryMultiplier.toFixed(2))}`]);

  for (const [label, value] of rows) {
    const row = element("div", "ffx-popover__row");
    row.append(element("span", "ffx-popover__label", label), element("span", "ffx-popover__value", value));
    popover.append(row);
  }
  if (isMostlyGuessed(debugInfo)) {
    const guessWeight = (seasonProjectionWeight * 100).toFixed(0);
    popover.append(
      element("p", "ffx-popover__note", `No preseason projection, so a guess of ~${NO_PROJECTION_RATE.toFixed(1)} is weighted at ${guessWeight}%`)
    );
  }
  return popover;
}

function isMostlyGuessed({ seasonProjectionAvg, seasonProjectionWeight }: ScoreAdjustments) {
  return seasonProjectionAvg == null && seasonProjectionWeight > 0.2;
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}`;
}

// Roughly the top 30 / 100 / 200 players by season projection
function band(today: number) {
  if (today >= 40) return "star";
  if (today >= 30) return "start";
  if (today >= 20) return "fringe";
  return "sit";
}

function railOffset(points: number) {
  return Math.min(Math.max(points, 0), RAIL_MAX_POINTS) * PX_PER_POINT;
}

function element(tag: string, className: string, text?: string) {
  const el = document.createElement(tag);
  el.className = className;
  if (text != null) el.textContent = text;
  return el;
}
