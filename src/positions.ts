import type { Player } from "./page-querying";

type StrictPosition = "PG" | "SG" | "SF" | "PF" | "C";
type WidePosition = StrictPosition | string;
type PositionSlot = StrictPosition | "G" | "F" | "UTIL";
