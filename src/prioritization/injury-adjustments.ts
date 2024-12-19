import { getNumDaysInFuture } from "../dates";
import type { Player } from "../page/get-players";

export function adjustPredictedScoreForInjury(score: number, player: Player) {
  const { playerStatus, refinedPlayerStatus } = player;
  const status = refinedPlayerStatus?.injuryStatus ?? playerStatus;
  const timeAgo = refinedPlayerStatus?.timeAgo;
  const numberOfDaysInFuture = getNumDaysInFuture();
  console.log("🟣 number of days in future:", numberOfDaysInFuture);

  if (status === "P") {
    if (numberOfDaysInFuture === 0) score *= 0.85;
    if (numberOfDaysInFuture === 1) score *= 0.95;
  } else if (status === "DTD" || status === "Q") {
    if (numberOfDaysInFuture === 0) score *= 0.65;
    if (numberOfDaysInFuture === 1) score *= 0.65;
  } else if (status === "D") {
    if (numberOfDaysInFuture === 0) score *= 0.1;
    if (numberOfDaysInFuture === 1) score *= 0.2;
  } else if (status === "OUT") {
    if (numberOfDaysInFuture === 0) score = 0;
    if (numberOfDaysInFuture === 1) score *= 0.1;
  } else if (status === "OFS") {
    score = 0;
  }

  return [
    score,
    { playerStatus, refinedPlayerStatus, status, timeAgo },
  ] as const;
}
