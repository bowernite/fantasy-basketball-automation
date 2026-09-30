import { env, exports } from "cloudflare:workers";
import { runDurableObjectAlarm } from "cloudflare:test";
import { afterEach, describe, expect, it, vi } from "vitest";

const LOGGED_OUT_PAGE = `<html><body><a class="btn" href="/nba/login">Log In</a></body></html>`;
const LOGGED_IN_PAGE = `<html><body><a href="/logout">Sign Out</a><select name="status123"></select></body></html>`;

afterEach(() => vi.restoreAllMocks());

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

    const stored = await env.RUN_LOG.get(record.key);
    expect(await stored?.json()).toEqual(record);
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
    const { objects } = await env.RUN_LOG.list();
    const records = await Promise.all(objects.map(async ({ key }) => (await env.RUN_LOG.get(key))!.json<RunRecord>()));
    expect(records.filter((record) => record.trigger === "alarm")).toEqual([
      expect.objectContaining({ lineupPage: { status: 200, loggedIn: true } }),
    ]);
  });

  it("refuses to run without the run token", async () => {
    stubFleaflicker(() => new Response(LOGGED_OUT_PAGE));
    const recordsBefore = (await env.RUN_LOG.list()).objects.length;

    const response = await exports.default.fetch("https://runner.test/run", {
      method: "POST",
      headers: { Authorization: "Bearer wrong-token" },
    });

    expect(response.status).toBe(401);
    expect((await env.RUN_LOG.list()).objects).toHaveLength(recordsBefore);
  });
});

type RunRecord = {
  key: string;
  trigger: "manual" | "alarm";
  login?: { status: number; gotSessionCookie: boolean };
  lineupPage: { status: number; loggedIn: boolean };
};

function triggerRun() {
  return exports.default.fetch("https://runner.test/run", {
    method: "POST",
    headers: { Authorization: "Bearer test-run-token" },
  });
}

async function fakeFleaflicker(request: Request) {
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
  return new Response(hasSession ? LOGGED_IN_PAGE : LOGGED_OUT_PAGE);
}

function stubFleaflicker(respond: (request: Request) => Response | Promise<Response>) {
  const realFetch = globalThis.fetch;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const request = new Request(input, init);
    if (new URL(request.url).hostname === "www.fleaflicker.com") return respond(request);
    return realFetch(input, init);
  });
}
