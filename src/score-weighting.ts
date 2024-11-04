import { PLAYER_DATA } from "./data";
import type { Player } from "./page-querying";

export const getPlayerWeightedScore = (player: Player) => {
  const playerData = PLAYER_DATA[player.playerName as keyof typeof PLAYER_DATA];
  const { last5Avg, seasonAvg, gamesPlayed, opponentInfo } = player;

  // Weight recent performance more heavily as season progresses
  const seasonProjectionAvg = playerData?.projectedSeasonAvg;
  const seasonProjectionWeight = Math.max(
    Math.min((12 - gamesPlayed) / 12, 1),
    0
  );

  // Recent form matters more than season average
  const actualPerformance = 0.7 * last5Avg + 0.3 * seasonAvg;
  const actualPerformanceWeight = 1 - seasonProjectionWeight;

  // Early season: rely more on projections
  // Late season: rely more on actual performance
  const weightedScore =
    seasonProjectionWeight * seasonProjectionAvg +
    actualPerformanceWeight * actualPerformance;
  // console.log(`weightedScore data for ${player.playerName}:`, {
  //   seasonProjectionWeight,
  //   seasonProjectionAvg,
  //   actualPerformanceWeight,
  //   actualPerformance,
  //   last5Avg,
  //   seasonAvg,
  //   weightedScore,
  // });

  return weightedScore;
};

export const getPlayerPredictedScore = (player: Player) => {
  const weightedScore = getPlayerWeightedScore(player);
  const { opponentInfo } = player;
  if (!opponentInfo) {
    return weightedScore;
  }

  const mpg = predictPlayerMinutesPerGame({
    position: opponentInfo?.position,
    avgScore: weightedScore,
  });
  const portionOfGamePlayed = mpg / 36;
  const avgOppPointsAllowed =
    (opponentInfo?.avgPointsAllowed ?? 0) * portionOfGamePlayed;

  return weightedScore;
};

function predictPlayerMinutesPerGame({
  position,
  avgScore,
}: {
  position?: string;
  avgScore: number;
}) {
  // TODO: Make this better?
  const basedOnScore = Math.min(avgScore * 1.25, 36);

  // TODO: Lessen for centers?

  return basedOnScore;
}
