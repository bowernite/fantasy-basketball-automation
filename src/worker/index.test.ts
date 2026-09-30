import { env, exports } from "cloudflare:workers";
import { createExecutionContext, createScheduledController, runDurableObjectAlarm, runInDurableObject, waitOnExecutionContext } from "cloudflare:test";
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
    expect(record.days[0].lineupPage).toEqual({ status: 200, loggedIn: false });

    expect(await listRuns()).toEqual([record]);
  });

  it("logs in to Fleaflicker when the lineup page shows logged out", async () => {
    stubFleaflicker(fakeFleaflicker);

    const response = await triggerRun();

    const record = await response.json<RunRecord>();
    expect(record.login).toEqual({ status: 303, gotSessionCookie: true });
    expect(record.days[0].lineupPage).toEqual({ status: 200, loggedIn: true });
  });

  it("reuses the saved session instead of logging in again", async () => {
    stubFleaflicker(fakeFleaflicker);
    await triggerRun();

    const record = await (await triggerRun()).json<RunRecord>();

    expect(record.login).toBeUndefined();
    expect(record.days[0].lineupPage).toEqual({ status: 200, loggedIn: true });
  });

  it("records a failed login without logging in", async () => {
    stubFleaflicker(async (request) =>
      request.method === "POST" ? new Response("<form>Your password is incorrect</form>") : new Response(LOGGED_OUT_PAGE),
    );

    const record = await (await triggerRun()).json<RunRecord>();

    expect(record.login).toEqual({ status: 200, gotSessionCookie: false });
    expect(record.days[0].lineupPage).toEqual({ status: 200, loggedIn: false });
  });

  it("decides today's lineup on the fantasy stats view without saving it", async () => {
    const lineupSaves: Request[] = [];
    stubFleaflicker((request) => {
      if (request.method === "POST" && new URL(request.url).pathname !== "/nba/login") lineupSaves.push(request);
      const fantasyStatsView = new URL(request.url).searchParams.get("statType") === "0";
      return fakeFleaflicker(request, fantasyStatsView ? fantasyStatsPage : seasonStatsPage);
    });

    const record = await (await triggerRun()).json<RunRecord>();

    expect(record.days[0].lineupPage).toEqual({ status: 200, loggedIn: true });
    expect(record.days[0].decision).toMatchObject({ ok: true, formAction: "/nba/leagues/30579/teams/161025" });
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

    expect(record.days).toMatchObject([{ day: 1, decision: { ok: true } }]);
  });

  it("sets today and tomorrow on the cron schedule", async () => {
    stubFleaflicker(fakeFleaflicker);
    const ctx = createExecutionContext();

    await worker.scheduled(createScheduledController({ cron: "*/5 * * * *" }), env, ctx);
    await waitOnExecutionContext(ctx);

    const [latest] = await listRuns();
    expect(latest).toMatchObject({ trigger: "cron", days: [{ day: 1 }, { day: 2 }] });
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
        "message": "- Fleaflicker login failed (HTTP 503, no session cookie)
      - No lineup form on the page; the session may be logged out",
        "priority": "1",
        "title": "Lineup run (manual) failed",
        "token": "test-pushover-token",
        "url": "https://www.fleaflicker.com/nba/leagues/30579/teams/161025",
        "user": "test-pushover-user",
      }
    `);
  });

  it("files a Trello card for a failed run", async () => {
    const { cards } = stubFleaflicker(() => {
      throw new TypeError("Connection refused");
    });

    const record = await (await triggerRun()).json<RunRecord>();

    expect(cards).toMatchInlineSnapshot(`
      [
        {
          "authorization": "OAuth oauth_consumer_key="test-trello-key", oauth_token="test-trello-token"",
          "desc": "- TypeError: Connection refused

      https://www.fleaflicker.com/nba/leagues/30579/teams/161025",
          "list": "test-trello-list",
          "name": "Lineup run (manual) failed",
        },
      ]
    `);
    expect(record.alert?.trello).toEqual({ status: 200 });
  });

  it("says in the alert when Fleaflicker serves an error page", async () => {
    const { alerts } = stubFleaflicker((request) =>
      request.method === "GET" ? new Response("Service unavailable", { status: 503 }) : fakeFleaflicker(request),
    );

    await triggerRun();

    expect(alerts.at(-1)?.message).toMatchInlineSnapshot(`
      "- Lineup page returned HTTP 503
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

  it("tries the alert again on the next run when Pushover rejects it", async () => {
    const pushoverStatuses = [429, 200];
    const { alerts } = stubFleaflicker(
      () => {
        throw new TypeError("TLS handshake failed");
      },
      { pushoverStatus: () => pushoverStatuses.shift()! },
    );

    const firstRun = await (await triggerRun()).json<RunRecord>();
    const secondRun = await (await triggerRun()).json<RunRecord>();

    expect(alerts).toHaveLength(2);
    expect(firstRun.alert?.pushover).toEqual({ status: 429, response: '{"status":0,"errors":["application is over its message limit"]}' });
    expect(secondRun.alert?.pushover).toEqual({ status: 200 });
  });

  it("retries only the channel that rejected the alert", async () => {
    const trelloStatuses = [401, 200];
    const { alerts, cards } = stubFleaflicker(
      () => {
        throw new TypeError("Handshake timed out");
      },
      { trelloStatus: () => trelloStatuses.shift()! },
    );

    const firstRun = await (await triggerRun()).json<RunRecord>();
    const secondRun = await (await triggerRun()).json<RunRecord>();

    expect(firstRun.alert).toEqual({ pushover: { status: 200 }, trello: { status: 401, response: "invalid token" } });
    expect(secondRun.alert).toEqual({ trello: { status: 200 } });
    expect([alerts.length, cards.length]).toEqual([1, 2]);
  });

  it("still records the run when the alert can't be sent", async () => {
    stubFleaflicker(
      () => {
        throw new TypeError("Socket closed");
      },
      {
        pushoverStatus: () => {
          throw new TypeError("Pushover unreachable");
        },
      },
    );

    const response = await triggerRun();

    expect(response.status).toBe(200);
    const [latest] = await listRuns();
    expect(latest).toMatchObject({ error: "TypeError: Socket closed", alert: { pushover: { error: "TypeError: Pushover unreachable" } } });
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

describe("scheduled checks", () => {
  it("sets today and tomorrow on the first tick", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    stubFleaflicker(fakeFleaflickerSeason);
    const runner = freshRunner();

    await runner.tick("cron");

    expect(await runner.recentRuns()).toMatchObject([
      { trigger: "cron", days: [{ day: 1, decision: { ok: true } }, { day: 2, decision: { ok: true } }] },
    ]);
  });

  it("does nothing on the next tick when today and tomorrow are already set", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    stubFleaflicker(fakeFleaflickerSeason);
    const runner = freshRunner();
    await runner.tick("cron");

    vi.setSystemTime(new Date("2026-10-20T15:15:00Z"));
    await runner.tick("cron");

    expect(await runner.recentRuns()).toHaveLength(1);
  });

  it("sets today again 40 min before a tip", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T18:06:00Z") });
    stubFleaflicker(fakeFleaflickerSeason);
    const runner = freshRunner();
    await runner.tick("cron");
    vi.setSystemTime(new Date("2026-10-20T18:16:00Z"));
    await runner.tick("cron");

    vi.setSystemTime(new Date("2026-10-20T18:21:00Z"));
    await runner.tick("cron");

    const runs = await runner.recentRuns();
    expect(runs.map(({ startedAt, days }) => ({ startedAt, days: days.map(({ day }) => day) }))).toEqual([
      { startedAt: "2026-10-20T18:21:00.000Z", days: [1] },
      { startedAt: "2026-10-20T18:06:00.000Z", days: [1, 2] },
    ]);
  });

  it("runs once when two ticks arrive together", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    stubFleaflicker(async (request) => {
      await new Promise((resolve) => setTimeout(resolve, 10));
      return fakeFleaflickerSeason(request);
    });
    const runner = freshRunner();

    await Promise.all([runner.tick("cron"), runner.tick("alarm")]);

    expect(await runner.recentRuns()).toHaveLength(1);
  });

  it("wakes itself for the next tip target", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T18:06:00Z") });
    stubFleaflicker(fakeFleaflickerSeason);
    const runner = freshRunner();
    await runner.tick("cron");

    expect(await runInDurableObject(runner, (_, state) => state.storage.getAlarm())).toBe(Date.parse("2026-10-20T18:20:00Z"));
    vi.setSystemTime(new Date("2026-10-20T18:20:00Z"));
    expect(await runDurableObjectAlarm(runner)).toBe(true);

    const [latest] = await runner.recentRuns();
    expect(latest).toMatchObject({ trigger: "alarm", startedAt: "2026-10-20T18:20:00.000Z", days: [{ day: 1 }] });
  });

  it("records and alerts a failed run when Fleaflicker's API goes down mid-day", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T18:06:00Z") });
    let apiDown = false;
    const { alerts } = stubFleaflicker(fakeFleaflickerSeason, { rosterApiUp: () => !apiDown });
    const runner = freshRunner();
    await runner.tick("cron");

    apiDown = true;
    vi.setSystemTime(new Date("2026-10-20T18:21:00Z"));
    await runner.tick("cron");

    const [latest] = await runner.recentRuns();
    expect(latest).toMatchObject({ startedAt: "2026-10-20T18:21:00.000Z", error: "Error: Roster API returned HTTP 503" });
    expect(alerts.at(-1)?.message).toContain("Roster API returned HTTP 503");
  });
  it("checks in with the dead-man monitor on every tick, not on manual runs", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    let fleaflickerDown = false;
    const { deadManPings } = stubFleaflicker((request) => {
      if (fleaflickerDown) throw new TypeError("Network unreachable");
      return fakeFleaflickerSeason(request);
    });
    const runner = freshRunner();

    await runner.tick("cron");
    vi.setSystemTime(new Date("2026-10-20T15:15:00Z"));
    await runner.tick("cron");
    fleaflickerDown = true;
    await runner.run();
    vi.setSystemTime(new Date("2026-10-20T16:05:00Z"));
    await runner.tick("cron");

    expect(deadManPings).toEqual(["/test-check", "/test-check", "/test-check/fail"]);
  });
});

