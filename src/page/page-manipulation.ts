import { getPlayersTable } from "./page-querying";

export {
  stylePlayerAsAlternate,
  stylePlayerAsPossiblyInjured,
  stylePlayerAsStarted,
  stylePlayerAsUnableToStart,
} from "./overlay/row-states";

export function randomPageStylings() {
  const playersTable = getPlayersTable();
  playersTable.style.maxWidth = "1200px";
}
