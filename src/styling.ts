import type { Player } from "./page-querying";

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
 * Alternate player
 *******************************************************************/
const BLUE_OUTLINE = "rgb(0, 200, 255)";
export const stylePlayerAsAlternate = (player: Player) => {
  stylePlayerAsStarted(player);
  player.row.style.outline = `2px solid ${BLUE_OUTLINE}`;
};

/********************************************************************
 * Utils
 *******************************************************************/

const setRowBackgroundColor = (row: HTMLTableRowElement, color: string) => {
  const cells = row.querySelectorAll("td");
  cells.forEach((cell) => {
    cell.style.backgroundColor = color;
  });
};