type RunRecord = {
  trigger: "manual" | "alarm" | "cron";
  login?: { status: number; gotSessionCookie: boolean };
  days: { day: number; lineupPage: { status: number; loggedIn: boolean }; decision?: { ok: boolean; formAction?: string; errors?: string[] } }[];
  error?: string;
  alert?: Record<"pushover" | "trello", { status: number; response?: string } | { error: string }>;
};

function freshRunner() {
  return env.RUNNER.getByName(crypto.randomUUID());
}

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

// Opening night's page, with its tip times moved to the requested day
function fakeFleaflickerSeason(request: Request) {
  const daysAfterOpeningNight = Number(new URL(request.url).searchParams.get("week") ?? 1) - 1;
  const page = fantasyStatsPage.replaceAll(/datetime="([^"]+)"/g, (_, at: string) => `datetime="${new Date(Date.parse(at) + daysAfterOpeningNight * 24 * 60 * 60 * 1000).toISOString()}"`);
  return fakeFleaflicker(request, page);
}

function stubFleaflicker(respond: (request: Request) => Response | Promise<Response>, { pushoverStatus = () => 200, trelloStatus = () => 200, rosterApiUp = () => true } = {}) {
  const deadManPings: string[] = [];
  const alerts: Record<string, string>[] = [];
  const cards: { list: string; name: string; desc: string; authorization: string | null }[] = [];
  const realFetch = globalThis.fetch;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const request = new Request(input, init);
    const { hostname, pathname } = new URL(request.url);
    if (hostname === "www.fleaflicker.com" && pathname === "/api/FetchRoster") {
      return rosterApiUp() ? Response.json(openingNightRoster) : new Response("Service unavailable", { status: 503 });
    }
    if (hostname === "www.fleaflicker.com") return respond(request);
    if (hostname === "api.pushover.net") {
      alerts.push(Object.fromEntries(new URLSearchParams(await request.text())));
      const status = pushoverStatus();
      return status === 200 ? Response.json({ status: 1, request: "r1" }) : Response.json({ status: 0, errors: ["application is over its message limit"] }, { status });
    }
    if (hostname === "api.trello.com" && pathname === "/1/cards") {
      const { idList, name, desc } = await request.json<{ idList: string; name: string; desc: string }>();
      cards.push({ list: idList, name, desc, authorization: request.headers.get("Authorization") });
      const status = trelloStatus();
      return status === 200 ? Response.json({ id: `card-${cards.length}` }) : new Response("invalid token", { status });
    }
    if (hostname === "hc-ping.com") {
      deadManPings.push(pathname);
      return new Response("OK");
    }
    return realFetch(input, init);
  });
  return { alerts, cards, deadManPings };
}
