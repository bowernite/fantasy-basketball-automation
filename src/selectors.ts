// NOTES
// - Assumes we're on `fantasy stats` page

let tables = document.querySelectorAll("table");
if (tables.length !== 1) {
  throw new Error("Expected exactly one table");
}
let table = tables[0];

let rows = table.querySelectorAll("tr");
if (rows.length === 0) {
  throw new Error("Expected at least one row");
}

export const playerData = Array.from(rows)
  .map((row) => {
    const playerName = row.querySelector(".player-text")?.textContent;
    if (!playerName) {
      console.warn("Empty row found; skipping");
      return;
    }
    console.log("🟣 :", playerName);

    const playerStatus = row.querySelector(".injury")?.textContent || "active";
    console.log("🟣 :", playerStatus);

    const fantasyPointsElements = row.querySelectorAll(".fp");
    console.log("🟣 :", fantasyPointsElements);
    const last5Avg = Number(fantasyPointsElements[1]?.textContent ?? 0);
    console.log("🟣 :", last5Avg);
    const seasonAvg = Number(fantasyPointsElements[2]?.textContent ?? 0);
    console.log("🟣 :", seasonAvg);
    const seasonTotal = Number(fantasyPointsElements[3]?.textContent ?? 0);
    console.log("🟣 :", seasonTotal);
    const gamesPlayed = seasonTotal / seasonAvg;
    console.log("🟣 :", gamesPlayed);

    const todaysGame = row.querySelector(".pro-opp-matchup")?.textContent;
    console.log("🟣 :", todaysGame);

    const position = row.querySelector(".position")?.textContent;
    console.log("🟣 :", position);

    return {
      playerName,
      playerStatus,
      last5Avg,
      seasonAvg,
      seasonTotal,
      gamesPlayed,
      todaysGame,
      position,
    };
  })
  .filter((player) => player !== undefined);

export type Player = (typeof playerData)[number];
