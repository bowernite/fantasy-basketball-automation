import { DurableObject } from "cloudflare:workers";
import { type ApiRoster, decideLineup, type LineupDecision } from "./decide-lineup";
import { fetchWithTimeout } from "./fetch-with-timeout";
import { type DayTip, type LedgerEntry, parseGameTips, planTick, type TipTable } from "./lineup-schedule";
import { type SaveResult, saveLineup } from "./save-lineup";

const FLEAFLICKER_LOGIN_URL = "https://www.fleaflicker.com/nba/login";
const PUSHOVER_URL = "https://api.pushover.net/1/messages.json";
const PUSHOVER_MAX_MESSAGE_LENGTH = 1024;
const TRELLO_CARDS_URL = "https://api.trello.com/1/cards";
const ALERT_CHANNELS = ["pushover", "trello"] as const;
const SESSION_COOKIE_KEY = "fleaflickerSessionCookie";
const TIP_TABLES_KEY = "tipTables";
const LINEUP_PERIODS_KEY = "lineupPeriods";
const SAVES_ENABLED_KEY = "savesEnabled";
const FAILED_LOGIN_KEY = "failedLogin";
const FAILURE_ALERTS_KEY = "failureAlerts";
const FAILED_SAVE_KEY = "failedSave";
// Repeated failed logins and saves risk a captcha or lockout, so they back off except shortly before a tip
const LOGIN_RETRY_AFTER_MS = 30 * 60 * 1000;
const SAVE_RETRY_AFTER_MS = 30 * 60 * 1000;
const RETRY_TIP_WINDOW_MS = 45 * 60 * 1000;
// About two days of runs: enough to cover yesterday's late tips and today's targets
const LEDGER_RUNS = 100;
const KEPT_RUNS = 1000;
const REPEAT_ALERT_AFTER_MS = 3 * 60 * 60 * 1000;
const FORGET_ALERT_AFTER_MS = 24 * 60 * 60 * 1000;
const SCHEDULE_START_DELAY_MS = 5 * 60 * 1000;

