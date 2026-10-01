import type { ScoreWeightingDebugInfo } from "../../prioritization/score-weighting";
import { NO_PROJECTION_RATE } from "../../data/player-data";
import type { Player } from "../../types";
import { getPlayerNameCell } from "../page-querying";

export const SCORE_RAIL_CSS = `
  td:has(> .ffx-score) { display: flex; align-items: center; gap: 8px; }
  .ffx-score {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
    font-variant-numeric: tabular-nums;
    cursor: default;
  }
  .ffx-score:focus-visible { outline: 2px solid var(--ffx-focus); outline-offset: 2px; border-radius: var(--ffx-radius-sm); }
  .ffx-score__today { min-width: 2.4em; text-align: right; font-size: 16px; font-weight: 700; color: var(--ffx-ink); }
  .ffx-score__today--none { font-weight: 400; color: var(--ffx-muted); }
  .ffx-score__est { font-size: 11px; color: var(--ffx-orange-text); }
  .ffx-score__season {
    position: absolute;
    bottom: calc(100% + 1px);
    left: 50%;
    transform: translateX(-50%);
    font-size: 12px;
    line-height: 1;
    white-space: nowrap;
    color: var(--ffx-muted);
  }
  .ffx-rail {
    position: relative;
    width: 120px;
    height: 8px;
    margin: 0 4px;
    background:
      linear-gradient(#fff, #fff) 40px 0 / 1px 100% no-repeat,
      linear-gradient(#fff, #fff) 60px 0 / 1px 100% no-repeat,
      linear-gradient(#fff, #fff) 80px 0 / 1px 100% no-repeat,
      var(--ffx-track);
    border-radius: var(--ffx-radius-sm);
  }
  .ffx-rail__bar { position: absolute; top: 0; bottom: 0; left: 0; border-radius: var(--ffx-radius-sm); }
  .ffx-rail__bar--sit { background-color: var(--ffx-band-sit); }
  .ffx-rail__bar--fringe { background-color: var(--ffx-band20); }
  .ffx-rail__bar--start { background-color: var(--ffx-band30); }
  .ffx-rail__bar--star { background-color: var(--ffx-band40); }
  .ffx-rail__bar--capped { box-shadow: inset -2px 0 0 var(--ffx-ink); }
  .ffx-rail__bar--dtd { background-image: repeating-linear-gradient(135deg, transparent 0 3px, #fff 3px 5px); }
  .ffx-rail__tick {
    position: absolute;
    top: 50%;
    z-index: 1;
    width: 2px;
    height: 14px;
    background: var(--ffx-ink);
    transform: translate(-1px, -50%);
  }
  .ffx-score-key { display: block; font-size: 11px; font-weight: 400; color: var(--ffx-muted); white-space: pre; }
  .ffx-popover {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    z-index: 20;
    min-width: 180px;
    padding: 8px 12px;
    background: #fff;
    border-radius: var(--ffx-radius);
    box-shadow: 0 1px 2px rgba(0, 56, 110, 0.12), 0 4px 12px rgba(0, 56, 110, 0.14);
    font-size: 12px;
    font-weight: 400;
    color: var(--ffx-ink);
    visibility: hidden;
    opacity: 0;
    transform: translateY(-2px);
    transition-property: opacity, transform, visibility;
    transition-duration: var(--ffx-duration);
    transition-timing-function: var(--ffx-ease);
  }
  .ffx-score:hover > .ffx-popover,
  .ffx-score:focus > .ffx-popover { visibility: visible; opacity: 1; transform: none; }
  .ffx-popover__row { display: flex; justify-content: space-between; gap: 12px; }
  .ffx-popover__label { color: var(--ffx-muted); }
  .ffx-popover__note { margin: 4px 0 0; color: var(--ffx-orange-text); }
`;

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
  addScoreKey(player.row);

  const hasGameToday = !!player.todaysGame;

  const score = element("div", "ffx-score");
  score.setAttribute("data-scores-container", "");
  score.tabIndex = 0;
  score.appendChild(
    hasGameToday
      ? element("span", "ffx-score__today", predictedScore.toFixed(1))
      : element("span", "ffx-score__today ffx-score__today--none", "–")
  );
  if (isMostlyGuessed(debugInfo)) score.appendChild(element("span", "ffx-score__est", "est"));

  const rail = element("span", "ffx-rail");
  if (hasGameToday) {
    const bar = element("span", `ffx-rail__bar ffx-rail__bar--${band(predictedScore)}`);
    bar.style.width = `${railOffset(predictedScore)}px`;
    bar.classList.toggle("ffx-rail__bar--capped", predictedScore > RAIL_MAX_POINTS);
    bar.classList.toggle("ffx-rail__bar--dtd", player.playerStatus === "DTD");
    rail.appendChild(bar);
  }
  if (weightedScore != null) {
    const tick = element("span", "ffx-rail__tick");
    tick.style.left = `${railOffset(weightedScore)}px`;
    tick.appendChild(element("span", "ffx-score__season", weightedScore.toFixed(1)));
    rail.appendChild(tick);
  }
  score.appendChild(rail);

  const popover = createPopover({ today: hasGameToday ? predictedScore : null, season: weightedScore, debugInfo });
  score.setAttribute("aria-describedby", popover.id);
  score.appendChild(popover);

  const existing = cell.querySelector("[data-scores-container]");
  if (existing) existing.replaceWith(score);
  else cell.insertBefore(score, cell.firstChild);
};

function addScoreKey(row: HTMLTableRowElement) {
  const nameHeader = row.closest("table")?.querySelector("thead span.player")?.closest("th");
  if (!nameHeader || nameHeader.querySelector(".ffx-score-key")) return;
  nameHeader.appendChild(element("span", "ffx-score-key", "Today (bar)  Season (tick)"));
}

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
    row.appendChild(element("span", "ffx-popover__label", label));
    row.appendChild(element("span", "ffx-popover__value", value));
    popover.appendChild(row);
  }
  if (isMostlyGuessed(debugInfo)) {
    const guessWeight = (seasonProjectionWeight * 100).toFixed(0);
    popover.appendChild(
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
