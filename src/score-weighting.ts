import { PLAYER_DATA } from "./data";
import type { Player } from "./page";
export const getPlayerWeightedScore = (player: Player) => {
  const playerData = PLAYER_DATA[player.playerName as keyof typeof PLAYER_DATA];
  const projectedSeasonAvg = playerData?.projectedSeasonAvg;
  const { last5Avg, seasonAvg, gamesPlayed } = player;

  // Weight recent performance more heavily as season progresses
  const seasonProgressWeight = Math.min(gamesPlayed / 20, 1); // Caps at 20 games

  // Recent form matters more than season average
  const actualPerformanceWeight = 0.7 * last5Avg + 0.3 * seasonAvg;

  // Early season: rely more on projections
  // Late season: rely more on actual performance
  return (
    seasonProgressWeight * actualPerformanceWeight +
    (1 - seasonProgressWeight) * (projectedSeasonAvg ?? actualPerformanceWeight)
  );
};
