import { parseHTML } from "linkedom";

export type GameTip = { at: string; players: string[] };
export type TipTable = { day: number; fetchedAt: string; tips: GameTip[] };
export type LedgerEntry = { startedAt: string; ok: boolean; days: number[] };
export type DayTip = GameTip & { day: number };
export type TickPlan = { runDays: number[]; tipTableStale: boolean; missedTips: DayTip[]; nextTarget: Date };

const MINUTE_MS = 60 * 1000;
const TIP_TARGET_LEADS_MS = [40 * MINUTE_MS, 15 * MINUTE_MS];
// Setting a lineup while a player locks mid-request has unknown server behavior
const TIP_CUTOFF_MS = 3 * MINUTE_MS;
const HOUR_MS = 60 * MINUTE_MS;
const MISSED_WINDOW_MS = 45 * MINUTE_MS;
const TIP_TABLE_MAX_AGE_MS = 2 * HOUR_MS;
// League time (America/Chicago) is a whole-hour UTC offset in both CST and CDT, so :05 UTC is :05 local
const HOURLY_OFFSET_MS = 5 * MINUTE_MS;

/**
 * What a tick should do, given Fleaflicker day `day` for `now`, stored tip tables and past runs
 * - `runDays`: days one run should set now (empty = nothing due)
 * - `missedTips`: passed tips with no successful run in the 45 min before them; reported on every tick after the tip, so dedupe by `at`
 * - `nextTarget`: earliest target after `now`
 */
export function planTick(now: Date, day: number, tipTables: TipTable[], ledger: LedgerEntry[]): TickPlan {
  const nowMs = now.getTime();
  const runDays = new Set<number>();
  const todaysTipTable = tipTables.find((table) => table.day === day);
  const tipTableStale = !todaysTipTable || nowMs - Date.parse(todaysTipTable.fetchedAt) > TIP_TABLE_MAX_AGE_MS;
  if (tipTableStale) runDays.add(day);
  const hourlyDays = [day, day + 1];
  if (!hasSuccessBetween(ledger, latestHourlyTargetMs(nowMs), Infinity, hourlyDays)) hourlyDays.forEach((hourlyDay) => runDays.add(hourlyDay));
  const tips = tipTables.filter((table) => table.day >= day).flatMap((table) => table.tips.map((tip) => ({ ...tip, day: table.day })));
  for (const tip of tips) {
    const tipMs = Date.parse(tip.at);
    if (nowMs >= tipMs - TIP_CUTOFF_MS) continue;
    const due = TIP_TARGET_LEADS_MS.some((lead) => {
      const targetMs = tipMs - lead;
      return nowMs >= targetMs && !hasSuccessBetween(ledger, targetMs, Infinity, [tip.day]);
    });
    if (due) runDays.add(tip.day);
  }
  const missedTips = tips.filter((tip) => {
    const tipMs = Date.parse(tip.at);
    return nowMs >= tipMs && !hasSuccessBetween(ledger, tipMs - MISSED_WINDOW_MS, tipMs, [tip.day]);
  });
  const futureTipTargetsMs = tips.flatMap((tip) => TIP_TARGET_LEADS_MS.map((lead) => Date.parse(tip.at) - lead)).filter((targetMs) => targetMs > nowMs);
  const nextTarget = new Date(Math.min(latestHourlyTargetMs(nowMs) + HOUR_MS, ...futureTipTargetsMs));
  return { runDays: [...runDays].sort((a, b) => a - b), tipTableStale, missedTips, nextTarget };
}

/** Distinct tip times (UTC ISO) of the rostered players' games on a team page, earliest first */
export function parseGameTips(html: string): GameTip[] {
  const { document } = parseHTML(html);
  const playersByTip = new Map<string, string[]>();
  for (const tipTime of Array.from(document.querySelectorAll("tr local-time[datetime]"))) {
    const at = new Date(tipTime.getAttribute("datetime")!).toISOString();
    const player = tipTime.closest("tr")!.querySelector(".player-text")?.textContent ?? "";
    playersByTip.set(at, [...(playersByTip.get(at) ?? []), player]);
  }
  return [...playersByTip].map(([at, players]) => ({ at, players })).sort((a, b) => a.at.localeCompare(b.at));
}

function latestHourlyTargetMs(nowMs: number) {
  return Math.floor((nowMs - HOURLY_OFFSET_MS) / HOUR_MS) * HOUR_MS + HOURLY_OFFSET_MS;
}

function hasSuccessBetween(ledger: LedgerEntry[], fromMs: number, toMs: number, days: number[]) {
  return ledger.some((entry) => {
    const startedMs = Date.parse(entry.startedAt);
    return entry.ok && startedMs >= fromMs && startedMs < toMs && days.every((day) => entry.days.includes(day));
  });
}
