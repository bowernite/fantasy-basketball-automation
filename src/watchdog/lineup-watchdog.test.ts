import { afterEach, expect, spyOn, test } from "bun:test";
import { runLineupWatchdog, type WatchdogState } from "./lineup-watchdog";

const RUNNER_URL = "https://runner.example.com";
const RUN_TOKEN = "test-run-token";
const PUSHOVER = { token: "test-app-token", user: "test-user-key" };
const NOW = new Date("2026-10-20T18:00:00.000Z");

afterEach(() => {
  (globalThis.fetch as unknown as { mockRestore?: () => void }).mockRestore?.();
});

test("forwards a new Worker alert to Pushover", async () => {
  const pushover = fakeServices({
    alerts: [{ id: 7, at: "2026-10-20T17:55:00.000Z", title: "Lineup check failed", body: "Page had no lineup form", priority: 1, push: true }],
  });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });

  expect(pushover.published).toMatchInlineSnapshot(`
    [
      {
        "message": "Page had no lineup form",
        "priority": "1",
        "title": "Lineup check failed",
      },
    ]
  `);
});

test("skips a Worker alert it forwarded on an earlier run", async () => {
  const pushover = fakeServices({
    alerts: [{ id: 7, at: "2026-10-20T17:40:00.000Z", title: "Lineup check failed", body: "Page had no lineup form", priority: 1, push: true }],
  });

  const { state } = await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });
  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, state, now: new Date("2026-10-20T18:15:00.000Z") });

  expect(pushover.published.map((message) => message.title)).toEqual(["Lineup check failed"]);
});

test("leaves out a Worker alert every channel already accepted", async () => {
  const pushover = fakeServices({
    alerts: [
      { id: 8, at: "2026-10-20T17:55:00.000Z", title: "Lineup check failed", body: "Page had no lineup form", priority: 1, push: true, delivered: true },
      { id: 7, at: "2026-10-20T17:50:00.000Z", title: "Lineup save rejected", body: "Fleaflicker showed an error", priority: 1, push: true, delivered: false },
    ],
  });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });

  expect(pushover.published.map((message) => message.title)).toEqual(["Lineup save rejected"]);
});

test("ignores Worker alerts older than 6 hours", async () => {
  const pushover = fakeServices({
    alerts: [{ id: 3, at: "2026-10-20T11:30:00.000Z", title: "Lineup check failed", body: "Page had no lineup form", priority: 1, push: true }],
  });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });

  expect(pushover.published).toEqual([]);
});

test.each([
  { priority: 1, push: true, pushoverPriority: "1" },
  { priority: 0, push: true, pushoverPriority: "0" },
  { priority: 0, push: false, pushoverPriority: "-1" },
])("forwards Worker priority $priority (push $push) as Pushover priority $pushoverPriority", async ({ priority, push, pushoverPriority }) => {
  const pushover = fakeServices({
    alerts: [{ id: 7, at: "2026-10-20T17:55:00.000Z", title: "Lineup check failed", body: "Page had no lineup form", priority, push }],
  });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });

  expect(pushover.published.map((message) => message.priority)).toEqual([pushoverPriority]);
});

test("forwards a missed-tip alert as a Pushover emergency that repeats until acknowledged", async () => {
  const pushover = fakeServices({
    alerts: [{ id: 9, at: "2026-10-20T17:55:00.000Z", title: "Lineup not checked before the 1:00 PM CT tip", body: "Check the lineup now", priority: 2, push: true }],
  });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });

  expect(pushover.published).toMatchInlineSnapshot(`
    [
      {
        "expire": "1800",
        "message": "Check the lineup now",
        "priority": "2",
        "retry": "60",
        "title": "Lineup not checked before the 1:00 PM CT tip",
      },
    ]
  `);
});

test("shortens a Worker alert body to Pushover's 1024-character limit", async () => {
  const pushover = fakeServices({
    alerts: [{ id: 7, at: "2026-10-20T17:55:00.000Z", title: "Lineup check failed", body: "x".repeat(1500), priority: 1, push: true }],
  });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });

  expect(pushover.published.map((message) => message.message)).toEqual([`${"x".repeat(1023)}…`]);
});

test("alerts when the Worker hasn't recorded a run in over 75 minutes", async () => {
  const pushover = fakeServices({ runs: [{ startedAt: "2026-10-20T16:40:00.000Z" }, { startedAt: "2026-10-20T15:40:00.000Z" }] });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });

  expect(pushover.published).toMatchInlineSnapshot(`
    [
      {
        "message": "No lineup run recorded in 80 min. Check the Worker (lineup-runner Skill)",
        "priority": "1",
        "title": "Lineup runner silent",
      },
    ]
  `);
});

