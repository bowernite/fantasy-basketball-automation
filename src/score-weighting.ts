import { PLAYER_DATA } from "./data";
import type { Player } from "./page-querying";

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

const getPlayerWeightedScore = (player: Player) => {
  const playerData = PLAYER_DATA[player.playerName as keyof typeof PLAYER_DATA];
  const { last5Avg, last10Avg, seasonAvg, gamesPlayed, opponentInfo } = player;

  // Weight recent performance more heavily as season progresses
  const seasonProjectionAvg = playerData?.projectedSeasonAvg;
  const seasonProjectionWeight = Math.max(
    Math.min((12 - gamesPlayed) / 12, 1),
    0
  );

  const actualPerformance = getActualPerformance({
    last5Avg,
    last10Avg,
    seasonAvg,
  });
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

/**
 * Calculate a score of how well the player's been doing this season, taking into account season average, last 5 games, and last 10 games.
 */
function getActualPerformance({
  last5Avg,
  last10Avg,
  seasonAvg,
}: {
  last5Avg?: number;
  last10Avg?: number;
  seasonAvg: number;
}) {
  // Recent form matters more than season average
  const SEASON_WEIGHT = 0.2;
  const LAST_10_WEIGHT = 0.45;
  const LAST_5_WEIGHT = 0.35;

  let totalWeight = SEASON_WEIGHT;
  let weightedSum = SEASON_WEIGHT * seasonAvg;

  if (last10Avg) {
    totalWeight += LAST_10_WEIGHT;
    weightedSum += LAST_10_WEIGHT * last10Avg;
  }

  if (last5Avg) {
    totalWeight += LAST_5_WEIGHT;
    weightedSum += LAST_5_WEIGHT * last5Avg;
  }

  return weightedSum / totalWeight;
}
