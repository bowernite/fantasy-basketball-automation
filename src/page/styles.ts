const PREDICTED_SCORE_TEXT = "rgb(255, 255, 255)"; // White text
const PREDICTED_SCORE_BORDER_DTD = "rgb(204, 85, 0)"; // Darker orange
const PREDICTED_SCORE_BORDER_DEFAULT = "rgb(75, 0, 130)"; // Deep purple

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
  predictedScore: {
    color: PREDICTED_SCORE_TEXT,
    "font-weight": "bold",
    "font-size": "1.1rem",
    padding: "4px 8px",
    "border-radius": "999px",
    "flex-shrink": "0",
    "min-width": "46px",
    "text-align": "center",
    border: `2px solid ${PREDICTED_SCORE_BORDER_DEFAULT}`,
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
  playerStatus: {
    "align-self": "flex-start",
  },
  playerStatusRefined: {
    position: "relative",
    display: "inline-block",
  },
  playerStatusProbable: {
    color: "rgb(255, 255, 0)",
  },
  playerStatusDoubtful: {
    color: "rgb(255, 69, 0)",
  },
  playerStatusOut: {
    color: "rgb(255, 0, 0)",
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
