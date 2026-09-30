import { DurableObject } from "cloudflare:workers";

const FLEAFLICKER_LOGIN_URL = "https://www.fleaflicker.com/nba/login";
const SESSION_COOKIE_KEY = "fleaflickerSessionCookie";

export class LineupRunner extends DurableObject<Env> {
  async run(trigger: RunRecord["trigger"] = "manual"): Promise<RunRecord> {
    const startedAt = new Date().toISOString();
    const record: RunRecord = {
      key: `runs/${startedAt}.json`,
      trigger,
      startedAt,
      lineupPage: await this.checkLineupPage(),
    };
    if (!record.lineupPage.loggedIn) {
      record.login = await this.logIn();
      record.lineupPage = await this.checkLineupPage();
    }
    await this.env.RUN_LOG.put(record.key, JSON.stringify(record));
    return record;
  }

  async schedule(at: Date) {
    await this.ctx.storage.setAlarm(at);
  }

  async alarm() {
    await this.run("alarm");
  }

  private async checkLineupPage() {
    const sessionCookie = await this.ctx.storage.get<string>(SESSION_COOKIE_KEY);
    const response = await fetch(this.env.LINEUP_URL, { headers: sessionCookie ? { Cookie: sessionCookie } : {} });
    const html = await response.text();
    const loggedIn = html.includes('href="/logout"') && html.includes('<select name="status');
    return { status: response.status, loggedIn };
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
    if (request.method === "POST" && pathname === "/schedule") {
      const { at } = await request.json<{ at: string }>();
      await runner.schedule(new Date(at));
      return Response.json({ scheduledAt: at });
    }
    return new Response("Not found", { status: 404 });
  },
} satisfies ExportedHandler<Env>;

type RunRecord = {
  key: string;
  trigger: "manual" | "alarm";
  startedAt: string;
  login?: { status: number; gotSessionCookie: boolean };
  lineupPage: { status: number; loggedIn: boolean };
};

function hasRunToken(request: Request, runToken: string) {
  const given = new TextEncoder().encode(request.headers.get("Authorization") ?? "");
  const expected = new TextEncoder().encode(`Bearer ${runToken}`);
  return given.byteLength === expected.byteLength && crypto.subtle.timingSafeEqual(given, expected);
}
