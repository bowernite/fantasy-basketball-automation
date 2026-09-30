import { env, exports } from "cloudflare:workers";
import { createExecutionContext, createScheduledController, runDurableObjectAlarm, waitOnExecutionContext } from "cloudflare:test";
import { afterEach, describe, expect, it, vi } from "vitest";
import fantasyStatsPage from "../lineup/fixtures/teampage-logged-in-fantasy-stats.html?raw";
import seasonStatsPage from "../lineup/fixtures/teampage-logged-in.html?raw";
import worker from "./index";

const LOGGED_OUT_PAGE = `<html><body><a class="btn" href="/nba/login">Log In</a></body></html>`;
const LOGGED_IN_PAGE = `<html><body><a href="/logout">Sign Out</a><select name="status123"></select></body></html>`;

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("lineup runner", () => {
  it("checks the lineup page and stores a run record when triggered", async () => {
    stubFleaflicker(() => new Response(LOGGED_OUT_PAGE));

    const response = await exports.default.fetch("https://runner.test/run", {
      method: "POST",
      headers: { Authorization: "Bearer test-run-token" },
    });

    expect(response.status).toBe(200);
    const record = await response.json<RunRecord>();
    expect(record.lineupPage).toEqual({ status: 200, loggedIn: false });

    expect(await listRuns()).toEqual([record]);
  });

  it("logs in to Fleaflicker when the lineup page shows logged out", async () => {
    stubFleaflicker(fakeFleaflicker);

    const response = await triggerRun();

    const record = await response.json<RunRecord>();
    expect(record.login).toEqual({ status: 303, gotSessionCookie: true });
    expect(record.lineupPage).toEqual({ status: 200, loggedIn: true });
  });

  it("reuses the saved session instead of logging in again", async () => {
    stubFleaflicker(fakeFleaflicker);
    await triggerRun();

    const record = await (await triggerRun()).json<RunRecord>();

    expect(record.login).toBeUndefined();
    expect(record.lineupPage).toEqual({ status: 200, loggedIn: true });
  });

  it("records a failed login without logging in", async () => {
    stubFleaflicker(async (request) =>
      request.method === "POST" ? new Response("<form>Your password is incorrect</form>") : new Response(LOGGED_OUT_PAGE),
    );

    const record = await (await triggerRun()).json<RunRecord>();

    expect(record.login).toEqual({ status: 200, gotSessionCookie: false });
    expect(record.lineupPage).toEqual({ status: 200, loggedIn: false });
  });

  it("runs at a scheduled time", async () => {
    stubFleaflicker(fakeFleaflicker);
    const at = new Date(Date.now() + 60_000).toISOString();

    const response = await exports.default.fetch("https://runner.test/schedule", {
      method: "POST",
      headers: { Authorization: "Bearer test-run-token" },
      body: JSON.stringify({ at }),
    });
    expect(await response.json()).toEqual({ scheduledAt: at });

    expect(await runDurableObjectAlarm(env.RUNNER.getByName("primary"))).toBe(true);
    expect((await listRuns()).filter((record) => record.trigger === "alarm")).toEqual([
      expect.objectContaining({ lineupPage: { status: 200, loggedIn: true } }),
    ]);
  });

  it("decides today's lineup on the fantasy stats view without saving it", async () => {
    const lineupSaves: Request[] = [];
    stubFleaflicker((request) => {
      if (request.method === "POST" && new URL(request.url).pathname !== "/nba/login") lineupSaves.push(request);
      const fantasyStatsView = new URL(request.url).searchParams.get("statType") === "0";
      return fakeFleaflicker(request, fantasyStatsView ? fantasyStatsPage : seasonStatsPage);
    });

    const record = await (await triggerRun()).json<RunRecord>();

    expect(record.lineupPage).toEqual({ status: 200, loggedIn: true });
    expect(record.decision).toMatchObject({ ok: true, formAction: "/nba/leagues/30579/teams/161025" });
    expect(lineupSaves).toEqual([]);
  });

  it("runs on the cron schedule", async () => {
    stubFleaflicker(fakeFleaflicker);
    const ctx = createExecutionContext();

    await worker.scheduled(createScheduledController({ cron: "0 * * * *" }), env, ctx);
    await waitOnExecutionContext(ctx);

    const [latest] = await listRuns();
    expect(latest).toMatchObject({ trigger: "cron", lineupPage: { status: 200, loggedIn: true } });
  });

  it("lists recent run records, newest first", async () => {
    stubFleaflicker(fakeFleaflicker);
    const first = await (await triggerRun()).json<RunRecord>();
    const second = await (await triggerRun()).json<RunRecord>();

    const records = await listRuns();

    expect(records.slice(0, 2)).toEqual([second, first]);
  });

  it("records a run that throws", async () => {
    stubFleaflicker(() => {
      throw new TypeError("Network connection lost");
    });

    const record = await (await triggerRun()).json<RunRecord>();

    expect(record).toMatchObject({ trigger: "manual", error: "TypeError: Network connection lost" });
    const [latest] = await listRuns();
    expect(latest).toEqual(record);
  });

  it("alerts the owner when a run can't decide the lineup", async () => {
    const { alerts } = stubFleaflicker(async (request) =>
      request.method === "POST" ? new Response("Service unavailable", { status: 503 }) : new Response(LOGGED_OUT_PAGE),
    );

    await triggerRun();

    expect(alerts).toHaveLength(1);
    expect(alerts[0]).toMatchInlineSnapshot(`
      {
        "click": "https://www.fleaflicker.com/nba/leagues/30579/teams/161025",
        "message": "Lineup run (manual) failed:
      - Fleaflicker login failed (HTTP 503, no session cookie)
      - No lineup form on the page; the session may be logged out",
        "title": "Lineup runner",
        "topic": "/test-alerts",
      }
    `);
  });

  it("alerts once while the same failure repeats", async () => {
    const { alerts } = stubFleaflicker(() => {
      throw new TypeError("DNS lookup failed");
    });

    await triggerRun();
    await triggerRun();

    expect(alerts).toHaveLength(1);
  });

  it("alerts again when the same failure is still happening hours later", async () => {
    const { alerts } = stubFleaflicker(() => {
      throw new TypeError("Connection reset");
    });
    vi.useFakeTimers({ toFake: ["Date"] });

    await triggerRun();
    vi.setSystemTime(Date.now() + 3 * 60 * 60 * 1000);
    await triggerRun();

    expect(alerts).toHaveLength(2);
  });

  it("checks in with the dead-man monitor after each run", async () => {
    const { deadManPings } = stubFleaflicker((request) => {
      const fantasyStatsView = new URL(request.url).searchParams.get("statType") === "0";
      return fakeFleaflicker(request, fantasyStatsView ? fantasyStatsPage : seasonStatsPage);
    });
    await triggerRun();

    stubFleaflicker(() => {
      throw new TypeError("Network unreachable");
    });
    await triggerRun();

    expect(deadManPings).toEqual(["/test-check", "/test-check/fail"]);
  });

  it("refuses to run without the run token", async () => {
    stubFleaflicker(() => new Response(LOGGED_OUT_PAGE));
    const recordsBefore = await listRuns();

    const response = await exports.default.fetch("https://runner.test/run", {
      method: "POST",
      headers: { Authorization: "Bearer wrong-token" },
    });

    expect(response.status).toBe(401);
    expect(await listRuns()).toEqual(recordsBefore);
  });
});

