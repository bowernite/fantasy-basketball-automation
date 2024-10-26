import type { Player } from "./selectors";

type StrictPosition = "PG" | "SG" | "SF" | "PF" | "C";
type WidePosition = StrictPosition | string;
type PositionSlot = StrictPosition | "G" | "F" | "UTIL";

export const getEligiblePositions = (playerData: Player) => {
  const { position } = playerData;
};
