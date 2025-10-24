import type { Player } from "../page/get-players";
import { getPlayerPredictedScore } from "./score-weighting";

export function prioritizePlayers(players: Player[]) {
  const playersWithScores = players.map((player) => {
    const [score, debugInfo] = getPlayerPredictedScore(player);
    return {
      player,
      score,
      debugInfo,
    };
  });

  const prioritizedPlayers = playersWithScores.sort((a, b) => {
    const aHasGame = Boolean(a.player.todaysGame);
    const bHasGame = Boolean(b.player.todaysGame);

    if (aHasGame && !bHasGame) return -1;
    if (!aHasGame && bHasGame) return 1;

    return b.score - a.score;
  });

  console.log("🟣 Prioritized players debug info:");
  console.table(
    prioritizedPlayers.map(({ player, score, debugInfo }) => ({
      name: player.playerName,
      predictedScore: score,
      todaysGame: player.todaysGame,
      ...debugInfo,
      // hasGame: Boolean(player.opponentInfo),
    }))
  );

  return prioritizedPlayers;
}

/********************************************************************
 * Archive
 *******************************************************************/
// const aIsDtd =
//   numberOfDaysInFuture >= 2
//     ? false
//     : // Quick hack: ignoring probable. Next step is probably a more thought out approach, where we take into account `time ago`, days in future, etc., and maybe use those as multipliers for the predicted score, instead of the fancy sorting logic below
//       ["DTD", "Q", "D"].includes(
//         a.player.refinedPlayerStatus?.injuryStatus ?? ""
//       );
// const bIsDtd =
//   numberOfDaysInFuture >= 2
//     ? false
//     : ["DTD", "Q", "D"].includes(
//         b.player.refinedPlayerStatus?.injuryStatus ?? ""
//       );
// const aIsOut = a.player.playerStatus === "OUT";
// const bIsOut = b.player.playerStatus === "OUT";
// const aIsInjured = aIsDtd || aIsOut;
// const bIsInjured = bIsDtd || bIsOut;

// if (aHasGame && !bHasGame) return -1;
// if (!aHasGame && bHasGame) return 1;

// if (!aIsInjured && bIsInjured) return -1;
// if (!bIsInjured && aIsInjured) return 1;

// if (aIsDtd && bIsOut) return -1;
// if (aIsOut && bIsDtd) return 1;
