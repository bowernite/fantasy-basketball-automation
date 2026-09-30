import { expect, test } from "bun:test";
import { parseOpponentInfo } from "./opponent-info";

// Inputs mirror the opponent tooltip text as read from the page's tooltip data (tags stripped).
// Rank 1st = fewest fantasy points allowed to that position, i.e. the toughest matchup.

test("reads the fantasy points the opponent allows and its rank", () => {
  const tooltip =
    "Vs opposing Cs per game:Pts: 20.96 (5th)Reb: 13.09 (5th)Ast: 3.87 (12th)Default FPts: 35.76 (2nd)";

  expect(parseOpponentInfo(tooltip, "Neemias Queta")).toMatchObject({
    avgPointsAllowed: 35.76,
    defenseRank: 2,
  });
});

test("reads a tied rank", () => {
  const tooltip =
    "Vs opposing Cs per game:Pts: 24.67 (6th)Reb: 20.67 (t-15th)Ast: 7 (19th)Default FPts: 43.78 (t-12th)";

  expect(parseOpponentInfo(tooltip, "Neemias Queta")).toMatchObject({
    avgPointsAllowed: 43.78,
    defenseRank: 12,
  });
});
