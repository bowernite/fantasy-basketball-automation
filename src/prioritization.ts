import { getNumDaysInFuture } from "./dates";
import type { Player } from "./page/page-querying";
import { getPlayerPredictedScore } from "./score-weighting";

export function prioritizePlayers(players: Player[]) {
  const numberOfDaysInFuture = getNumDaysInFuture();

  const playersWithScores = players
    .filter(
      (player) =>
        player.playerStatus === "(active)" ||
        player.playerStatus === "DTD" ||
        player.playerStatus === "OUT"
    )
    .filter((player) => player.setPositionDropdown)
    .map((player) => {
      const [score, debugInfo] = getPlayerPredictedScore(player);
      return {
        player,
        score,
        debugInfo,
      };
    });

  const prioritizedPlayers = playersWithScores.sort((a, b) => {
    const aHasGame = Boolean(a.player.opponentInfo);
    const bHasGame = Boolean(b.player.opponentInfo);
    const aIsDtd = numberOfDaysInFuture >= 2 ? false : a.player.playerStatus === "DTD";
    const bIsDtd = numberOfDaysInFuture >= 2 ? false : b.player.playerStatus === "DTD";
    const aIsOut = a.player.playerStatus === "OUT";
    const bIsOut = b.player.playerStatus === "OUT";
    const aIsInjured = aIsDtd || aIsOut;
    const bIsInjured = bIsDtd || bIsOut;

    if (aHasGame && !bHasGame) return -1;
    if (!aHasGame && bHasGame) return 1;

    if (!aIsInjured && bIsInjured) return -1;
    if (!bIsInjured && aIsInjured) return 1;

    if (aIsDtd && bIsOut) return -1;
    if (aIsOut && bIsDtd) return 1;

    return b.score - a.score;
  });

  console.log("🟣 Prioritized players debug info:");
  console.table(
    prioritizedPlayers.map(({ player, score, debugInfo }) => ({
      name: player.playerName,
      // status: player.playerStatus,
      predictedScore: score,
      ...debugInfo,
      // hasGame: Boolean(player.opponentInfo),
    }))
  );

  return prioritizedPlayers;
}
