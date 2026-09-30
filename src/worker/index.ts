import { DurableObject } from "cloudflare:workers";
import { type ApiRoster, decideLineup, type LineupDecision } from "./decide-lineup";
import { fetchWithTimeout } from "./fetch-with-timeout";
import { type DayTip, type LedgerEntry, parseGameTips, planTick, type TipTable } from "./lineup-schedule";

const FLEAFLICKER_LOGIN_URL = "https://www.fleaflicker.com/nba/login";
const PUSHOVER_URL = "https://api.pushover.net/1/messages.json";
const TRELLO_CARDS_URL = "https://api.trello.com/1/cards";
const ALERT_CHANNELS = ["pushover", "trello"] as const;
const SESSION_COOKIE_KEY = "fleaflickerSessionCookie";
const TIP_TABLES_KEY = "tipTables";
const LINEUP_PERIODS_KEY = "lineupPeriods";
// About two days of runs: enough to cover yesterday's late tips and today's targets
const LEDGER_RUNS = 100;
const REPEAT_ALERT_AFTER_MS = 3 * 60 * 60 * 1000;

export class LineupRunner extends DurableObject<Env> {
  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    ctx.storage.sql.exec("CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, record TEXT NOT NULL)");
  }

  // Cron can deliver a tick twice, and a tick, alarm and manual run can interleave while one awaits Fleaflicker
  private tickInFlight = false;

  async tick(trigger: "cron" | "alarm") {
    if (this.tickInFlight) return;
    this.tickInFlight = true;
    let healthy = false;
    try {
      healthy = await this.planAndRun(trigger);
    } finally {
      this.tickInFlight = false;
      if (this.env.HEALTHCHECK_URL) await fetchWithTimeout(healthy ? this.env.HEALTHCHECK_URL : `${this.env.HEALTHCHECK_URL}/fail`, { method: "POST" });
    }
  }

  private async planAndRun(trigger: "cron" | "alarm") {
    const eligibleLineupPeriods = (await this.ctx.storage.get<LineupPeriod[]>(LINEUP_PERIODS_KEY)) ?? (await this.fetchRoster()).eligibleLineupPeriods;
    const planNow = async () => {
      const now = new Date();
      const tipTables = (await this.ctx.storage.get<TipTable[]>(TIP_TABLES_KEY)) ?? [];
      return planTick(now, findCurrentDay(eligibleLineupPeriods, now.getTime()), tipTables, this.ledger());
    };
    const { runDays } = await planNow();
    const record = runDays.length > 0 ? await this.run(trigger, runDays) : undefined;
    const { missedTips, nextTarget } = await planNow();
    for (const missedTip of missedTips) await this.alertMissedTip(missedTip);
    await this.ctx.storage.setAlarm(nextTarget);
    return !record || listProblems(record).length === 0;
  }

  async run(trigger: RunRecord["trigger"] = "manual", days?: number[]): Promise<RunRecord> {
    const record: RunRecord = { trigger, startedAt: new Date().toISOString(), days: [] };
    try {
      await this.checkDays(record, days);
    } catch (error) {
      record.error = String(error);
    }
    const problems = listProblems(record);
    if (problems.length > 0) record.alert = await this.alertFailure(trigger, problems).catch((error) => ({ error: String(error) }));
    this.ctx.storage.sql.exec("INSERT INTO runs (record) VALUES (?)", JSON.stringify(record));
    return record;
  }

  private async alertFailure(trigger: RunRecord["trigger"], problems: string[]) {
    const alert: Alert = { title: `Lineup run (${trigger}) failed`, body: problems.map((problem) => `- ${problem}`).join("\n"), priority: 1 };
    return this.notify(alert, { key: "lastAlert", fingerprint: problems.join("\n"), repeatAfterMs: REPEAT_ALERT_AFTER_MS });
  }

  private async alertMissedTip({ at, players }: DayTip) {
    const tipTime = new Date(at).toLocaleTimeString("en-US", { timeZone: "America/Chicago", hour: "numeric", minute: "2-digit" });
    const alert: Alert = {
      title: `Lineup not checked before the ${tipTime} CT tip`,
      body: `No successful run since 45 min before the tip. Check the lineup now.\nPlayers: ${players.join(", ")}`,
      priority: 2,
    };
    const sends = await this.notify(alert, { key: `missedTip:${at}`, fingerprint: at, repeatAfterMs: Infinity });
    console.log(JSON.stringify({ event: "missedTipAlert", at, sends }));
  }

  private async notify(alert: Alert, dedupe: { key: string; fingerprint: string; repeatAfterMs: number }) {
    const sends: RunRecord["alert"] = {};
    for (const channel of ALERT_CHANNELS) {
      const lastAlertKey = `${dedupe.key}:${channel}`;
      const lastAlert = await this.ctx.storage.get<{ fingerprint: string; at: number; cardId?: string }>(lastAlertKey);
      const sameFailure = lastAlert?.fingerprint === dedupe.fingerprint;
      if (sameFailure && Date.now() - lastAlert.at < dedupe.repeatAfterMs) continue;
      const send = channel === "pushover" ? this.sendPushover(alert) : this.postToTrello(alert, sameFailure ? lastAlert.cardId : undefined);
      const { accepted, cardId, ...sendRecord } = await send.catch((error): AlertOutcome => ({ accepted: false, error: String(error) }));
      sends[channel] = sendRecord;
      if (accepted) await this.ctx.storage.put(lastAlertKey, { fingerprint: dedupe.fingerprint, at: Date.now(), cardId });
    }
    return sends;
  }

  private async sendPushover({ title, body, priority }: Alert): Promise<AlertOutcome> {
    if (!this.env.PUSHOVER_TOKEN || !this.env.PUSHOVER_USER) return { accepted: false, error: "PUSHOVER_TOKEN or PUSHOVER_USER not set" };
    // Emergency priority re-alerts every `retry` seconds until acknowledged or `expire` passes
    const emergency = priority === 2 ? { retry: "60", expire: "1800" } : {};
    const response = await fetchWithTimeout(PUSHOVER_URL, {
      method: "POST",
      body: new URLSearchParams({ token: this.env.PUSHOVER_TOKEN, user: this.env.PUSHOVER_USER, title, message: body, url: this.env.LINEUP_URL, priority: String(priority), ...emergency }),
    });
    const accepted = response.ok && (await response.clone().json<{ status: number }>()).status === 1;
    return summarizeAlertResponse(response, accepted);
  }

  private async postToTrello({ title, body }: Alert, sameFailureCardId?: string): Promise<AlertOutcome> {
    if (!this.env.TRELLO_API_KEY || !this.env.TRELLO_TOKEN || !this.env.TRELLO_LIST) return { accepted: false, error: "TRELLO_API_KEY, TRELLO_TOKEN or TRELLO_LIST not set" };
    const authorization = `OAuth oauth_consumer_key="${this.env.TRELLO_API_KEY}", oauth_token="${this.env.TRELLO_TOKEN}"`;
    if (sameFailureCardId && (await this.isTrelloCardOpen(sameFailureCardId, authorization))) {
      const commentUrl = `${TRELLO_CARDS_URL}/${sameFailureCardId}/actions/comments?${new URLSearchParams({ text: `Still failing:\n${body}` })}`;
      const response = await fetchWithTimeout(commentUrl, { method: "POST", headers: { Authorization: authorization } });
      return { ...(await summarizeAlertResponse(response, response.ok)), cardId: sameFailureCardId };
    }
    const response = await fetchWithTimeout(TRELLO_CARDS_URL, {
      method: "POST",
      headers: { Authorization: authorization, "Content-Type": "application/json" },
      body: JSON.stringify({ idList: this.env.TRELLO_LIST, name: title, desc: `${body}\n\n${this.env.LINEUP_URL}` }),
    });
    const cardId = response.ok ? (await response.clone().json<{ id: string }>()).id : undefined;
    return { ...(await summarizeAlertResponse(response, response.ok)), cardId };
  }

  private async isTrelloCardOpen(cardId: string, authorization: string) {
    const response = await fetchWithTimeout(`${TRELLO_CARDS_URL}/${cardId}?fields=closed`, { headers: { Authorization: authorization } });
    return response.ok && !(await response.json<{ closed: boolean }>()).closed;
  }

  private async checkDays(record: RunRecord, days?: number[]) {
    days ??= [findCurrentDay((await this.fetchRoster()).eligibleLineupPeriods, Date.now())];
    for (const day of days) {
      let lineupPage = await this.fetchLineupPage(day);
      if (!lineupPage.loggedIn && !record.login) {
        record.login = await this.logIn();
        lineupPage = await this.fetchLineupPage(day);
      }
      const { html, ...pageSummary } = lineupPage;
      const dayCheck: DayCheck = { day, lineupPage: pageSummary };
      record.days.push(dayCheck);
      dayCheck.decision = await decideLineup(html, await this.fetchRoster(day));
      if (pageSummary.loggedIn) await this.storeTipTable({ day, fetchedAt: record.startedAt, tips: parseGameTips(html) });
    }
  }

  private async storeTipTable(tipTable: TipTable) {
    const tipTables = (await this.ctx.storage.get<TipTable[]>(TIP_TABLES_KEY)) ?? [];
    const otherRecentDays = tipTables.filter((table) => table.day !== tipTable.day && table.day >= tipTable.day - 1);
    await this.ctx.storage.put(TIP_TABLES_KEY, [...otherRecentDays, tipTable]);
  }

  private ledger(): LedgerEntry[] {
    return this.recentRuns(LEDGER_RUNS).flatMap((record) => {
      const runOk = listProblems({ ...record, days: [] }).length === 0;
      return record.days.map((dayCheck) => ({ startedAt: record.startedAt, ok: runOk && listDayProblems(dayCheck).length === 0, days: [dayCheck.day] }));
    });
  }

  private async fetchRoster(day?: number) {
    const [, leagueId, teamId] = this.env.LINEUP_URL.match(/leagues\/(\d+)\/teams\/(\d+)/)!;
    const url = new URL("https://www.fleaflicker.com/api/FetchRoster");
    url.search = new URLSearchParams({ sport: "NBA", league_id: leagueId, team_id: teamId, ...(day ? { scoring_period: String(day) } : {}) }).toString();
    const response = await fetchWithTimeout(url, { headers: await this.sessionHeaders() });
    if (!response.ok) throw new Error(`Roster API returned HTTP ${response.status}`);
    const roster = await response.json<ApiRoster & { eligibleLineupPeriods: LineupPeriod[] }>();
    await this.ctx.storage.put(LINEUP_PERIODS_KEY, roster.eligibleLineupPeriods);
    return roster;
  }

  private async sessionHeaders(): Promise<Record<string, string>> {
    const sessionCookie = await this.ctx.storage.get<string>(SESSION_COOKIE_KEY);
    return sessionCookie ? { Cookie: sessionCookie } : {};
  }

  recentRuns(limit = 20): RunRecord[] {
    return this.ctx.storage.sql
      .exec<{ record: string }>("SELECT record FROM runs ORDER BY id DESC LIMIT ?", limit)
      .toArray()
      .map((row) => JSON.parse(row.record));
  }

  async alarm() {
    await this.tick("alarm");
  }

  private async fetchLineupPage(day: number) {
    const fantasyStatsView = `${this.env.LINEUP_URL}?statType=0&week=${day}`;
    const response = await fetchWithTimeout(fantasyStatsView, { headers: await this.sessionHeaders() });
    const html = await response.text();
    const loggedIn = html.includes('href="/logout"');
    return { status: response.status, loggedIn, html };
  }

  // A failed login re-renders the form with the submitted email and password, so its body is never read
  private async logIn() {
    const response = await fetchWithTimeout(FLEAFLICKER_LOGIN_URL, {
      method: "POST",
      body: new URLSearchParams({ email: this.env.FF_EMAIL, password: this.env.FF_PASSWORD, keepMe: "true" }),
      redirect: "manual",
    });
    const sessionCookie = response.headers
      .getSetCookie()
      .map((cookie) => cookie.split(";")[0])
      .find((cookie) => cookie.startsWith("cookieId="));
    if (sessionCookie) await this.ctx.storage.put(SESSION_COOKIE_KEY, sessionCookie);
    return { status: response.status, gotSessionCookie: sessionCookie != null };
  }
}