test("repeats a watchdog alert only after 3 hours", async () => {
  const pushover = fakeServices({ runs: [{ startedAt: "2026-10-20T12:00:00.000Z" }], status: { alarm: "2026-10-20T21:02:00.000Z" } });
  const runAt = async (now: string, state?: WatchdogState) => (await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, state, now: new Date(now) })).state;

  const afterFirstPush = await runAt("2026-10-20T18:00:00.000Z");
  await runAt("2026-10-20T20:59:00.000Z", afterFirstPush);
  await runAt("2026-10-20T21:00:00.000Z", afterFirstPush);

  expect(pushover.published.map((message) => message.title)).toEqual(["Lineup runner silent", "Lineup runner silent"]);
});

test.each([
  { alarm: "2026-10-20T17:40:00.000Z", message: "The Worker's 5-min alarm was due at 12:40p CT and hasn't fired, and cron didn't re-arm it" },
  { alarm: null, message: "The Worker has no alarm set, and cron didn't re-arm it" },
])("alerts when the Worker's alarm is $alarm", async ({ alarm, message }) => {
  const pushover = fakeServices({ status: { alarm } });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });

  expect(pushover.published).toEqual([{ title: "Lineup runner alarm stuck", message, priority: "1" }]);
});

test("alerts when the Worker is unreachable", async () => {
  const pushover = fakeServices({ runnerDown: true });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });

  expect(pushover.published).toMatchInlineSnapshot(`
    [
      {
        "message": "The watchdog couldn't read the Worker: GET /runs returned HTTP 503",
        "priority": "1",
        "title": "Lineup runner unreachable",
      },
    ]
  `);
});

test("reports how many pushes Pushover accepted and rejected", async () => {
  fakeServices({ runs: [{ startedAt: "2026-10-20T12:00:00.000Z" }], status: { alarm: null }, pushoverRejectsTitle: "Lineup runner alarm stuck" });

  const { sent, failed } = await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });

  expect({ sent, failed }).toEqual({ sent: 1, failed: 1 });
});

test("retries a forward Pushover rejected on the next run", async () => {
  const alerts = [{ id: 7, at: "2026-10-20T17:55:00.000Z", title: "Lineup check failed", body: "Page had no lineup form", priority: 1, push: true }];
  fakeServices({ alerts, pushoverRejectsTitle: "Lineup check failed" });
  const { state } = await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, now: NOW });
  (globalThis.fetch as unknown as { mockRestore: () => void }).mockRestore();

  const pushover = fakeServices({ alerts });
  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, pushover: PUSHOVER, state, now: new Date("2026-10-20T18:15:00.000Z") });

  expect(pushover.published.map((message) => message.title)).toEqual(["Lineup check failed"]);
});

function fakeServices({
  runs = [{ startedAt: "2026-10-20T17:30:00.000Z" }],
  status = { alarm: "2026-10-20T18:02:00.000Z" },
  alerts = [],
  runnerDown = false,
  pushoverRejectsTitle,
}: {
  runs?: { startedAt: string }[];
  status?: { alarm: string | null };
  alerts?: { id: number; at: string; title: string; body: string; priority: number; push: boolean; delivered?: boolean }[];
  runnerDown?: boolean;
  pushoverRejectsTitle?: string;
} = {}) {
  const published: Record<string, unknown>[] = [];
  spyOn(globalThis, "fetch").mockImplementation((async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input));
    if (url.origin === RUNNER_URL) {
      if (runnerDown) return new Response("error code: 1102", { status: 503 });
      if (new Headers(init?.headers).get("Authorization") !== `Bearer ${RUN_TOKEN}`) return new Response("unauthorized", { status: 401 });
      const routes: Record<string, unknown> = { "/runs": runs, "/status": status, "/alerts": alerts };
      return url.pathname in routes ? Response.json(routes[url.pathname]) : new Response("not found", { status: 404 });
    }
    if (url.href === "https://api.pushover.net/1/messages.json" && init?.method === "POST") {
      const form = Object.fromEntries(new URLSearchParams(String(init.body)));
      if (form.token !== PUSHOVER.token || form.user !== PUSHOVER.user) return Response.json({ status: 0, errors: ["application token is invalid"] }, { status: 400 });
      if (form.message.length > 1024) return Response.json({ status: 0, errors: ["message is too long"] }, { status: 400 });
      if (form.title === pushoverRejectsTitle) return Response.json({ status: 0, errors: ["message cannot be blank"] }, { status: 400 });
      const { token, user, ...message } = form;
      published.push(message);
      return Response.json({ status: 1, request: `r${published.length}` });
    }
    throw new Error(`Unexpected fetch ${url}`);
  }) as typeof fetch);
  return { published };
}
