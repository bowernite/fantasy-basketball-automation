import type { Player } from "./page-querying";
import { getPlayerPredictedScore } from "./score-weighting";

export function prioritizePlayers(players: Player[]): Player[] {
  return players
    .filter(
      (player) =>
        player.playerStatus === "(active)" ||
        player.playerStatus === "DTD" ||
        player.playerStatus === "OUT"
    )
    .filter((player) => player.setPositionDropdown)
    .sort((a, b) => {
      // First prioritize players who have a game today
      if (a.todaysGame !== b.todaysGame) {
        return a.todaysGame ? -1 : 1;
      }

      // Then prioritize non-injured players
      const aIsInjured = a.playerStatus === "DTD" || a.playerStatus === "OUT";
      const bIsInjured = b.playerStatus === "DTD" || b.playerStatus === "OUT";
      if (aIsInjured !== bIsInjured) {
        return aIsInjured ? 1 : -1;
      }

      // Within injury status, sort OUT players after DTD players
      if (aIsInjured && bIsInjured) {
        const aIsOut = a.playerStatus === "OUT";
        const bIsOut = b.playerStatus === "OUT";
        if (aIsOut !== bIsOut) {
          return aIsOut ? 1 : -1;
        }
      }

      // Finally sort by predicted score
      return getPlayerPredictedScore(b) - getPlayerPredictedScore(a);
    });
}