export default {
  async fetch(request, env) {
    if (!hasRunToken(request, env.RUN_TOKEN)) return new Response("Unauthorized", { status: 401 });
    const { pathname } = new URL(request.url);
    const runner = env.RUNNER.getByName("primary");
    if (request.method === "POST" && pathname === "/run") return Response.json(await runner.run());
    if (request.method === "GET" && pathname === "/runs") return Response.json(await runner.recentRuns());
    return new Response("Not found", { status: 404 });
  },

  async scheduled(_controller, env) {
    await env.RUNNER.getByName("primary").tick("cron");
  },
} satisfies ExportedHandler<Env>;

type RunRecord = {
  trigger: "manual" | "alarm" | "cron";
  startedAt: string;
  login?: { status: number; gotSessionCookie: boolean };
  days: DayCheck[];
  error?: string;
  alert?: Partial<Record<(typeof ALERT_CHANNELS)[number], AlertSend>>;
};

type Alert = { title: string; body: string; priority: 1 | 2 };

type AlertSend = { status: number; response?: string } | { error: string };

type AlertOutcome = AlertSend & { accepted: boolean; cardId?: string };

type DayCheck = { day: number; lineupPage: { status: number; loggedIn: boolean }; decision?: LineupDecision };

type LineupPeriod = { ordinal: number; low: { startEpochMilli: string } };