export class LineupRunner extends DurableObject<Env> {
  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    ctx.storage.sql.exec("CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, record TEXT NOT NULL)");
  }

  // Cron can deliver a tick twice, and a tick, alarm and manual run can interleave while one awaits Fleaflicker
  private busy = false;

  async tick(trigger: "cron" | "alarm") {
    if (this.busy) return;
    this.busy = true;
    let healthy = false;
    try {
      healthy = await this.planAndRun(trigger);
    } catch (error) {
      console.error(JSON.stringify({ event: "tickFailed", trigger, error: String(error) }));
      await this.alertFailure(`Lineup tick (${trigger}) failed`, [String(error)]);
    } finally {
      this.busy = false;
      if (this.env.HEALTHCHECK_URL) {
        await fetchWithTimeout(healthy ? this.env.HEALTHCHECK_URL : `${this.env.HEALTHCHECK_URL}/fail`, { method: "POST" }).catch((error) =>
          console.error(JSON.stringify({ event: "deadManPingFailed", error: String(error) })),
        );
      }
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

  // Only ticks re-arm the alarm, so a manual run starts the schedule when cron never has
  async runManually() {
    if (this.busy) return undefined;
    this.busy = true;
    try {
      const record = await this.run("manual");
      if (!(await this.ctx.storage.getAlarm())) await this.ctx.storage.setAlarm(Date.now() + SCHEDULE_START_DELAY_MS);
      return record;
    } finally {
      this.busy = false;
    }
  }

  async run(trigger: RunRecord["trigger"] = "manual", days?: number[]): Promise<RunRecord> {
    const record: RunRecord = { trigger, startedAt: new Date().toISOString(), days: [] };
    try {
      await this.checkDays(record, days);
    } catch (error) {
      record.error = String(error);
    }
    const problems = listProblems(record);
    if (problems.length > 0) record.alert = await this.alertFailure(`Lineup run (${trigger}) failed`, problems).catch((error) => ({ error: String(error) }));
    else await this.ctx.storage.delete(ALERT_CHANNELS.map((channel) => `${FAILURE_ALERTS_KEY}:${channel}`));
    const warnings = record.days.flatMap(({ decision }) => (decision?.ok ? decision.warnings : []));
    if (warnings.length > 0) record.warningAlert = await this.alertWarnings(trigger, warnings).catch((error) => ({ error: String(error) }));
    this.ctx.storage.sql.exec("INSERT INTO runs (record) VALUES (?)", JSON.stringify(record));
    this.ctx.storage.sql.exec("DELETE FROM runs WHERE id <= (SELECT MAX(id) FROM runs) - ?", KEPT_RUNS);
    return record;
  }

  private async alertFailure(title: string, problems: string[]) {
    const alert: Alert = { title, body: problems.map((problem) => `- ${problem}`).join("\n"), priority: 1 };
    return this.notify(alert, { key: FAILURE_ALERTS_KEY, fingerprint: problems.join("\n"), repeatAfterMs: REPEAT_ALERT_AFTER_MS });
  }

  private async alertWarnings(trigger: RunRecord["trigger"], warnings: string[]) {
    const alert: Alert = { title: `Lineup run (${trigger}) has warnings`, body: warnings.map((warning) => `- ${warning}`).join("\n"), priority: 0 };
    return this.notify(alert, { key: "warningAlerts", fingerprint: warnings.join("\n"), repeatAfterMs: REPEAT_ALERT_AFTER_MS });
  }

  private async alertMissedTip({ at, players }: DayTip) {
    const tipTime = new Date(at).toLocaleTimeString("en-US", { timeZone: "America/Chicago", hour: "numeric", minute: "2-digit" });
    const alert: Alert = {
      title: `Lineup not checked before the ${tipTime} CT tip`,
      body: `No successful run since 45 min before the tip. Check the lineup now.\nPlayers: ${players.join(", ")}`,
      priority: 2,
    };
    const sends = await this.notify(alert, { key: `missedTipAlerts:${at}`, fingerprint: at, repeatAfterMs: Infinity });
    console.log(JSON.stringify({ event: "missedTipAlert", at, sends }));
  }

  private async notify(alert: Alert, dedupe: { key: string; fingerprint: string; repeatAfterMs: number }) {
    const sends: AlertSends = {};
    for (const channel of ALERT_CHANNELS) {
      const sentAlertsKey = `${dedupe.key}:${channel}`;
      const sentAlerts = (await this.ctx.storage.get<Record<string, { at: number; cardId?: string }>>(sentAlertsKey)) ?? {};
      const lastAlert = sentAlerts[dedupe.fingerprint];
      if (lastAlert && Date.now() - lastAlert.at < dedupe.repeatAfterMs) continue;
      const send = channel === "pushover" ? this.sendPushover(alert) : this.postToTrello(alert, lastAlert?.cardId);
      const { accepted, cardId, ...sendRecord } = await send.catch((error): AlertOutcome => ({ accepted: false, error: String(error) }));
      sends[channel] = sendRecord;
      if (!accepted) continue;
      const recentAlerts = Object.entries(sentAlerts).filter(([, { at }]) => Date.now() - at < FORGET_ALERT_AFTER_MS);
      await this.ctx.storage.put(sentAlertsKey, { ...Object.fromEntries(recentAlerts), [dedupe.fingerprint]: { at: Date.now(), cardId } });
    }
    return sends;
  }

  private async sendPushover({ title, body, priority }: Alert): Promise<AlertOutcome> {
    if (!this.env.PUSHOVER_TOKEN || !this.env.PUSHOVER_USER) return { accepted: false, error: "PUSHOVER_TOKEN or PUSHOVER_USER not set" };
    // Emergency priority re-alerts every `retry` seconds until acknowledged or `expire` passes
    const emergency = priority === 2 ? { retry: "60", expire: "1800" } : {};
    const message = body.length > PUSHOVER_MAX_MESSAGE_LENGTH ? `${body.slice(0, PUSHOVER_MAX_MESSAGE_LENGTH - 1)}…` : body;
    const response = await fetchWithTimeout(PUSHOVER_URL, {
      method: "POST",
      body: new URLSearchParams({ token: this.env.PUSHOVER_TOKEN, user: this.env.PUSHOVER_USER, title, message, url: this.env.LINEUP_URL, priority: String(priority), ...emergency }),
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
      const dayCheck: DayCheck = { day };
      record.days.push(dayCheck);
      await this.checkDay(record, dayCheck).catch((error) => (dayCheck.error = String(error)));
    }
  }

  private async checkDay(record: RunRecord, dayCheck: DayCheck) {
    const { day } = dayCheck;
    let lineupPage = await this.fetchLineupPage(day);
    if (!lineupPage.loggedIn && !record.login) {
      const loginAttempt = await this.logInUnlessBackingOff(day);
      record.login = loginAttempt.login;
      lineupPage = loginAttempt.lineupPage ?? lineupPage;
    }
    const { html, ...pageSummary } = lineupPage;
    dayCheck.lineupPage = pageSummary;
    if (pageSummary.status === 200) await this.storeTipTable({ day, fetchedAt: record.startedAt, tips: parseGameTips(html) });
    dayCheck.decision = await decideLineup(html, await this.fetchRoster(day));
    if (dayCheck.decision.ok && (await this.ctx.storage.get<boolean>(SAVES_ENABLED_KEY))) dayCheck.save = await this.saveUnlessBackingOff(day, dayCheck.decision);
  }

  private async saveUnlessBackingOff(day: number, decision: Extract<LineupDecision, { ok: true }>): Promise<DayCheck["save"]> {
    const failedSaveKey = `${FAILED_SAVE_KEY}:${day}`;
    const failedSave = await this.ctx.storage.get<{ at: number; body: string; save: SaveResult }>(failedSaveKey);
    const tipTables = (await this.ctx.storage.get<TipTable[]>(TIP_TABLES_KEY)) ?? [];
    const sameSaveFailedRecently = failedSave?.body === decision.body && Date.now() - failedSave.at < SAVE_RETRY_AFTER_MS;
    if (sameSaveFailedRecently && !hasTipWithin(tipTables, RETRY_TIP_WINDOW_MS)) return { ...failedSave.save, posted: false, backedOff: true };
    const save = await saveLineup(decision, await this.sessionHeaders());
    if (save.problems.length > 0) await this.ctx.storage.put(failedSaveKey, { at: Date.now(), body: decision.body, save });
    else await this.ctx.storage.delete(failedSaveKey);
    return save;
  }

  private async storeTipTable(tipTable: TipTable) {
    const tipTables = (await this.ctx.storage.get<TipTable[]>(TIP_TABLES_KEY)) ?? [];
    const otherRecentDays = tipTables.filter((table) => table.day !== tipTable.day && table.day >= tipTable.day - 1);
    await this.ctx.storage.put(TIP_TABLES_KEY, [...otherRecentDays, tipTable]);
  }

  private ledger(): LedgerEntry[] {
    return this.recentRuns(LEDGER_RUNS).flatMap((record) => {
      const runOk = listProblems({ ...record, days: [] }).length === 0;
      // Records from before multi-day runs have no `days`
      return (record.days ?? []).map((dayCheck) => ({ startedAt: record.startedAt, ok: runOk && listDayProblems(dayCheck).length === 0, days: [dayCheck.day] }));
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

  async setSaves(enabled: boolean) {
    await this.ctx.storage.put(SAVES_ENABLED_KEY, enabled);
    return { enabled };
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

  private async logInUnlessBackingOff(day: number) {
    const failedLogin = await this.ctx.storage.get<{ at: number; login: LoginOutcome }>(FAILED_LOGIN_KEY);
    const tipTables = (await this.ctx.storage.get<TipTable[]>(TIP_TABLES_KEY)) ?? [];
    const backingOff = failedLogin && Date.now() - failedLogin.at < LOGIN_RETRY_AFTER_MS && !hasTipWithin(tipTables, RETRY_TIP_WINDOW_MS);
    if (backingOff) return { login: { ...failedLogin.login, backedOff: true } };
    const response = await this.logIn();
    const lineupPage = response.gotSessionCookie ? await this.fetchLineupPage(day) : undefined;
    const stillSignedOut = lineupPage?.status === 200 && !lineupPage.loggedIn;
    const login: LoginOutcome = { ...response, ...(stillSignedOut && { stillSignedOut }) };
    if (!loginFailed(login)) await this.ctx.storage.delete(FAILED_LOGIN_KEY);
    else await this.ctx.storage.put(FAILED_LOGIN_KEY, { at: Date.now(), login });
    return { login, lineupPage };
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
    if (request.method === "POST" && pathname === "/run") {
      const record = await runner.runManually();
      return record ? Response.json(record) : new Response("A run is already in progress", { status: 409 });
    }
    if (request.method === "GET" && pathname === "/runs") return Response.json(await runner.recentRuns());
    if (request.method === "PUT" && pathname === "/saves") {
      const { enabled } = await request.json<{ enabled?: unknown }>();
      return Response.json(await runner.setSaves(enabled === true));
    }
    return new Response("Not found", { status: 404 });
  },

  async scheduled(_controller, env) {
    await env.RUNNER.getByName("primary").tick("cron");
  },
} satisfies ExportedHandler<Env>;

type RunRecord = {
  trigger: "manual" | "alarm" | "cron";
  startedAt: string;
  login?: LoginOutcome;
  days: DayCheck[];
  error?: string;
  alert?: AlertSends;
  warningAlert?: AlertSends;
};

type AlertSends = Partial<Record<(typeof ALERT_CHANNELS)[number], AlertSend>>;

type LoginOutcome = { status: number; gotSessionCookie: boolean; stillSignedOut?: true; backedOff?: true };

type Alert = { title: string; body: string; priority: 0 | 1 | 2 };

type AlertSend = { status: number; response?: string } | { error: string };

type AlertOutcome = AlertSend & { accepted: boolean; cardId?: string };

type DayCheck = { day: number; lineupPage?: { status: number; loggedIn: boolean }; decision?: LineupDecision; save?: SaveResult & { backedOff?: true }; error?: string };

type LineupPeriod = { ordinal: number; low: { startEpochMilli: string } };

// Before the season starts, the first day is the one to set
function findCurrentDay(periods: LineupPeriod[], nowMs: number) {
  const started = periods.filter((period) => Number(period.low.startEpochMilli) <= nowMs);
  return (started.at(-1) ?? periods[0]).ordinal;
}

function listProblems({ login, days, error }: RunRecord) {
  const loginProblems = login && loginFailed(login) ? [`Fleaflicker login failed (HTTP ${login.status}, ${login.gotSessionCookie ? "still signed out" : "no session cookie"})`] : [];
  return [...loginProblems, ...days.flatMap(listDayProblems), ...(error ? [error] : [])];
}

function loginFailed({ gotSessionCookie, stillSignedOut }: LoginOutcome) {
  return !gotSessionCookie || stillSignedOut === true;
}

function listDayProblems({ lineupPage, decision, save, error }: DayCheck) {
  const problems: string[] = [];
  if (lineupPage && lineupPage.status !== 200) problems.push(`Lineup page returned HTTP ${lineupPage.status}`);
  if (decision && !decision.ok) problems.push(...decision.errors);
  problems.push(...(save?.problems ?? []));
  if (error) problems.push(error);
  return problems;
}

function hasTipWithin(tipTables: TipTable[], windowMs: number) {
  return tipTables.some(({ tips }) =>
    tips.some(({ at }) => {
      const untilTipMs = Date.parse(at) - Date.now();
      return untilTipMs >= 0 && untilTipMs <= windowMs;
    }),
  );
}

async function summarizeAlertResponse(response: Response, accepted: boolean) {
  return accepted ? { accepted, status: response.status } : { accepted, status: response.status, response: (await response.text()).slice(0, 200) };
}

function hasRunToken(request: Request, runToken: string | undefined) {
  if (!runToken) return false;
  const given = new TextEncoder().encode(request.headers.get("Authorization") ?? "");
  const expected = new TextEncoder().encode(`Bearer ${runToken}`);
  return given.byteLength === expected.byteLength && crypto.subtle.timingSafeEqual(given, expected);
}
