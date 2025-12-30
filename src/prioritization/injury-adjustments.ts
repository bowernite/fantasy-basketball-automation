import { getNumDaysInFuture } from "../utils/date-utils";
import type { Player, TimeAgo } from "../types";

export function adjustPredictedScoreForInjury(score: number, player: Player) {
  const { playerStatus, refinedPlayerStatus } = player;
  const status = refinedPlayerStatus?.injuryStatus ?? playerStatus;
  const timeAgo = refinedPlayerStatus?.timeAgo;
  const numberOfDaysInFuture = getNumDaysInFuture();

  const timeAgoInDays = timeAgo ? getTimeAgoInDays(timeAgo) : null;
  let daysBetweenReportAndGame =
    timeAgoInDays != null
      ? timeAgoInDays + numberOfDaysInFuture
      : numberOfDaysInFuture;

  let multiplier = 1;
  if (status === "P") {
    // Probable: Very likely to play (>90%).
    // High confidence if reported within the last ~36 hours.
    if (daysBetweenReportAndGame <= 1.5) multiplier = 0.95;
  } else if (status === "DTD" || status === "Q") {
    // Questionable: Typically 50/50.
    // We use 0.5 to reflect the coin-flip nature.
    if (daysBetweenReportAndGame <= 1.5) multiplier = 0.5;
  } else if (status === "D") {
    // Doubtful: Very unlikely (~25% or less).
    // If fresh (< 17 hours), almost certainly out.
    if (daysBetweenReportAndGame <= 0.7) multiplier = 0.05;
    else if (daysBetweenReportAndGame <= 1.5) multiplier = 0.2;
    else if (daysBetweenReportAndGame <= 2.5) multiplier = 0.4;
    else if (daysBetweenReportAndGame <= 3.5) multiplier = 0.6;
  } else if (status === "OUT") {
    // OUT: Confirmed out.
    // If report is fresh (< 17 hours), it's definitely for this game -> 0.
    if (daysBetweenReportAndGame <= 0.7) multiplier = 0;
    // If report is ~1 day old (e.g. 22 hours), it might be from the *previous* game.
    // We treat this as high risk (likely still injured), but give it a chance (0.25)
    // so we don't completely zero out a player who might just be DTD.
    else if (daysBetweenReportAndGame <= 1.5) multiplier = 0.25;
    else if (daysBetweenReportAndGame <= 2.5) multiplier = 0.4;
    else if (daysBetweenReportAndGame <= 3.5) multiplier = 0.6;
  } else if (status === "OFS") {
    multiplier = 0;
  }

  return [
    score * multiplier,
    {
      injuryStatus: status,
      reportDaysAgo: timeAgoInDays?.toFixed(2) ?? null,
      daysBetweenReportAndGame: daysBetweenReportAndGame.toFixed(2),
      injuryMultiplier: multiplier,
    },
  ] as const;
}

function getTimeAgoInDays(timeAgo: TimeAgo) {
  if (timeAgo.unit === "minutes") {
    return timeAgo.value / 60 / 24;
  }
  if (timeAgo.unit === "hours") {
    return timeAgo.value / 24;
  }
  return timeAgo.value;
}

