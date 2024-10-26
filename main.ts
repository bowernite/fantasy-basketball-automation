import { playerData } from "./src/selectors";



const playersToStart = playerData
  // TODO: Handle probable, questionable, etc.
  .filter((player) => player.playerStatus === "active")
  .filter((player) => player.todaysGame)
  .sort((a, b) => b.seasonAvg - a.seasonAvg)
  .slice(0, 9);

console.table(playersToStart);
