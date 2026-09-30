import { DurableObject } from "cloudflare:workers";
import { decideLineup, type LineupDecision } from "./decide-lineup";

const FLEAFLICKER_LOGIN_URL = "https://www.fleaflicker.com/nba/login";
const SESSION_COOKIE_KEY = "fleaflickerSessionCookie";

export class LineupRunner extends DurableObject<Env> {
  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    ctx.storage.sql.exec("CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, record TEXT NOT NULL)");
  }

  async run(trigger: RunRecord["trigger"] = "manual"): Promise<RunRecord> {
    const startedAt = new Date().toISOString();
    let lineupPage = await this.fetchLineupPage();
    let login: RunRecord["login"];
    if (!lineupPage.loggedIn) {
      login = await this.logIn();
      lineupPage = await this.fetchLineupPage();
    }
    const { html, ...pageSummary } = lineupPage;
    const record: RunRecord = { trigger, startedAt, login, lineupPage: pageSummary, decision: await decideLineup(html) };
    this.ctx.storage.sql.exec("INSERT INTO runs (record) VALUES (?)", JSON.stringify(record));
    return record;
  }

  recentRuns(limit = 20): RunRecord[] {
    return this.ctx.storage.sql
      .exec<{ record: string }>("SELECT record FROM runs ORDER BY id DESC LIMIT ?", limit)
      .toArray()
      .map((row) => JSON.parse(row.record));
  }

  async schedule(at: Date) {
    await this.ctx.storage.setAlarm(at);
  }

  async alarm() {
    await this.run("alarm");
  }

  private async fetchLineupPage() {
    const sessionCookie = await this.ctx.storage.get<string>(SESSION_COOKIE_KEY);
    const fantasyStatsView = `${this.env.LINEUP_URL}?statType=0`;
    const response = await fetch(fantasyStatsView, { headers: sessionCookie ? { Cookie: sessionCookie } : {} });
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
    if (request.method === "POST" && pathname === "/schedule") {
      const { at } = await request.json<{ at: string }>();
      await runner.schedule(new Date(at));
      return Response.json({ scheduledAt: at });
    }
    return new Response("Not found", { status: 404 });
  },

  async scheduled(_controller, env, ctx) {
    ctx.waitUntil(env.RUNNER.getByName("primary").run("cron"));
  },
} satisfies ExportedHandler<Env>;

type RunRecord = {
  trigger: "manual" | "alarm" | "cron";
  startedAt: string;
  login?: { status: number; gotSessionCookie: boolean };
  lineupPage: { status: number; loggedIn: boolean };
  decision: LineupDecision;
};

function hasRunToken(request: Request, runToken: string) {
  const given = new TextEncoder().encode(request.headers.get("Authorization") ?? "");
  const expected = new TextEncoder().encode(`Bearer ${runToken}`);
  return given.byteLength === expected.byteLength && crypto.subtle.timingSafeEqual(given, expected);
}
