import type { Player } from "./page";

const ALTERNATE_COLOR = "rgba(0, 255, 255, 0.3)";
const OUTLINE_COLOR = "rgb(0, 200, 255)";
const SELECTED_COLOR = "rgba(0, 255, 0, 0.3)";
const WARNING_COLOR = "rgba(255, 0, 0, 0.3)";

export const stylePlayerAsAlternate = (player: Player) => {
  player.row.style.backgroundColor = ALTERNATE_COLOR;
  player.row.style.outline = `2px solid ${OUTLINE_COLOR}`;
  setTimeout(() => {
    player.row.style.backgroundColor = ALTERNATE_COLOR;
  }, 1000);
};

export const stylePlayerAsSelected = (player: Player) => {
  player.row.style.backgroundColor = SELECTED_COLOR;
};

export const stylePlayerAsWarning = (player: Player) => {
  player.row.style.backgroundColor = WARNING_COLOR;
};
