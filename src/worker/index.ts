import { DurableObject } from "cloudflare:workers";
import { parseHTML } from "linkedom";
import { type ApiRoster, decideLineup, type LineupDecision } from "./decide-lineup";
import { fetchWithTimeout } from "./fetch-with-timeout";
import { compareInjuryFeeds, fetchEspnInjuries, type InjuryComparison, type InjuryDisagreement, type InjuryRoster } from "./injury-cross-check";
import { type DayTip, type LedgerEntry, parseGameTips, planTick, RETRY_TIP_WINDOW_MS, TIP_CUTOFF_MS, type TipTable } from "./lineup-schedule";
import { type SaveResult, saveLineup } from "./save-lineup";
import { findUntaggedNews, type UntaggedNews } from "./untagged-news";
import { matchOutNews, type OutNewsMatch } from "./untagged-out-match";

const FLEAFLICKER_LOGIN_URL = "https://www.fleaflicker.com/nba/login";
const PUSHOVER_URL = "https://api.pushover.net/1/messages.json";
const PUSHOVER_MAX_MESSAGE_LENGTH = 1024;
const NTFY_URL = "https://ntfy.sh";
const NTFY_PRIORITIES = { 0: 3, 1: 4, 2: 5 } as const;
// From Cloudflare, about half of ntfy requests fail (per-IP quota on shared egress, or no connection); each attempt may leave from another IP
const NTFY_ATTEMPTS = 3;
const TRELLO_API_URL = "https://api.trello.com/1";
const ALERT_CHANNELS = ["pushover", "trello"] as const;
const SESSION_COOKIE_KEY = "fleaflickerSessionCookie";
const TIP_TABLES_KEY = "tipTables";
const LINEUP_PERIODS_KEY = "lineupPeriods";
const SAVES_ENABLED_KEY = "savesEnabled";
const UNTAGGED_OUT_NEWS_ACT_KEY = "untaggedOutNewsAct";
const FAILED_LOGIN_KEY = "failedLogin";
const FAILURE_ALERTS_KEY = "failureAlerts";
const FAILED_SAVE_KEY = "failedSave";
const INJURY_ALERTS_KEY = "injuryAlerts";
const LOCKED_ROWS_CAPTURED_DAY_KEY = "lockedRowsCapturedDay";
// Repeated failed logins and saves risk a captcha or lockout, so they back off except shortly before a tip
const LOGIN_RETRY_AFTER_MS = 30 * 60 * 1000;
const SAVE_RETRY_AFTER_MS = 30 * 60 * 1000;
const URGENT_TIP_WINDOW_MS = 3 * 60 * 60 * 1000;
// About two days of runs: enough to cover yesterday's late tips and today's targets
const LEDGER_RUNS = 100;
const KEPT_RUNS = 1000;
const REPEAT_ALERT_AFTER_MS = 3 * 60 * 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;
const FORGET_ALERT_AFTER_MS = 24 * 60 * 60 * 1000;
const REPEAT_INJURY_ALERT_AFTER_MS = 24 * 60 * 60 * 1000;
const SAVES_OFF_WARNING_WINDOW_MS = 24 * 60 * 60 * 1000;
// Player alerts (injury disagreements, untagged news) start this long before the fantasy season's first day
const PLAYER_ALERTS_LEAD_MS = 3 * DAY_MS;
const WAKE_INTERVAL_MS = 5 * 60 * 1000;
const LISTED_ALERTS = 50;
const KEPT_CAPTURES = 10;

