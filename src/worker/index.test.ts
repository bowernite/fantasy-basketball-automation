import { env, exports } from "cloudflare:workers";
import { createExecutionContext, createScheduledController, runDurableObjectAlarm, runInDurableObject, waitOnExecutionContext } from "cloudflare:test";
import { parseHTML } from "linkedom";
import { afterEach, describe, expect, it, vi } from "vitest";
import openingNightRoster from "../lineup/fixtures/fetch-roster-week1-signed-in.json";
import fantasyStatsPage from "../lineup/fixtures/teampage-logged-in-fantasy-stats.html?raw";
import seasonStatsPage from "../lineup/fixtures/teampage-logged-in.html?raw";
import signedOutPage from "../lineup/fixtures/teampage.html?raw";
import worker from "./index";

const LOGGED_OUT_PAGE = `<html><body><a class="btn" href="/nba/login">Log In</a></body></html>`;
const LOGGED_IN_PAGE = `<html><body><a href="/logout">Sign Out</a><select name="status123"></select></body></html>`;
// Captured from a real accepted save; its `_gAlert` decodes to "Lineup set successfully."
const ACCEPTED_SAVE_LOCATION =
  "https://www.fleaflicker.com/nba/leagues/30579/teams/161025?_fm=eJxjYGBc8IX3_mFGAAzsA0Y&week=1&_gAlert=eJxjYGBc8IX3_uE1bxlYyxUYGMFQwiczL7W0QKE4tUShuDQ5ObW4OK00J6dSDwBMBA7h";

