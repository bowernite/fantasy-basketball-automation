import type { LineupDecision } from "./decide-lineup";

const FLEAFLICKER_ORIGIN = "https://www.fleaflicker.com";

export type SaveResult = { posted: boolean; problems: string[] };

export async function saveLineup(decision: Extract<LineupDecision, { ok: true }>, sessionHeaders: Record<string, string>): Promise<SaveResult> {
  if (decision.changes.length === 0) return { posted: false, problems: [] };
  const lineupUrl = `${FLEAFLICKER_ORIGIN}${decision.formAction}`;
  await fetch(lineupUrl, {
    method: "POST",
    headers: { ...sessionHeaders, "Content-Type": "application/x-www-form-urlencoded", Origin: FLEAFLICKER_ORIGIN, Referer: lineupUrl },
    body: decision.body,
    redirect: "manual",
  });
  return { posted: true, problems: [] };
}
