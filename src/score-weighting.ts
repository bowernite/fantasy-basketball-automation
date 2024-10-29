import { PLAYER_DATA } from "./data";
import type { Player } from "./page";

export const getPlayerWeightedScore = (player: Player) => {
  const playerData = PLAYER_DATA[player.playerName as keyof typeof PLAYER_DATA];
  const { last5Avg, seasonAvg, gamesPlayed } = player;

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
  console.log(`weightedScore data for ${player.playerName}:`, {
    seasonProjectionWeight,
    seasonProjectionAvg,
    actualPerformanceWeight,
    actualPerformance,
    last5Avg,
    seasonAvg,
    weightedScore,
  });

  return weightedScore;
};
