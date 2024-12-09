import { PLAYER_DATA, type PlayerData } from "./data/player-data";
import type { Player } from "./page/get-players";

export function getPlayerPredictedScore(player: Player) {
  const [weightedScore, debugInfo] = getPlayerWeightedScore(player);
  if (isNaN(weightedScore)) {
    console.error(`NaN weighted score for ${player.playerName}`);
  }
  const [adjustedForOpponent, opponentAdjustmentDebugInfo] =
    adjustPredictedScoreBasedOnOpponent(weightedScore, player.opponentInfo);
  return [
    adjustedForOpponent,
    {
      ...debugInfo,
      beforeOpponentAdjustment: weightedScore,
      ...opponentAdjustmentDebugInfo,
    },
  ] as const;
}

function getPlayerWeightedScore(player: Player) {
  // @ts-ignore
  const playerData = PLAYER_DATA[player.playerName] as PlayerData | undefined;
  const { last5Avg, last10Avg, seasonAvg, gamesPlayed } = player;

  // Weight recent performance more heavily as season progresses
  const seasonProjectionAvg = playerData?.projectedSeasonAvg;
  const seasonProjectionWeight = seasonProjectionAvg
    ? Math.max(Math.min((12 - gamesPlayed) / 12, 1), 0)
    : 0;

  const actualPerformance = getActualPerformance({
    last5Avg,
    last10Avg,
    seasonAvg,
  });
  const actualPerformanceWeight = 1 - seasonProjectionWeight;

  // Early season: rely more on projections
  // Late season: rely more on actual performance
  const weightedScore =
    seasonProjectionWeight * (seasonProjectionAvg ?? 0) +
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

  return [
    weightedScore,
    {
      gamesPlayed,
      seasonProjectionWeight,
      seasonProjectionAvg,
      actualPerformanceWeight,
      actualPerformance,
      last5Avg,
      last10Avg,
      seasonAvg,
    },
  ] as const;
}

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

/**
 * Adjust the predicted score based on the opponent's defense.
 */
function adjustPredictedScoreBasedOnOpponent(
  initialScore: number,
  opponentInfo: Player["opponentInfo"]
) {
  if (!opponentInfo) {
    return [initialScore, {}] as const;
  }

  const WORST_DEFENSE_RANK = 30;
  const BEST_DEFENSE_RANK = 1;
  const MIDDLE_RANK = (WORST_DEFENSE_RANK + BEST_DEFENSE_RANK) / 2;
  const MAX_RANK_ADJUSTMENT = 0.15; // 15% boost/reduction based on opponent defense

  // Center around middle rank (15.5) instead of best rank (1)
  const defenseRankDifference = opponentInfo.defenseRank - MIDDLE_RANK;
  const maxRankDifference = (WORST_DEFENSE_RANK - BEST_DEFENSE_RANK) / 2;
  const rankAdjustmentFactor = defenseRankDifference / maxRankDifference;

  const scoreMultiplier = 1 + rankAdjustmentFactor * MAX_RANK_ADJUSTMENT;

  return [
    initialScore * scoreMultiplier,
    {
      scoreMultiplier,
      rankAdjustmentFactor,
      defenseRankDifference,
      maxRankDifference,
    },
  ] as const;
}
