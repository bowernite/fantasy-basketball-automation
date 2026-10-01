import type { Player, PlayerStatus } from "../../types";
import { PLAYER_STATUS_SELECTOR } from "../page-querying";

type StatusTone = "risk" | "muted" | "ok";

const STATUS_WORDS: Record<PlayerStatus, { word: string; tone: StatusTone }> = {
  OUT: { word: "Out", tone: "risk" },
  OFS: { word: "Out for season", tone: "risk" },
  D: { word: "Doubtful", tone: "risk" },
  Q: { word: "Questionable", tone: "risk" },
  DTD: { word: "Day-to-day", tone: "risk" },
  P: { word: "Probable", tone: "muted" },
  "(active)": { word: "Available", tone: "ok" },
};

export const STATUS_TAG_CSS = `
  .player-name .injury { color: var(--ffx-orange-text); }
  .injury.ffx-native-status--refined { display: none; }
  .ffx-status {
    margin-left: 4px;
    font-size: 11px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .ffx-status--risk { color: var(--ffx-orange-text); }
  .ffx-status--muted { color: var(--ffx-muted); }
  .ffx-status--ok { color: var(--ffx-ink); }
  .ffx-status__age { color: var(--ffx-muted); font-weight: 400; }
`;

export function refinePlayerStatus(player: Player) {
  const { refinedPlayerStatus: { injuryStatus: status, timeAgo } = {} } = player;
  const nameLink = player.row.querySelector(".player-text");
  player.row.querySelector(".ffx-status")?.remove();
  if (!nameLink || !status) return;

  // Hidden, not rewritten: setting the lineup re-reads this tag's text as the player's status
  player.row.querySelector(PLAYER_STATUS_SELECTOR)?.classList.add("ffx-native-status--refined");

  const { word, tone } = STATUS_WORDS[status];
  const tag = document.createElement("span");
  tag.className = `ffx-status ffx-status--${tone}`;
  tag.textContent = word;
  if (timeAgo) {
    const age = document.createElement("span");
    age.className = "ffx-status__age";
    age.textContent = `${timeAgo.value}${timeAgo.unit.charAt(0)}`;
    tag.insertAdjacentText("beforeend", " ");
    tag.appendChild(age);
  }
  nameLink.insertAdjacentElement("afterend", tag);
}
