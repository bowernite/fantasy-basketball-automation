import type { Player } from "./page";

const ALTERNATE_COLOR = "rgba(255, 255, 0, 0.3)";
const OUTLINE_COLOR = "rgb(0, 200, 255)";
const SELECTED_COLOR = "rgba(0, 255, 0, 0.3)";
const UNABLE_TO_START_COLOR = "rgba(255, 0, 0, 0.15)";

const setRowBackgroundColor = (row: HTMLTableRowElement, color: string) => {
  const cells = row.querySelectorAll("td");
  cells.forEach((cell) => {
    cell.style.backgroundColor = color;
  });
};

export const stylePlayerAsAlternate = (player: Player) => {
  setRowBackgroundColor(player.row, ALTERNATE_COLOR);
  player.row.style.outline = `2px solid ${OUTLINE_COLOR}`;
  setTimeout(() => {
    setRowBackgroundColor(player.row, ALTERNATE_COLOR);
  }, 1000);
};

export const stylePlayerAsSelected = (player: Player) => {
  setRowBackgroundColor(player.row, SELECTED_COLOR);
};

export const stylePlayerAsUnableToStart = (player: Player) => {
  setRowBackgroundColor(player.row, UNABLE_TO_START_COLOR);
  player.row.style.outline = `2px solid red`;
};
