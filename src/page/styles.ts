import { interpolateColors } from "../utils/interpolate-colors";

const PREDICTED_SCORE_TEXT = "rgb(255, 255, 255)"; // White text
const PREDICTED_SCORE_BORDER_DTD = "rgb(204, 85, 0)"; // Darker orange

export function applyStyles(
  element: HTMLElement,
  styles: Record<string, string>
) {
  Object.entries(styles).forEach(([key, value]) => {
    element.style.setProperty(key, value);
  });
}

export const STYLES = {
  playerNameCell: {
    display: "flex",
    "align-items": "center",
    gap: "4px",
  },
  playerName: {
    "margin-left": "8px",
  },
  scorePill: {
    color: PREDICTED_SCORE_TEXT,
    "font-weight": "bold",
    "font-size": "1.1rem",
    padding: "4px 8px",
    "border-radius": "999px",
    "flex-shrink": "0",
    "min-width": "8ch",
    "text-align": "center",
    border: `2px solid transparent`,
  },
  predictedScoreWithGameToday: {
    "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.2)",
  },
  predictedScoreWithGameTodayAndDtd: {
    border: `2px solid ${PREDICTED_SCORE_BORDER_DTD}`,
  },
  predictedScoreWithNoSeasonProjection: {
    "background-color": "rgb(255, 0, 0)",
  },
  scoresContainer: {
    display: "flex",
    "align-items": "center",
    gap: "6px",
    "flex-shrink": "0",
  },
  scoreSeparator: {
    color: "rgb(64, 64, 64)",
    "font-weight": "bold",
    "font-size": "1.1rem",
  },
  playerStatus: {
    "align-self": "flex-start",
  },
  playerStatusRefined: {
    position: "relative",
    display: "inline-block",
  },
  playerStatusProbable: {
    color: "rgb(46, 125, 50)", // Deep green
  },
  playerStatusDoubtful: {
    color: "rgb(255, 69, 0)", // Orange red
  },
  playerStatusOut: {
    color: "rgb(255, 0, 0)", // Red
  },
  playerStatusSparkle: {
    "margin-right": "4px",
  },
};

export const SAVE_LINEUP_STYLES = `
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

export function generateScoreColor(score: number) {
  const minScore = 15;
  const maxScore = 50;
  const normalizedScore = Math.min(Math.max(score, minScore), maxScore);
  const percentage = (normalizedScore - minScore) / (maxScore - minScore);
  return interpolateColors(
    {
      start: "rgb(64, 64, 64)",
      end: "rgb(0, 0, 139)",
      stops: [
        { color: "rgb(204, 150, 0)", percentage: 0.2 },
        { color: "rgb(0, 100, 0)", percentage: 0.6 },
      ],
    },
    percentage
  );
}
