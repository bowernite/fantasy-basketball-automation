import { parsePlayerNews } from "../page/player-status";
import { resolveInjuryStatus } from "../prioritization/injury-adjustments";
import type { PlayerStatus } from "../types";
import { fetchWithTimeout } from "./fetch-with-timeout";

const ESPN_INJURIES_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries";
// ESPN's CDN answers 403 to browser and custom User-Agents but lets curl's through
const ESPN_USER_AGENT = "curl/8.7.1";
const URGENT_TIP_WINDOW_MS = 3 * 60 * 60 * 1000;
const OUT_STATUSES: PlayerStatus[] = ["OUT", "OFS"];

export type EspnInjury = { status: string; date: string; shortComment?: string; athlete: { displayName: string }; details?: { returnDate?: string } };
/** Signed-in `FetchRoster` response for one day (only the fields read here) */
export type InjuryRoster = { groups: { slots: { leaguePlayer?: RosterPlayer }[] }[] };
type RosterPlayer = {
  proPlayer: { nameFull: string; injury?: { typeAbbreviaition: PlayerStatus }; news?: { timeEpochMilli: string; contents: string }[] };
  requestedGames?: { game: { startTimeEpochMilli: string } }[];
};
/** Both feeds' view of a rostered player with a game that day, when either has him injured */
export type InjuryComparison = { player: string; ffStatus: PlayerStatus; ffNewsAt?: string; espnStatus?: string; espnDate?: string; espnReturnDate?: string; espnComment?: string };
export type InjuryDisagreement = { message: string; urgent: boolean };

export async function fetchEspnInjuries(): Promise<{ injuries: EspnInjury[] } | { error: string }> {
  try {
    const response = await fetchWithTimeout(ESPN_INJURIES_URL, { headers: { "User-Agent": ESPN_USER_AGENT } });
    if (!response.ok) return { error: `ESPN injuries unavailable (HTTP ${response.status})` };
    const { injuries } = await response.json<{ injuries: { injuries: EspnInjury[] }[] }>();
    return { injuries: injuries.flatMap((team) => team.injuries) };
  } catch (error) {
    return { error: `ESPN injuries unavailable (${error})` };
  }
}

/** Compares Fleaflicker's injury status (tag, refined by news the way scoring does) with ESPN's for players with a game that day */
export function compareInjuryFeeds(roster: InjuryRoster, espnInjuries: EspnInjury[], starters: Set<string>) {
  const espnByName = Map.groupBy(espnInjuries, (injury) => normalizeName(injury.athlete.displayName));
  const players = roster.groups.flatMap(({ slots }) => slots.flatMap(({ leaguePlayer }) => (leaguePlayer?.requestedGames?.length ? [leaguePlayer] : [])));
  const comparisons: InjuryComparison[] = [];
  const disagreements: InjuryDisagreement[] = [];
  for (const { proPlayer, requestedGames = [] } of players) {
    const player = proPlayer.nameFull;
    const espnMatches = espnByName.get(normalizeName(player)) ?? [];
    if (espnMatches.length > 1) continue;
    const [espn] = espnMatches;
    const { ffStatus, ffNewsAt } = readFleaflickerStatus(proPlayer);
    if (ffStatus === "(active)" && !espn) continue;
    comparisons.push({ player, ffStatus, ffNewsAt, espnStatus: espn?.status, espnDate: espn?.date, espnReturnDate: espn?.details?.returnDate, espnComment: espn?.shortComment });

    const espnOut = espn?.status === "Out";
    if (OUT_STATUSES.includes(ffStatus) && !espnOut) {
      const espnView = espn ? `${espn.status}${espn.details?.returnDate ? ` (return ${espn.details.returnDate})` : ""}` : "not on its injury list";
      disagreements.push({ message: `Fleaflicker has ${player} ${ffStatus}, ESPN ${espnView}: he may be benched wrongly`, urgent: false });
    }
    const espnNewer = espnOut && (!ffNewsAt || Date.parse(espn.date) > Date.parse(ffNewsAt));
    if (espnNewer && !OUT_STATUSES.includes(ffStatus) && ffStatus !== "D") {
      const tipSoon = requestedGames.some(({ game }) => {
        const untilTipMs = Number(game.startTimeEpochMilli) - Date.now();
        return untilTipMs >= 0 && untilTipMs <= URGENT_TIP_WINDOW_MS;
      });
      const comment = espn.shortComment ? `: "${espn.shortComment}"` : "";
      const ffView = ffStatus === "(active)" ? "healthy" : ffStatus;
      disagreements.push({ message: `ESPN has ${player} Out as of ${espn.date}${comment}, Fleaflicker ${ffView}: he may start while out`, urgent: tipSoon && starters.has(player) });
    }
  }
  return { comparisons, disagreements };
}

// Mirrors how the page's status is read for scoring: news only refines an injury tag
function readFleaflickerStatus({ injury, news = [] }: RosterPlayer["proPlayer"]) {
  const playerStatus = injury?.typeAbbreviaition ?? "(active)";
  const latestNews = news.toSorted((a, b) => Number(b.timeEpochMilli) - Number(a.timeEpochMilli))[0];
  const ffNewsAt = latestNews && new Date(Number(latestNews.timeEpochMilli)).toISOString();
  const parsedNews = latestNews && playerStatus !== "(active)" ? parsePlayerNews(latestNews.contents, undefined) : undefined;
  const refinedPlayerStatus = parsedNews && { ...parsedNews, timeAgo: { value: (Date.now() - Number(latestNews.timeEpochMilli)) / 60000, unit: "minutes" as const } };
  return { ffStatus: resolveInjuryStatus({ playerStatus, refinedPlayerStatus }).status, ffNewsAt };
}

function normalizeName(name: string) {
  return name
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[.']/g, "")
    .replace(/\s+(jr|sr|ii|iii|iv)$/, "")
    .trim();
}