// `primary` lives for the whole file; clear its session, dedupe and backoff state (run rows stay)
afterEach(async () => {
  vi.restoreAllMocks();
  vi.useRealTimers();
  await runInDurableObject(env.RUNNER.getByName("primary"), async (_, state) => {
    await state.storage.delete([...(await state.storage.list()).keys()]);
    await state.storage.deleteAlarm();
  });
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

  it("saves the decided lineup once saves are turned on", async () => {
    const { lineupSaves } = stubLineupSaves();

    expect(await (await setSaves(true)).json()).toEqual({ enabled: true });
    const record = await (await triggerRun()).json<RunRecord>();

    expect(lineupSaves).toHaveLength(1);
    expect(record.days[0].save).toEqual({ posted: true, problems: [] });
  });

  it("alerts the owner when the reloaded page doesn't show the saved lineup", async () => {
    const { alerts } = stubLineupSaves({ applySaves: false });

    await setSaves(true);
    await triggerRun();

    expect(alerts.at(-1)?.message).toMatchInlineSnapshot(`
      "- After saving, Fleaflicker shows Naz Reid in C, not Bench
      - After saving, Fleaflicker shows John Collins in F/C, not C
      - After saving, Fleaflicker shows Neemias Queta in ANY, not F/C
      - After saving, Fleaflicker shows Josh Giddey in Bench, not ANY"
    `);
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

    expect(record).toMatchObject({ trigger: "manual", days: [{ error: "TypeError: Network connection lost" }] });
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

  it("alerts once per failure while two failures take turns", async () => {
    let failure = "";
    const { alerts } = stubFleaflicker(() => {
      throw new TypeError(failure);
    });

    for (failure of ["DNS lookup failed", "Connection refused", "DNS lookup failed", "Connection refused"]) await triggerRun();

    expect(alerts.map(({ message }) => message)).toEqual(["- TypeError: DNS lookup failed", "- TypeError: Connection refused"]);
  });

  it("alerts again when a failure comes back after a successful run", async () => {
    let fleaflickerDown = true;
    const { alerts } = stubFleaflicker((request) => {
      if (fleaflickerDown) throw new TypeError("Connection dropped");
      return fakeFleaflicker(request, fantasyStatsPage);
    });

    await triggerRun();
    fleaflickerDown = false;
    await triggerRun();
    fleaflickerDown = true;
    await triggerRun();

    expect(alerts.map(({ message }) => message)).toEqual(["- TypeError: Connection dropped", "- TypeError: Connection dropped"]);
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

  it("comments on the open Trello card when the same failure is still happening hours later", async () => {
    const { cards, cardComments } = stubFleaflicker(() => {
      throw new TypeError("Connection timed out");
    });
    vi.useFakeTimers({ toFake: ["Date"] });

    await triggerRun();
    vi.setSystemTime(Date.now() + 3 * 60 * 60 * 1000);
    await triggerRun();

    expect(cards).toHaveLength(1);
    expect(cardComments).toEqual([{ card: "card-1", text: "Still failing:\n- TypeError: Connection timed out" }]);
  });

  it("files a new Trello card for a repeat failure once the old card is archived", async () => {
    let cardArchived = false;
    const { cards, cardComments } = stubFleaflicker(
      () => {
        throw new TypeError("Connection aborted");
      },
      { trelloCardArchived: () => cardArchived },
    );
    vi.useFakeTimers({ toFake: ["Date"] });

    await triggerRun();
    cardArchived = true;
    vi.setSystemTime(Date.now() + 3 * 60 * 60 * 1000);
    await triggerRun();

    expect(cards).toHaveLength(2);
    expect(cardComments).toEqual([]);
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
    expect(latest).toMatchObject({ days: [{ error: "TypeError: Socket closed" }], alert: { pushover: { error: "TypeError: Pushover unreachable" } } });
  });

  it("starts the schedule on a manual run when nothing is scheduled", async () => {
    stubFleaflicker(fakeFleaflicker);
    const runner = env.RUNNER.getByName("primary");
    await runInDurableObject(runner, (_, state) => state.storage.deleteAlarm());

    await triggerRun();

    expect(await runDurableObjectAlarm(runner)).toBe(true);
    const [latest] = await listRuns();
    expect(latest).toMatchObject({ trigger: "alarm" });
  });

  it("turns away a manual run while a scheduled one is in progress", async () => {
    stubFleaflicker(async (request) => {
      await new Promise((resolve) => setTimeout(resolve, 10));
      return fakeFleaflicker(request);
    });
    const [latestBefore] = await listRuns();

    const [, response] = await Promise.all([env.RUNNER.getByName("primary").tick("cron"), triggerRun()]);

    expect(response.status).toBe(409);
    const [latest, previous] = await listRuns();
    expect(latest.trigger).toBe("cron");
    expect(previous).toEqual(latestBefore);
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

  it("gives up on a Fleaflicker request that never answers, then ticks again", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setTimeout"], now: new Date("2026-10-20T15:10:00Z") });
    let fleaflickerHangs = true;
    stubFleaflicker((request) => (fleaflickerHangs ? new Promise((_, reject) => request.signal.addEventListener("abort", () => reject(request.signal.reason))) : fakeFleaflickerSeason(request)));
    const runner = freshRunner();

    let hungTickDone = false;
    const hungTick = runner.tick("cron").finally(() => (hungTickDone = true));
    // The Durable Object shares this isolate; its timers only fire when the clock is advanced from its own I/O context
    for (let second = 0; second < 60 && !hungTickDone; second++) await runInDurableObject(runner, () => vi.advanceTimersByTimeAsync(1000));
    await hungTick;
    fleaflickerHangs = false;
    await runner.tick("cron");

    const runs = await runner.recentRuns();
    expect(runs.map(({ days }) => days[0].error)).toEqual([undefined, "Error: Request to www.fleaflicker.com timed out after 20 s"]);
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
    expect(latest).toMatchObject({ startedAt: "2026-10-20T18:21:00.000Z", days: [{ error: "Error: Roster API returned HTTP 503" }] });
    expect(alerts.at(-1)?.message).toContain("Roster API returned HTTP 503");
  });
  it("sends one emergency alert when a tip passes with no successful run in the 45 min before it", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T18:06:00Z") });
    const { alerts, cards } = stubFleaflicker(fakeFleaflickerSeason);
    const runner = freshRunner();
    await runner.tick("cron");

    vi.setSystemTime(new Date("2026-10-20T19:01:00Z"));
    await runner.tick("cron");
    vi.setSystemTime(new Date("2026-10-20T19:06:00Z"));
    await runner.tick("cron");

    expect(alerts).toHaveLength(1);
    expect(alerts[0]).toMatchInlineSnapshot(`
      {
        "expire": "1800",
        "message": "No successful run since 45 min before the tip. Check the lineup now.
      Players: Cade Cunningham, John Collins, Neemias Queta",
        "priority": "2",
        "retry": "60",
        "title": "Lineup not checked before the 2:00 PM CT tip",
        "token": "test-pushover-token",
        "url": "https://www.fleaflicker.com/nba/leagues/30579/teams/161025",
        "user": "test-pushover-user",
      }
    `);
    expect(cards.map(({ name }) => name)).toEqual([alerts[0].title]);
  });

  it("sends an emergency alert 10 min before a tip with no successful run since T-45, unless that tick's run succeeds", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T18:06:00Z") });
    let fleaflickerDown = false;
    const { alerts } = stubFleaflicker((request) => (fleaflickerDown ? new Response("Service unavailable", { status: 503 }) : fakeFleaflickerSeason(request)));
    const failingRunner = freshRunner();
    const recoveringRunner = freshRunner();
    await failingRunner.tick("cron");
    await recoveringRunner.tick("cron");

    fleaflickerDown = true;
    for (const at of ["18:21", "18:46"]) {
      vi.setSystemTime(new Date(`2026-10-20T${at}:00Z`));
      await failingRunner.tick("cron");
      await recoveringRunner.tick("cron");
    }
    vi.setSystemTime(new Date("2026-10-20T18:51:00Z"));
    await failingRunner.tick("cron");
    fleaflickerDown = false;
    await recoveringRunner.tick("cron");

    expect(alerts.filter(({ priority }) => priority === "2").map(({ title }) => title)).toEqual(["Lineup not checked before the 2:00 PM CT tip"]);
  });

  it("sends no emergency alert for today's tip when only tomorrow's page fails", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T18:06:00Z") });
    const { alerts } = stubFleaflicker((request) =>
      new URL(request.url).searchParams.get("week") === "2" ? new Response("Service unavailable", { status: 503 }) : fakeFleaflickerSeason(request),
    );
    const runner = freshRunner();

    for (const at of ["18:06", "18:21", "18:46", "18:51", "18:56", "19:01"]) {
      vi.setSystemTime(new Date(`2026-10-20T${at}:00Z`));
      await runner.tick("cron");
    }

    expect(alerts.map(({ title, priority }) => ({ title, priority }))).toEqual([{ title: "Lineup run (cron) failed", priority: "1" }]);
  });

  it("waits 30 min before trying a failed login again", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    const loginAttempts: string[] = [];
    stubFleaflicker(async (request) => {
      if (request.method === "POST") loginAttempts.push(new Date().toISOString());
      return request.method === "POST" ? new Response("<form>Your password is incorrect</form>") : new Response(LOGGED_OUT_PAGE);
    });
    const runner = freshRunner();

    for (const at of ["15:10", "15:15", "15:35", "15:40"]) {
      vi.setSystemTime(new Date(`2026-10-20T${at}:00Z`));
      await runner.tick("cron");
    }

    expect(loginAttempts).toEqual(["2026-10-20T15:10:00.000Z", "2026-10-20T15:40:00.000Z"]);
    expect((await runner.recentRuns()).map(({ login }) => login)).toMatchInlineSnapshot(`
      [
        {
          "gotSessionCookie": false,
          "status": 200,
        },
        {
          "backedOff": true,
          "gotSessionCookie": false,
          "status": 200,
        },
        {
          "backedOff": true,
          "gotSessionCookie": false,
          "status": 200,
        },
        {
          "gotSessionCookie": false,
          "status": 200,
        },
      ]
    `);
  });

  it("treats a login that leaves the page signed out as failed", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    const loginAttempts: string[] = [];
    const { alerts } = stubFleaflicker(async (request) => {
      if (request.method !== "POST") return new Response(LOGGED_OUT_PAGE);
      loginAttempts.push(new Date().toISOString());
      return fakeFleaflicker(request);
    });
    const runner = freshRunner();

    for (const at of ["15:10", "15:15"]) {
      vi.setSystemTime(new Date(`2026-10-20T${at}:00Z`));
      await runner.tick("cron");
    }

    expect(loginAttempts).toEqual(["2026-10-20T15:10:00.000Z"]);
    expect(alerts[0].message.split("\n")[0]).toMatchInlineSnapshot(`"- Fleaflicker login failed (HTTP 303, still signed out)"`);
  });

  it("keeps trying a failed login on every tick within 45 min of a tip", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T18:06:00Z") });
    let passwordChanged = false;
    const loginAttempts: string[] = [];
    stubFleaflicker(async (request) => {
      if (!passwordChanged) return fakeFleaflickerSeason(request);
      if (request.method === "POST") loginAttempts.push(new Date().toISOString());
      return request.method === "POST" ? new Response("<form>Your password is incorrect</form>") : new Response(signedOutPage);
    });
    const runner = freshRunner();
    await runner.tick("cron");

    passwordChanged = true;
    for (const at of ["18:21", "18:26"]) {
      vi.setSystemTime(new Date(`2026-10-20T${at}:00Z`));
      await runner.tick("cron");
    }

    expect(loginAttempts).toEqual(["2026-10-20T18:21:00.000Z", "2026-10-20T18:26:00.000Z"]);
  });

  it("keeps trying a failed login near a tip it only saw on the signed-out page", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T18:21:00Z") });
    const loginAttempts: string[] = [];
    stubFleaflicker(async (request) => {
      if (request.method !== "POST") return new Response(signedOutPage);
      loginAttempts.push(new Date().toISOString());
      return new Response("<form>Your password is incorrect</form>");
    });
    const runner = freshRunner();

    await runner.tick("cron");
    vi.setSystemTime(new Date("2026-10-20T18:26:00Z"));
    await runner.tick("cron");

    expect(loginAttempts).toEqual(["2026-10-20T18:21:00.000Z", "2026-10-20T18:26:00.000Z"]);
  });

  it("waits 30 min before sending a save that didn't land again", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    const { lineupSaves } = stubLineupSaves({ applySaves: false });
    const runner = freshRunner();
    await runner.setSaves(true);

    const savesPerTick = [];
    for (const at of ["15:10", "15:15", "15:45"]) {
      vi.setSystemTime(new Date(`2026-10-20T${at}:00Z`));
      const savesBefore = lineupSaves.length;
      await runner.tick("cron");
      savesPerTick.push(lineupSaves.length - savesBefore);
    }

    expect(savesPerTick).toEqual([2, 0, 2]);
  });

  it("sends a save that didn't land again on every tick within 45 min of a tip", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T18:21:00Z") });
    const { lineupSaves } = stubLineupSaves({ applySaves: false });
    const runner = freshRunner();
    await runner.setSaves(true);
    await runner.tick("cron");

    const savesBefore = lineupSaves.length;
    vi.setSystemTime(new Date("2026-10-20T18:26:00Z"));
    await runner.tick("cron");

    expect(lineupSaves.length - savesBefore).toBeGreaterThan(0);
  });

  it("sends a general alert when the page lacks matchups, without treating the run as failed", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    const { alerts } = stubFleaflicker(async (request) => {
      const response = await fakeFleaflickerSeason(request);
      return new Response((await response.text()).replace('"tooltips":[', '"tooltips":[],"renamedTooltips":['), response);
    });
    const runner = freshRunner();

    await runner.tick("cron");
    vi.setSystemTime(new Date("2026-10-20T15:15:00Z"));
    await runner.tick("cron");

    const runs = await runner.recentRuns();
    expect(runs).toHaveLength(1);
    expect(runs[0].warningAlert).toEqual({ pushover: { status: 200 }, trello: { status: 200 } });
    expect(alerts.map(({ title, priority }) => ({ title, priority }))).toEqual([{ title: "Lineup run (cron) has warnings", priority: "0" }]);
    expect(alerts[0].message.split("\n")[0]).toMatchInlineSnapshot(`"- Falling back to DOM scrape for Cade Cunningham opponent info"`);
  });

  it("keeps ticking over run records from before runs checked more than one day", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    stubFleaflicker(fakeFleaflickerSeason);
    const runner = freshRunner();
    const singleDayRecord = { trigger: "manual", startedAt: "2026-09-30T20:00:00.000Z", lineupPage: { status: 200, loggedIn: true }, decision: { ok: true } };
    await runInDurableObject(runner, (_, state) => state.storage.sql.exec("INSERT INTO runs (record) VALUES (?)", JSON.stringify(singleDayRecord)));

    await runner.tick("cron");

    const [latest] = await runner.recentRuns();
    expect(latest).toMatchObject({ trigger: "cron", days: [{ day: 1 }, { day: 2 }] });
  });

  it("alerts the owner when a tick can't even plan", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    const { alerts } = stubFleaflicker(fakeFleaflickerSeason, { rosterApiUp: () => false });
    const runner = freshRunner();

    await runner.tick("cron");

    expect(alerts.map(({ title, message }) => ({ title, message }))).toEqual([{ title: "Lineup tick (cron) failed", message: "- Error: Roster API returned HTTP 503" }]);
  });

  it("finishes the tick when the dead-man monitor is unreachable", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T15:10:00Z") });
    stubFleaflicker(fakeFleaflickerSeason, { deadManUp: false });
    const runner = freshRunner();

    await expect(runner.tick("cron")).resolves.toBeUndefined();
  });

  it("sends no emergency alert for today's tip when only tomorrow's roster fails to load", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date("2026-10-20T18:06:00Z") });
    const { alerts } = stubFleaflicker(fakeFleaflickerSeason, { rosterApiUp: (url) => url.searchParams.get("scoring_period") !== "2" });
    const runner = freshRunner();

    for (const at of ["18:06", "18:21", "18:46", "18:51", "18:56", "19:01"]) {
      vi.setSystemTime(new Date(`2026-10-20T${at}:00Z`));
      await runner.tick("cron");
    }

    expect(alerts.map(({ title, priority }) => ({ title, priority }))).toEqual([{ title: "Lineup run (cron) failed", priority: "1" }]);
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
  days: {
    day: number;
    lineupPage?: { status: number; loggedIn: boolean };
    decision?: { ok: boolean; formAction?: string; errors?: string[] };
    save?: { posted: boolean; problems: string[] };
    error?: string;
  }[];
  error?: string;
  alert?: Record<"pushover" | "trello", { status: number; response?: string } | { error: string }>;
  warningAlert?: Record<"pushover" | "trello", { status: number; response?: string } | { error: string }>;
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