export class LineupRunner extends DurableObject<Env> {
  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    ctx.storage.sql.exec("CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, record TEXT NOT NULL)");
    ctx.storage.sql.exec("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, alert TEXT NOT NULL)");
    ctx.storage.sql.exec("CREATE TABLE IF NOT EXISTS captures (id INTEGER PRIMARY KEY AUTOINCREMENT, capture TEXT NOT NULL)");
  }

  // Cron can deliver a tick twice, and a tick, alarm and manual run can interleave while one awaits Fleaflicker
  private busy = false;
  private alertUndelivered = false;

  async tick(trigger: "cron" | "alarm") {
    if (this.busy) return;
    this.busy = true;
    this.alertUndelivered = false;
    let healthy = false;
    let nextTargetMs = Infinity;
    try {
      ({ healthy, nextTargetMs } = await this.planAndRun(trigger));
    } catch (error) {
      console.error(JSON.stringify({ event: "tickFailed", trigger, error: String(error) }));
      await this.alertFailure("Lineup tick failed", [String(error)]);
    } finally {
      this.busy = false;
      // Waking at least every 5 min retries failed runs and keeps the schedule going when cron doesn't fire
      await this.ctx.storage.setAlarm(Math.min(nextTargetMs, Date.now() + WAKE_INTERVAL_MS));
      if (this.env.HEALTHCHECK_URL) {
        await fetchWithTimeout(healthy && !this.alertUndelivered ? this.env.HEALTHCHECK_URL : `${this.env.HEALTHCHECK_URL}/fail`, { method: "POST" }).catch((error) =>
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
      return planTick(now, findCurrentDay(eligibleLineupPeriods, now.getTime()), tipTables, this.ledger(), eligibleLineupPeriods.at(-1)?.ordinal);
    };
    const { runDays } = await planNow();
    const record = runDays.length > 0 ? await this.run(trigger, runDays) : undefined;
    const { missedTips, nextTarget } = await planNow();
    for (const missedTip of missedTips) await this.alertMissedTip(missedTip);
    const tipTables = (await this.ctx.storage.get<TipTable[]>(TIP_TABLES_KEY)) ?? [];
    const savesOff = !(await this.ctx.storage.get<boolean>(SAVES_ENABLED_KEY));
    if (savesOff && hasTipWithin(tipTables, SAVES_OFF_WARNING_WINDOW_MS)) await this.alertSavesOff();
    return { healthy: !record || listProblems(record).length === 0, nextTargetMs: nextTarget.getTime() };
  }

  // Only ticks re-arm the alarm, so a manual run starts the schedule when cron never has
  async runManually() {
    if (this.busy) return undefined;
    this.busy = true;
    try {
      const record = await this.run("manual");
      if (!(await this.ctx.storage.getAlarm())) await this.ctx.storage.setAlarm(Date.now() + WAKE_INTERVAL_MS);
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
    if (problems.length > 0) record.alert = await this.alertFailure("Lineup run failed", problems).catch((error) => ({ error: String(error) }));
    else await this.ctx.storage.delete([...ALERT_CHANNELS, "log"].map((channel) => `${FAILURE_ALERTS_KEY}:${channel}`));
    const warnings = [...(record.warnings ?? []), ...record.days.flatMap(({ decision, warnings = [] }) => [...warnings, ...(decision?.ok ? decision.warnings : [])])];
    if (warnings.length > 0) record.warningAlert = await this.alertWarnings(warnings).catch((error) => ({ error: String(error) }));
    this.ctx.storage.sql.exec("INSERT INTO runs (record) VALUES (?)", JSON.stringify(record));
    this.ctx.storage.sql.exec("DELETE FROM runs WHERE id <= (SELECT MAX(id) FROM runs) - ?", KEPT_RUNS);
    return record;
  }

  private async alertFailure(title: string, problems: string[]) {
    const tipTables = (await this.ctx.storage.get<TipTable[]>(TIP_TABLES_KEY)) ?? [];
    const body = problems.map((problem) => `- ${problem}`).join("\n");
    const dedupe = { key: FAILURE_ALERTS_KEY, fingerprint: problems.join("\n") };
    if (!hasTipWithin(tipTables, Infinity)) {
      // After the fantasy season's last day no game is at stake; before it, with no upcoming tip stored (All-Star break, or tip times stopped parsing), one may still be near, so it reaches the phone, daily and within quiet hours
      const periods = (await this.ctx.storage.get<LineupPeriod[]>(LINEUP_PERIODS_KEY)) ?? [];
      const seasonOver = periods.length > 0 && Date.now() - Number(periods.at(-1)!.low.startEpochMilli) > DAY_MS;
      return this.notify({ title, body, priority: 0, push: !seasonOver }, { ...dedupe, repeatAfterMs: DAY_MS });
    }
    // Priority 1 bypasses the phone's quiet hours, so it's kept for failures that can still cost a game
    const priority = hasTipWithin(tipTables, URGENT_TIP_WINDOW_MS) ? 1 : 0;
    return this.notify({ title, body, priority }, { ...dedupe, repeatAfterMs: REPEAT_ALERT_AFTER_MS });
  }

  private async alertWarnings(warnings: string[]) {
    const alert: Alert = { title: "Lineup run has warnings", body: warnings.map((warning) => `- ${warning}`).join("\n"), priority: 0 };
    return this.notify(alert, { key: "warningAlerts", fingerprint: warnings.join("\n"), repeatAfterMs: REPEAT_ALERT_AFTER_MS });
  }

  private async alertInjuryDisagreements(disagreements: InjuryDisagreement[]) {
    const sends: AlertSends[] = [];
    for (const { player, message, urgent } of disagreements) {
      const alert: Alert = { title: `Fleaflicker and ESPN disagree on ${player}`, body: `- ${message}`, priority: urgent ? 1 : 0 };
      sends.push(await this.notify(alert, { key: INJURY_ALERTS_KEY, fingerprint: message, repeatAfterMs: REPEAT_INJURY_ALERT_AFTER_MS }));
    }
    return sends.filter((send) => Object.keys(send).length > 0);
  }

  // News can rule a player out before Fleaflicker tags him; a starter tipping within 3 h reaches the phone
  private async alertUntaggedNews(record: RunRecord) {
    const sends: AlertSends[] = [];
    for (const { decision, untaggedOutNews = [] } of record.days) {
      const starters = decision?.ok ? decision.starters.map(({ player }) => player) : [];
      for (const { player, postedAt, headline, tipAt, matched, benched } of untaggedOutNews) {
        if (!tipAt || !matched) continue;
        const title = matched.status === "D" ? `News says ${player} is doubtful` : `${benched ? "Benched" : "Would bench"} ${player} (news: out, no Fleaflicker tag)`;
        const posted = new Date(postedAt).toLocaleString("en-US", { timeZone: "America/Chicago", weekday: "short", hour: "numeric", minute: "2-digit" });
        const alert: Alert = { title, body: `${headline} (posted ${posted} CT)\n> ${matched.sentence}`, priority: starters.includes(player) && isWithin(tipAt, URGENT_TIP_WINDOW_MS) ? 1 : 0 };
        sends.push(await this.notify(alert, { key: "untaggedNewsAlerts", fingerprint: `${player}|${postedAt}`, repeatAfterMs: DAY_MS }));
      }
    }
    const sent = sends.filter((send) => Object.keys(send).length > 0);
    if (sent.length > 0) record.untaggedNewsAlerts = sent;
  }

  private async alertSavesOff() {
    const alert: Alert = {
      title: "Lineup saves are off",
      body: 'A game tips within 24 h, but the runner only checks the lineup. Turn saves back on: PUT /saves {"enabled": true}',
      priority: 0,
    };
    const sends = await this.notify(alert, { key: "savesOffAlerts", fingerprint: "savesOff", repeatAfterMs: SAVES_OFF_WARNING_WINDOW_MS });
    if (Object.keys(sends).length > 0) console.log(JSON.stringify({ event: "savesOffAlert", sends }));
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

  // Urgent alerts go to the phone; the rest become Trello cards, the user's list of things that may not be working
  private async notify(alert: Alert, dedupe: { key: string; fingerprint: string; repeatAfterMs: number }) {
    const urgent = alert.push ?? alert.priority > 0;
    const sends: AlertSends = {};
    let delivered = true;
    for (const channel of urgent ? (["pushover"] as const) : (["trello"] as const)) {
      const { due } = await this.checkAlertDue(`${dedupe.key}:${channel}`, dedupe);
      if (!due) continue;
      const send = channel === "pushover" ? this.sendPushover(alert) : this.postToTrello(alert);
      let { accepted, ...sendRecord } = await send.catch(failedSend);
      sends[channel] = sendRecord;
      if (channel === "pushover" && !accepted) {
        const { accepted: ntfyAccepted, ...ntfySend } = await this.sendNtfy(alert);
        sends.ntfy = ntfySend;
        accepted = ntfyAccepted;
      }
      if (!accepted) {
        this.alertUndelivered = true;
        delivered = false;
        continue;
      }
      await this.rememberAlert(`${dedupe.key}:${channel}`, dedupe.fingerprint);
    }
    // Logged on the channels' schedule whether or not they accepted it, so a watchdog can deliver what they didn't
    if ((await this.checkAlertDue(`${dedupe.key}:log`, dedupe)).due) {
      this.ctx.storage.sql.exec("INSERT INTO alerts (alert) VALUES (?)", JSON.stringify({ at: new Date().toISOString(), ...alert, push: urgent, delivered }));
      this.ctx.storage.sql.exec("DELETE FROM alerts WHERE id <= (SELECT MAX(id) FROM alerts) - ?", LISTED_ALERTS);
      await this.rememberAlert(`${dedupe.key}:log`, dedupe.fingerprint);
    }
    return sends;
  }

  private async checkAlertDue(sentAlertsKey: string, { fingerprint, repeatAfterMs }: { fingerprint: string; repeatAfterMs: number }) {
    const lastAlert = (await this.ctx.storage.get<SentAlerts>(sentAlertsKey))?.[fingerprint];
    return { due: !lastAlert || Date.now() - lastAlert.at >= repeatAfterMs };
  }

  private async rememberAlert(sentAlertsKey: string, fingerprint: string) {
    const sentAlerts = (await this.ctx.storage.get<SentAlerts>(sentAlertsKey)) ?? {};
    const recentAlerts = Object.entries(sentAlerts).filter(([, { at }]) => Date.now() - at < FORGET_ALERT_AFTER_MS);
    await this.ctx.storage.put(sentAlertsKey, { ...Object.fromEntries(recentAlerts), [fingerprint]: { at: Date.now() } });
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

  private async sendNtfy({ title, body, priority }: Alert): Promise<AlertOutcome> {
    if (!this.env.NTFY_TOPIC) return { accepted: false, error: "NTFY_TOPIC not set" };
    const message = `${body}\n\n(Sent via ntfy: Pushover didn't accept it)`;
    const publish = JSON.stringify({ topic: this.env.NTFY_TOPIC, title, message, priority: NTFY_PRIORITIES[priority], click: this.env.LINEUP_URL });
    let outcome: AlertOutcome = { accepted: false, error: "not sent" };
    for (let attempt = 0; attempt < NTFY_ATTEMPTS && !outcome.accepted; attempt++) {
      outcome = await fetchWithTimeout(NTFY_URL, { method: "POST", body: publish })
        .then((response) => summarizeAlertResponse(response, response.ok))
        .catch(failedSend);
    }
    return outcome;
  }

  private async postToTrello({ title, body }: Alert): Promise<AlertOutcome> {
    if (!this.env.TRELLO_API_KEY || !this.env.TRELLO_TOKEN || !this.env.TRELLO_LIST) return { accepted: false, error: "TRELLO_API_KEY, TRELLO_TOKEN or TRELLO_LIST not set" };
    const headers = { Authorization: `OAuth oauth_consumer_key="${this.env.TRELLO_API_KEY}", oauth_token="${this.env.TRELLO_TOKEN}"`, "Content-Type": "application/json" };
    const desc = `${body}\n\n${this.env.LINEUP_URL}`;
    let lookupError: string | undefined;
    const openCard = await this.findOpenTrelloCard(title, headers).catch((error) => {
      lookupError = String(error);
      return undefined;
    });
    if (openCard) {
      if ([body, desc].includes(openCard.latestText)) return { accepted: true, openCard: openCard.id, unchanged: true };
      const response = await fetchWithTimeout(`${TRELLO_API_URL}/cards/${openCard.id}/actions/comments`, { method: "POST", headers, body: JSON.stringify({ text: body }) });
      return { ...(await summarizeAlertResponse(response, response.ok)), openCard: openCard.id };
    }
    const response = await fetchWithTimeout(`${TRELLO_API_URL}/cards`, {
      method: "POST",
      headers,
      body: JSON.stringify({ idList: this.env.TRELLO_LIST, name: title, desc }),
    });
    return { ...(await summarizeAlertResponse(response, response.ok)), ...(lookupError && { lookupError }) };
  }

  // The whole board, since the user moves cards out of the Inbox; archiving a card closes it
  private async findOpenTrelloCard(name: string, headers: Record<string, string>) {
    const { idBoard } = await getFromTrello<{ idBoard: string }>(`/lists/${this.env.TRELLO_LIST}?fields=idBoard`, headers);
    const openCards = await getFromTrello<{ id: string; name: string; desc: string }[]>(`/boards/${idBoard}/cards/open?fields=name,desc`, headers);
    const openCard = openCards.find((card) => card.name === name);
    if (!openCard) return undefined;
    const [lastComment] = await getFromTrello<{ data: { text: string } }[]>(`/cards/${openCard.id}/actions?filter=commentCard&limit=1`, headers);
    return { id: openCard.id, latestText: lastComment?.data.text ?? openCard.desc };
  }

  private async checkDays(record: RunRecord, days?: number[]) {
    days ??= [findCurrentDay((await this.fetchRoster()).eligibleLineupPeriods, Date.now())];
    const checkedRosters = new Map<DayCheck, InjuryRoster>();
    for (const day of days) {
      const dayCheck: DayCheck = { day };
      record.days.push(dayCheck);
      const fetched: FetchedDay = {};
      const roster = await this.checkDay(record, dayCheck, fetched).catch((error) => {
        dayCheck.error = String(error);
        return undefined;
      });
      if (roster) checkedRosters.set(dayCheck, roster);
      await this.captureUnexpectedDay(record, dayCheck, fetched).catch((error) => console.error(JSON.stringify({ event: "captureFailed", day, error: String(error) })));
    }
    await this.alertUntaggedNews(record).catch((error) => (record.warnings = [...(record.warnings ?? []), `Untagged-news alerts failed: ${error}`]));
    // After every save, so a slow or failing ESPN never delays one or fails the run
    if (checkedRosters.size === 0) return;
    await this.crossCheckInjuries(record, checkedRosters).catch((error) => (record.warnings = [...(record.warnings ?? []), `Injury cross-check with ESPN failed: ${error}`]));
  }

  private async crossCheckInjuries(record: RunRecord, checkedRosters: Map<DayCheck, InjuryRoster>) {
    const espn = await fetchEspnInjuries();
    if ("error" in espn) {
      record.warnings = [espn.error];
      return;
    }
    const disagreements = new Map<string, InjuryDisagreement>();
    for (const [dayCheck, roster] of checkedRosters) {
      const starters = new Set(dayCheck.decision?.ok ? dayCheck.decision.starters.map(({ player }) => player) : []);
      const comparison = compareInjuryFeeds(roster, espn.injuries, starters);
      if (comparison.comparisons.length > 0) dayCheck.injuries = comparison.comparisons;
      for (const disagreement of comparison.disagreements) disagreements.set(disagreement.message, disagreement);
    }
    if (!(await this.playerAlertsOn())) return;
    const injuryAlerts = await this.alertInjuryDisagreements([...disagreements.values()]);
    if (injuryAlerts.length > 0) record.injuryAlerts = injuryAlerts;
  }

  // Player news can't cost a game outside the fantasy season, so only process failures and warnings alert then; the window comes from Fleaflicker's lineup periods, so it rolls to each new season on its own
  private async playerAlertsOn() {
    const periods = (await this.ctx.storage.get<LineupPeriod[]>(LINEUP_PERIODS_KEY)) ?? [];
    if (periods.length === 0) return true;
    const now = Date.now();
    return now >= Number(periods[0].low.startEpochMilli) - PLAYER_ALERTS_LEAD_MS && now - Number(periods.at(-1)!.low.startEpochMilli) <= DAY_MS;
  }

  // Evidence to fix parsing from the real page later: in-game markup, for one, is gone by the next day
  private async captureUnexpectedDay(record: RunRecord, dayCheck: DayCheck, fetched: FetchedDay) {
    const problems = listDayProblems(dayCheck);
    const hasLockedRows = dayCheck.decision?.ok && dayCheck.decision.starters.some(({ locked }) => locked);
    const firstLockedRows = hasLockedRows && (await this.ctx.storage.get<number>(LOCKED_ROWS_CAPTURED_DAY_KEY)) !== dayCheck.day;
    if (problems.length === 0 && !firstLockedRows) return;
    if (firstLockedRows) await this.ctx.storage.put(LOCKED_ROWS_CAPTURED_DAY_KEY, dayCheck.day);
    const capture = { at: record.startedAt, day: dayCheck.day, reason: problems.length > 0 ? "problems" : "first locked rows", problems, ...fetched };
    this.ctx.storage.sql.exec("INSERT INTO captures (capture) VALUES (?)", JSON.stringify(capture));
    this.ctx.storage.sql.exec("DELETE FROM captures WHERE id <= (SELECT MAX(id) FROM captures) - ?", KEPT_CAPTURES);
  }

  recentCaptures() {
    return this.ctx.storage.sql
      .exec<{ id: number; capture: string }>("SELECT id, capture FROM captures ORDER BY id DESC")
      .toArray()
      .map(({ id, capture }) => ({ id, ...JSON.parse(capture) }));
  }

  private async checkDay(record: RunRecord, dayCheck: DayCheck, fetched: FetchedDay) {
    const { day } = dayCheck;
    let lineupPage = await this.fetchLineupPage(day);
    if (!lineupPage.loggedIn && !record.login) {
      const loginAttempt = await this.logInUnlessBackingOff(day);
      record.login = loginAttempt.login;
      lineupPage = loginAttempt.lineupPage ?? lineupPage;
    }
    const { html, ...pageSummary } = lineupPage;
    dayCheck.lineupPage = pageSummary;
    fetched.html = html;
    const roster = await this.fetchRoster(day);
    fetched.roster = roster;
    let lineupHtml = html;
    let benchOnNews: UntaggedOutNewsCheck[] = [];
    if (pageSummary.status === 200) {
      const tips = parseGameTips(html);
      await this.storeTipTable({ day, fetchedAt: record.startedAt, tips });
      const act = (await this.ctx.storage.get<boolean>(UNTAGGED_OUT_NEWS_ACT_KEY)) === true;
      // The strict match judges freshness against the tip itself, so it reads news the loose 36 h status skips
      const untaggedOutNews = findUntaggedNews(html).flatMap(({ body, ...news }): UntaggedOutNewsCheck[] => {
        const tipAt = tips.find(({ players }) => players.includes(news.player))?.at;
        const matched = tipAt ? matchOutNews({ ...news, body }, tipAt) : undefined;
        if (!tipAt || !matched) return news.status ? [news] : [];
        if (matched.status !== "OUT") return [{ ...news, tipAt, matched }];
        return [{ ...news, tipAt, matched, wouldBench: true }];
      });
      if (untaggedOutNews.length > 0) dayCheck.untaggedOutNews = untaggedOutNews;
      if (act) benchOnNews = untaggedOutNews.filter(({ wouldBench }) => wouldBench);
      lineupHtml = tagOut(html, benchOnNews.map(({ player }) => player));
      const players = roster.groups.flatMap(({ slots }) => slots.map(({ leaguePlayer }) => leaguePlayer?.requestedGames ?? []));
      const playersWithGamesAhead = players.filter((games) => games.some(({ game }) => Number(game.startTimeEpochMilli) > Date.now())).length;
      if (tips.length === 0 && playersWithGamesAhead > 0) {
        dayCheck.warnings = [`No tip times on the day ${day} page though ${playersWithGamesAhead} players have games ahead, so no pre-tip runs or missed-tip alerts that day`];
      }
    }
    dayCheck.decision = await decideLineup(lineupHtml, roster);
    // Tagged OUT, he still starts when no one with a game can replace him
    const starters = dayCheck.decision.ok ? dayCheck.decision.starters.map(({ player }) => player) : [];
    for (const news of benchOnNews) {
      if (!dayCheck.decision.ok || starters.includes(news.player)) continue;
      delete news.wouldBench;
      news.benched = true;
    }
    if (dayCheck.decision.ok && (await this.ctx.storage.get<boolean>(SAVES_ENABLED_KEY))) dayCheck.save = await this.saveUnlessBackingOff(day, dayCheck.decision);
    return roster;
  }

  private async saveUnlessBackingOff(day: number, decision: Extract<LineupDecision, { ok: true }>): Promise<DayCheck["save"]> {
    const failedSaveKey = `${FAILED_SAVE_KEY}:${day}`;
    const failedSave = await this.ctx.storage.get<{ at: number; body: string; save: SaveResult }>(failedSaveKey);
    const tipTables = (await this.ctx.storage.get<TipTable[]>(TIP_TABLES_KEY)) ?? [];
    const tipAboutToStart = tipTables.find((table) => table.day === day)?.tips.find(({ at }) => isWithin(at, TIP_CUTOFF_MS));
    if (tipAboutToStart) return { posted: false, problems: [], skippedNearTip: tipAboutToStart.at };
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
    const roster = await response.json<ApiRoster & { eligibleLineupPeriods: LineupPeriod[]; groups: { slots: { leaguePlayer?: { requestedGames?: { game: { startTimeEpochMilli: string } }[] } }[] }[] }>();
    await this.ctx.storage.put(LINEUP_PERIODS_KEY, roster.eligibleLineupPeriods);
    return roster;
  }

  private async sessionHeaders(): Promise<Record<string, string>> {
    const sessionCookie = await this.ctx.storage.get<string>(SESSION_COOKIE_KEY);
    return sessionCookie ? { Cookie: sessionCookie } : {};
  }

  async status() {
    const alarm = await this.ctx.storage.getAlarm();
    const tipTables = (await this.ctx.storage.get<TipTable[]>(TIP_TABLES_KEY)) ?? [];
    const upcomingTips = tipTables
      .flatMap(({ day, tips }) => tips.map(({ at }) => ({ day, at })))
      .filter(({ at }) => Date.parse(at) > Date.now())
      .sort((a, b) => a.at.localeCompare(b.at));
    return {
      alarm: alarm ? new Date(alarm).toISOString() : null,
      savesEnabled: (await this.ctx.storage.get<boolean>(SAVES_ENABLED_KEY)) === true,
      untaggedOutNewsAct: (await this.ctx.storage.get<boolean>(UNTAGGED_OUT_NEWS_ACT_KEY)) === true,
      upcomingTips,
    };
  }

  async setUntaggedOutNewsAct(act: boolean) {
    await this.ctx.storage.put(UNTAGGED_OUT_NEWS_ACT_KEY, act);
    return { act };
  }

  async setSaves(enabled: boolean) {
    await this.ctx.storage.put(SAVES_ENABLED_KEY, enabled);
    return { enabled };
  }

  recentAlerts() {
    return this.ctx.storage.sql
      .exec<{ id: number; alert: string }>("SELECT id, alert FROM alerts ORDER BY id DESC LIMIT ?", LISTED_ALERTS)
      .toArray()
      .map(({ id, alert }) => ({ id, ...JSON.parse(alert) }));
  }

  deleteAlert(id: number) {
    this.ctx.storage.sql.exec("DELETE FROM alerts WHERE id = ?", id);
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
    if (request.method === "GET" && pathname === "/captures") return Response.json(await runner.recentCaptures());
    if (request.method === "GET" && pathname === "/alerts") return Response.json(await runner.recentAlerts());
    const alertToDelete = pathname.match(/^\/alerts\/(\d+)$/);
    if (request.method === "DELETE" && alertToDelete) {
      await runner.deleteAlert(Number(alertToDelete[1]));
      return new Response(null, { status: 204 });
    }
    if (request.method === "GET" && pathname === "/status") return Response.json(await runner.status());
    if (request.method === "PUT" && pathname === "/saves") {
      const { enabled } = await request.json<{ enabled?: unknown }>();
      return Response.json(await runner.setSaves(enabled === true));
    }
    if (request.method === "PUT" && pathname === "/untagged-out-news") {
      const { act } = await request.json<{ act?: unknown }>();
      return Response.json(await runner.setUntaggedOutNewsAct(act === true));
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
  warnings?: string[];
  error?: string;
  alert?: AlertSends;
  warningAlert?: AlertSends;
  injuryAlerts?: AlertSends[];
  untaggedNewsAlerts?: AlertSends[];
};

type AlertChannel = (typeof ALERT_CHANNELS)[number];

type SentAlerts = Record<string, { at: number }>;

type AlertSends = Partial<Record<AlertChannel | "ntfy", AlertSend>>;

type LoginOutcome = { status: number; gotSessionCookie: boolean; stillSignedOut?: true; backedOff?: true };

// `push` sends a priority-0 alert to the phone instead of Trello
type Alert = { title: string; body: string; priority: 0 | 1 | 2; push?: boolean };

type AlertSend = ({ status: number; response?: string } | { error: string } | { unchanged: true }) & { openCard?: string; lookupError?: string };

type AlertOutcome = AlertSend & { accepted: boolean };

type DayCheck = { day: number; lineupPage?: { status: number; loggedIn: boolean }; warnings?: string[]; untaggedOutNews?: UntaggedOutNewsCheck[]; injuries?: InjuryComparison[]; decision?: LineupDecision; save?: SaveResult & { backedOff?: true; skippedNearTip?: string }; error?: string };

// `wouldBench`: news rules him out of the day's game, but he may still start (shadow mode, or no one with a game can replace him)
// `benched`: news rules him out, the runner acts on news (PUT /untagged-out-news) and the decision moved him out of the starters
type UntaggedOutNewsCheck = Omit<UntaggedNews, "body"> & { tipAt?: string; matched?: OutNewsMatch; wouldBench?: true; benched?: true };

// Tags each player OUT on the lineup page, as Fleaflicker would, so `decideLineup` benches him
function tagOut(html: string, players: string[]) {
  if (players.length === 0) return html;
  const { document } = parseHTML(html);
  for (const row of Array.from(document.querySelectorAll("tr"))) {
    if (!players.includes(row.querySelector(".player-text")?.textContent ?? "")) continue;
    row.querySelector(".player-name")?.insertAdjacentHTML("beforeend", '<span class="injury">OUT</span>');
    for (const icon of Array.from(row.querySelectorAll(".fa-file-text-o, .fa-file-text"))) icon.remove();
  }
  return document.toString();
}

type FetchedDay = { html?: string; roster?: unknown };

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
  return tipTables.some(({ tips }) => tips.some(({ at }) => isWithin(at, windowMs)));
}

function isWithin(at: string, windowMs: number) {
  const untilMs = Date.parse(at) - Date.now();
  return untilMs >= 0 && untilMs <= windowMs;
}

function failedSend(error: unknown): AlertOutcome {
  return { accepted: false, error: String(error) };
}

async function summarizeAlertResponse(response: Response, accepted: boolean) {
  return accepted ? { accepted, status: response.status } : { accepted, status: response.status, response: (await response.text()).slice(0, 200) };
}

async function getFromTrello<T>(path: string, headers: Record<string, string>) {
  const response = await fetchWithTimeout(`${TRELLO_API_URL}${path}`, { headers });
  if (!response.ok) throw new Error(`Trello ${path.split("?")[0]} returned HTTP ${response.status}`);
  return response.json<T>();
}

function hasRunToken(request: Request, runToken: string | undefined) {
  if (!runToken) return false;
  const given = new TextEncoder().encode(request.headers.get("Authorization") ?? "");
  const expected = new TextEncoder().encode(`Bearer ${runToken}`);
  return given.byteLength === expected.byteLength && crypto.subtle.timingSafeEqual(given, expected);
}
