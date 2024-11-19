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
      const aScore = getPlayerPredictedScore(a);
      const bScore = getPlayerPredictedScore(b);

      const aHasGame = Boolean(a.opponentInfo);
      const bHasGame = Boolean(b.opponentInfo);

      const aIsInjured = a.playerStatus === "DTD" || a.playerStatus === "OUT";
      const bIsInjured = b.playerStatus === "DTD" || b.playerStatus === "OUT";

      // First priority: Has game and not injured
      if (aHasGame && !aIsInjured && (!bHasGame || bIsInjured)) return -1;
      if (bHasGame && !bIsInjured && (!aHasGame || aIsInjured)) return 1;

      // Second priority: Has game and injured
      if (aHasGame && aIsInjured && !bHasGame) return -1;
      if (bHasGame && bIsInjured && !aHasGame) return 1;

      // Within same priority group, sort by predicted score
      return bScore - aScore;
    });
}
