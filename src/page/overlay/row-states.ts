import type { Player } from "../../types";

// Selectors outrank the host's zebra and hover rules; risk comes after started so it wins when a row has both
export const ROW_STATES_CSS = `
  .table-striped > tbody > tr.ffx-row--started > td { background-color: var(--ffx-row-started); }
  .table-striped > tbody > tr.ffx-row--risk > td { background-color: var(--ffx-row-risk); }
  .table-striped > tbody > tr.ffx-row--alternate { outline: 1px dashed var(--ffx-band20); outline-offset: -1px; }
  .table-striped > tbody > tr.ffx-row--unable > td { opacity: 0.55; }
`;

export const stylePlayerAsStarted = (player: Player) => {
  player.row.classList.add("ffx-row--started");
};

export const stylePlayerAsUnableToStart = (player: Player) => {
  player.row.classList.add("ffx-row--unable");
};

export const stylePlayerAsPossiblyInjured = (player: Player) => {
  player.row.classList.add("ffx-row--risk");
};

export const stylePlayerAsAlternate = (player: Player) => {
  stylePlayerAsStarted(player);
  player.row.classList.add("ffx-row--alternate");
};
