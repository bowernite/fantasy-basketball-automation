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
      const aIsDtd = a.playerStatus === "DTD";
      const bIsDtd = b.playerStatus === "DTD";
      const aIsOut = a.playerStatus === "OUT";
      const bIsOut = b.playerStatus === "OUT";
      const aIsInjured = aIsDtd || aIsOut;
      const bIsInjured = bIsDtd || bIsOut;


      if (aHasGame && !bHasGame) return -1;
      if (!aHasGame && bHasGame) return 1;

      if (
        a.playerName === "Khris Middleton" ||
        b.playerName === "Khris Middleton"
      ) {
        console.log(
          "Player A Name:",
          a.playerName,
          "A Injured:",
          aIsInjured,
          "A DTD:",
          aIsDtd,
          "A Out:",
          aIsOut,
          "Player B Name:",
          b.playerName,
          "B Injured:",
          bIsInjured,
          "B DTD:",
          bIsDtd,
          "B Out:",
          bIsOut
        );
      }
      if (!aIsInjured && bIsInjured) return -1;
      if (!bIsInjured && aIsInjured) return 1;

      if (aIsDtd && bIsOut) return -1;
      if (aIsOut && bIsDtd) return 1;

      return bScore - aScore;
    });
}
