export type PlayerStatus = "(active)" | "DTD" | "P" | "Q" | "D" | "OUT" | "OFS";

export type PlayerOpponentInfo = {
  avgPointsAllowed: number;
  avgPointsAllowedRank: number;
  position?: string;
  defenseRank?: number;
};

export type TimeAgo = {
  value: number;
  unit: "days" | "hours" | "minutes";
};

export interface Player {
  playerName: string;
  playerStatus: PlayerStatus;
  refinedPlayerStatus:
    | { injuryStatus: PlayerStatus; timeAgo: TimeAgo | undefined }
    | undefined;
  last5Avg: number | null;
  last10Avg: number | null;
  seasonAvg: number | null;
  seasonTotal: number | null;
  gamesPlayed: number | null;
  todaysGame: string | null | undefined;
  position: string | null | undefined;
  setPositionDropdown: HTMLSelectElement | null;
  isTaxi: boolean;
  isIr: boolean;
  opponentInfo: PlayerOpponentInfo | undefined;
  row: HTMLTableRowElement;
}