// Before the season starts, the first day is the one to set
function findCurrentDay(periods: LineupPeriod[], nowMs: number) {
  const started = periods.filter((period) => Number(period.low.startEpochMilli) <= nowMs);
  return (started.at(-1) ?? periods[0]).ordinal;
}

function listProblems({ login, days, error }: RunRecord) {
  const loginProblems = login && !login.gotSessionCookie ? [`Fleaflicker login failed (HTTP ${login.status}, no session cookie)`] : [];
  return [...loginProblems, ...days.flatMap(listDayProblems), ...(error ? [error] : [])];
}

function listDayProblems({ lineupPage, decision }: DayCheck) {
  const problems: string[] = [];
  if (lineupPage.status !== 200) problems.push(`Lineup page returned HTTP ${lineupPage.status}`);
  if (decision && !decision.ok) problems.push(...decision.errors);
  return problems;
}

async function summarizeAlertResponse(response: Response, accepted: boolean) {
  return accepted ? { accepted, status: response.status } : { accepted, status: response.status, response: (await response.text()).slice(0, 200) };
}

function hasRunToken(request: Request, runToken: string) {
  const given = new TextEncoder().encode(request.headers.get("Authorization") ?? "");
  const expected = new TextEncoder().encode(`Bearer ${runToken}`);
  return given.byteLength === expected.byteLength && crypto.subtle.timingSafeEqual(given, expected);
}
