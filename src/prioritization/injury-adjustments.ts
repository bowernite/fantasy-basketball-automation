import { getNumDaysInFuture } from "../dates";
import type { Player, TimeAgo } from "../page/get-players";

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
    if (daysBetweenReportAndGame <= 0) multiplier = 0.85;
    if (daysBetweenReportAndGame <= 1) multiplier = 0.95;
  } else if (status === "DTD" || status === "Q") {
    if (daysBetweenReportAndGame <= 0) multiplier = 0.65;
    else if (daysBetweenReportAndGame <= 1) multiplier = 0.65;
  } else if (status === "D") {
    if (daysBetweenReportAndGame <= 0) multiplier = 0.1;
    else if (daysBetweenReportAndGame <= 1) multiplier = 0.2;
  } else if (status === "OUT") {
    if (daysBetweenReportAndGame <= 1) multiplier = 0;
    else if (daysBetweenReportAndGame <= 2) multiplier = 0.1;
  } else if (status === "OFS") {
    multiplier = 0;
  }

  return [
    score * multiplier,
    {
      playerStatus,
      refinedPlayerStatus,
      status,
      timeAgo,
      daysBetweenReportAndGame,
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