function setSaves(enabled: boolean) {
  return exports.default.fetch("https://runner.test/saves", {
    method: "PUT",
    headers: { Authorization: "Bearer test-run-token" },
    body: JSON.stringify({ enabled }),
  });
}

// Opening night's page, which saves posted lineups onto itself like Fleaflicker does for a signed-in owner
function stubLineupSaves({ applySaves = true } = {}) {
  const lineupSaves: string[] = [];
  let page = fantasyStatsPage;
  const fakes = stubFleaflicker(async (request) => {
    const { pathname, searchParams } = new URL(request.url);
    if (request.method === "POST" && pathname !== "/nba/login") {
      const body = await request.text();
      lineupSaves.push(body);
      if (applySaves) page = withSlots(page, body);
      return new Response(null, { status: 303, headers: { Location: ACCEPTED_SAVE_LOCATION } });
    }
    return fakeFleaflicker(request, searchParams.get("statType") === "0" ? page : seasonStatsPage);
  });
  return { ...fakes, lineupSaves };
}

function withSlots(html: string, body: string) {
  const { document } = parseHTML(html);
  for (const [name, value] of new URLSearchParams(body)) {
    if (!name.startsWith("status")) continue;
    for (const option of document.querySelectorAll(`select[name="${name}"] option`)) option.toggleAttribute("selected", option.getAttribute("value") === value);
  }
  return document.toString();
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

function stubFleaflicker(respond: (request: Request) => Response | Promise<Response>, { pushoverStatus = () => 200, trelloStatus = () => 200, trelloCardArchived = () => false, rosterApiUp = (_url: URL) => true, deadManUp = true } = {}) {
  const deadManPings: string[] = [];
  const alerts: Record<string, string>[] = [];
  const cards: { list: string; name: string; desc: string; authorization: string | null }[] = [];
  const cardComments: { card: string; text: string }[] = [];
  const realFetch = globalThis.fetch;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const request = new Request(input, init);
    const { hostname, pathname } = new URL(request.url);
    if (hostname === "www.fleaflicker.com" && pathname === "/api/FetchRoster") {
      return rosterApiUp(new URL(request.url)) ? Response.json(openingNightRoster) : new Response("Service unavailable", { status: 503 });
    }
    if (hostname === "www.fleaflicker.com") return respond(request);
    if (hostname === "api.pushover.net") {
      const alert = Object.fromEntries(new URLSearchParams(await request.text()));
      alerts.push(alert);
      if (alert.message.length > 1024) return Response.json({ message: "cannot be longer than 1024 characters", status: 0 }, { status: 400 });
      const status = pushoverStatus();
      return status === 200 ? Response.json({ status: 1, request: "r1" }) : Response.json({ status: 0, errors: ["application is over its message limit"] }, { status });
    }
    if (hostname === "api.trello.com" && pathname === "/1/cards") {
      const { idList, name, desc } = await request.json<{ idList: string; name: string; desc: string }>();
      cards.push({ list: idList, name, desc, authorization: request.headers.get("Authorization") });
      const status = trelloStatus();
      return status === 200 ? Response.json({ id: `card-${cards.length}` }) : new Response("invalid token", { status });
    }
    const cardComment = pathname.match(/^\/1\/cards\/([^/]+)\/actions\/comments$/);
    if (hostname === "api.trello.com" && cardComment) {
      cardComments.push({ card: cardComment[1], text: new URL(request.url).searchParams.get("text")! });
      return Response.json({});
    }
    const cardLookup = pathname.match(/^\/1\/cards\/([^/]+)$/);
    if (hostname === "api.trello.com" && cardLookup) return Response.json({ id: cardLookup[1], closed: trelloCardArchived() });
    if (hostname === "hc-ping.com") {
      if (!deadManUp) throw new TypeError("hc-ping.com unreachable");
      deadManPings.push(pathname);
      return new Response("OK");
    }
    return realFetch(input, init);
  });
  return { alerts, cards, cardComments, deadManPings };
}
