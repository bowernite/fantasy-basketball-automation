import { env, exports } from "cloudflare:workers";
import { createExecutionContext, createScheduledController, runDurableObjectAlarm, waitOnExecutionContext } from "cloudflare:test";
import { afterEach, describe, expect, it, vi } from "vitest";
import openingNightRoster from "../lineup/fixtures/fetch-roster-week1-signed-in.json";
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

  it("sets the league's current day, which runs until 6a ET the next morning", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-21T03:00:00Z") });
    stubFleaflicker((request) => {
      const { searchParams } = new URL(request.url);
      const openingNightView = searchParams.get("statType") === "0" && searchParams.get("week") === "1";
      return fakeFleaflicker(request, openingNightView ? fantasyStatsPage : seasonStatsPage);
    });

    const record = await (await triggerRun()).json<RunRecord>();

    expect(record).toMatchObject({ day: 1, decision: { ok: true } });
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

  it("says in the alert when Fleaflicker serves an error page", async () => {
    const { alerts } = stubFleaflicker((request) =>
      request.method === "GET" ? new Response("Service unavailable", { status: 503 }) : fakeFleaflicker(request),
    );

    await triggerRun();

    expect(alerts.at(-1)?.message).toMatchInlineSnapshot(`
      "Lineup run (manual) failed:
      - Lineup page returned HTTP 503
      - No lineup form on the page; the session may be logged out"
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

  it("tries the alert again on the next run when ntfy rejects it", async () => {
    const ntfyStatuses = [429, 200];
    const { alerts } = stubFleaflicker(
      () => {
        throw new TypeError("TLS handshake failed");
      },
      { ntfyStatus: () => ntfyStatuses.shift()! },
    );

    const firstRun = await (await triggerRun()).json<RunRecord>();
    const secondRun = await (await triggerRun()).json<RunRecord>();

    expect(alerts).toHaveLength(2);
    expect(firstRun.alert).toEqual({ status: 429, response: '{"code":42908,"error":"limit reached: daily message quota reached"}' });
    expect(secondRun.alert).toEqual({ status: 200 });
  });

  it("still records the run when the alert can't be sent", async () => {
    stubFleaflicker(
      () => {
        throw new TypeError("Socket closed");
      },
      {
        ntfyStatus: () => {
          throw new TypeError("ntfy.sh unreachable");
        },
      },
    );

    const response = await triggerRun();

    expect(response.status).toBe(200);
    const [latest] = await listRuns();
    expect(latest).toMatchObject({ error: "TypeError: Socket closed", alert: { error: "TypeError: ntfy.sh unreachable" } });
  });

  it("checks in with the dead-man monitor after each run", async () => {
    let fleaflickerDown = false;
    const { deadManPings } = stubFleaflicker((request) => {
      if (fleaflickerDown) throw new TypeError("Network unreachable");
      const fantasyStatsView = new URL(request.url).searchParams.get("statType") === "0";
      return fakeFleaflicker(request, fantasyStatsView ? fantasyStatsPage : seasonStatsPage);
    });

    await triggerRun();
    fleaflickerDown = true;
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
  day?: number;
  login?: { status: number; gotSessionCookie: boolean };
  lineupPage: { status: number; loggedIn: boolean };
  decision?: { ok: boolean; formAction?: string; errors?: string[] };
  error?: string;
  alert?: { status: number; response?: string } | { error: string };
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

function stubFleaflicker(respond: (request: Request) => Response | Promise<Response>, { ntfyStatus = () => 200 } = {}) {
  const deadManPings: string[] = [];
  const alerts: { topic: string; title: string | null; click: string | null; message: string }[] = [];
  const realFetch = globalThis.fetch;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const request = new Request(input, init);
    const { hostname, pathname } = new URL(request.url);
    if (hostname === "www.fleaflicker.com") return pathname === "/api/FetchRoster" ? Response.json(openingNightRoster) : respond(request);
    if (hostname === "ntfy.sh") {
      const { headers } = request;
      alerts.push({ topic: pathname, title: headers.get("Title"), click: headers.get("Click"), message: await request.text() });
      const status = ntfyStatus();
      return new Response(status === 429 ? '{"code":42908,"error":"limit reached: daily message quota reached"}' : "{}", { status });
    }
    if (hostname === "hc-ping.com") {
      deadManPings.push(pathname);
      return new Response("OK");
    }
    return realFetch(input, init);
  });
  return { alerts, deadManPings };
}