type RunRecord = {
  trigger: "manual" | "alarm" | "cron";
  login?: { status: number; gotSessionCookie: boolean };
  lineupPage: { status: number; loggedIn: boolean };
  decision?: { ok: boolean; formAction?: string; errors?: string[] };
  error?: string;
};

async function listRuns() {
  const response = await exports.default.fetch("https://runner.test/runs", {
    headers: { Authorization: "Bearer test-run-token" },
  });
  return response.json<RunRecord[]>();
}

function triggerRun() {
  return exports.default.fetch("https://runner.test/run", {
    method: "POST",
    headers: { Authorization: "Bearer test-run-token" },
  });
}

async function fakeFleaflicker(request: Request, loggedInPage = LOGGED_IN_PAGE) {
  const { pathname } = new URL(request.url);
  if (request.method === "POST" && pathname === "/nba/login") {
    const form = await request.formData();
    const validLogin = form.get("email") === "owner@example.com" && form.get("password") === "test-password";
    if (!validLogin) return new Response("<form>Your password is incorrect</form>");
    return new Response(null, {
      status: 303,
      headers: { Location: "/nba", "Set-Cookie": "cookieId=session-1; Max-Age=43200000; Path=/; Secure" },
    });
  }
  const hasSession = request.headers.get("Cookie")?.includes("cookieId=session-1");
  return new Response(hasSession ? loggedInPage : LOGGED_OUT_PAGE);
}

function stubFleaflicker(respond: (request: Request) => Response | Promise<Response>) {
  const deadManPings: string[] = [];
  const alerts: { topic: string; title: string | null; click: string | null; message: string }[] = [];
  const realFetch = globalThis.fetch;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const request = new Request(input, init);
    const { hostname, pathname } = new URL(request.url);
    if (hostname === "www.fleaflicker.com") return respond(request);
    if (hostname === "ntfy.sh") {
      const { headers } = request;
      alerts.push({ topic: pathname, title: headers.get("Title"), click: headers.get("Click"), message: await request.text() });
      return new Response("{}");
    }
    if (hostname === "hc-ping.com") {
      deadManPings.push(pathname);
      return new Response("OK");
    }
    return realFetch(input, init);
  });
  return { alerts, deadManPings };
}
