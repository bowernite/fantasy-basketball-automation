import { DurableObject } from "cloudflare:workers";
import { type ApiRoster, decideLineup, type LineupDecision } from "./decide-lineup";
import { type LedgerEntry, parseGameTips, planTick, type TipTable } from "./lineup-schedule";

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
      if (this.env.HEALTHCHECK_URL) await fetch(healthy ? this.env.HEALTHCHECK_URL : `${this.env.HEALTHCHECK_URL}/fail`, { method: "POST" });
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
    await this.ctx.storage.setAlarm((await planNow()).nextTarget);
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
    const alert = { title: `Lineup run (${trigger}) failed`, body: problems.map((problem) => `- ${problem}`).join("\n") };
    const fingerprint = problems.join("\n");
    const sends: RunRecord["alert"] = {};
    for (const channel of ALERT_CHANNELS) {
      const lastAlertKey = `lastAlert:${channel}`;
      const lastAlert = await this.ctx.storage.get<{ fingerprint: string; at: number }>(lastAlertKey);
      const alreadyAlerted = lastAlert?.fingerprint === fingerprint && Date.now() - lastAlert.at < REPEAT_ALERT_AFTER_MS;
      if (alreadyAlerted) continue;
      const send = channel === "pushover" ? this.sendPushover(alert) : this.createTrelloCard(alert);
      const { accepted, ...sendRecord } = await send.catch((error) => ({ accepted: false, error: String(error) }));
      sends[channel] = sendRecord;
      if (accepted) await this.ctx.storage.put(lastAlertKey, { fingerprint, at: Date.now() });
    }
    return sends;
  }

  private async sendPushover({ title, body }: Alert) {
    const response = await fetch(PUSHOVER_URL, {
      method: "POST",
      body: new URLSearchParams({ token: this.env.PUSHOVER_TOKEN, user: this.env.PUSHOVER_USER, title, message: body, url: this.env.LINEUP_URL, priority: "1" }),
    });
    const accepted = response.ok && (await response.clone().json<{ status: number }>()).status === 1;
    return summarizeAlertResponse(response, accepted);
  }

  private async createTrelloCard({ title, body }: Alert) {
    const response = await fetch(TRELLO_CARDS_URL, {
      method: "POST",
      headers: { Authorization: `OAuth oauth_consumer_key="${this.env.TRELLO_API_KEY}", oauth_token="${this.env.TRELLO_TOKEN}"`, "Content-Type": "application/json" },
      body: JSON.stringify({ idList: this.env.TRELLO_LIST, name: title, desc: `${body}\n\n${this.env.LINEUP_URL}` }),
    });
    return summarizeAlertResponse(response, response.ok);
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
    return this.recentRuns(LEDGER_RUNS).map((record) => ({
      startedAt: record.startedAt,
      ok: listProblems(record).length === 0,
      days: (record.days ?? []).map(({ day }) => day),
    }));
  }

  private async fetchRoster(day?: number) {
    const [, leagueId, teamId] = this.env.LINEUP_URL.match(/leagues\/(\d+)\/teams\/(\d+)/)!;
    const url = new URL("https://www.fleaflicker.com/api/FetchRoster");
    url.search = new URLSearchParams({ sport: "NBA", league_id: leagueId, team_id: teamId, ...(day ? { scoring_period: String(day) } : {}) }).toString();
    const response = await fetch(url, { headers: await this.sessionHeaders() });
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
    const response = await fetch(fantasyStatsView, { headers: await this.sessionHeaders() });
    const html = await response.text();
    const loggedIn = html.includes('href="/logout"');
    return { status: response.status, loggedIn, html };
  }

  // A failed login re-renders the form with the submitted email and password, so its body is never read
  private async logIn() {
    const response = await fetch(FLEAFLICKER_LOGIN_URL, {
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

type Alert = { title: string; body: string };

type AlertSend = { status: number; response?: string } | { error: string };

type DayCheck = { day: number; lineupPage: { status: number; loggedIn: boolean }; decision?: LineupDecision };

type LineupPeriod = { ordinal: number; low: { startEpochMilli: string } };

// Before the season starts, the first day is the one to set
function findCurrentDay(periods: LineupPeriod[], nowMs: number) {
  const started = periods.filter((period) => Number(period.low.startEpochMilli) <= nowMs);
  return (started.at(-1) ?? periods[0]).ordinal;
}

function listProblems({ login, days = [], error }: RunRecord) {
  const problems: string[] = [];
  if (login && !login.gotSessionCookie) problems.push(`Fleaflicker login failed (HTTP ${login.status}, no session cookie)`);
  for (const { lineupPage, decision } of days) {
    if (lineupPage.status !== 200) problems.push(`Lineup page returned HTTP ${lineupPage.status}`);
    if (decision && !decision.ok) problems.push(...decision.errors);
  }
  if (error) problems.push(error);
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
