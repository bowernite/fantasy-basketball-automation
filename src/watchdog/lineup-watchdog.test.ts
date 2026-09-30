import { afterEach, expect, spyOn, test } from "bun:test";
import { runLineupWatchdog } from "./lineup-watchdog";

const RUNNER_URL = "https://runner.example.com";
const RUN_TOKEN = "test-run-token";
const NTFY_TOPIC = "test-topic";
const NOW = new Date("2026-10-20T18:00:00.000Z");

afterEach(() => {
  (globalThis.fetch as unknown as { mockRestore?: () => void }).mockRestore?.();
});

test("forwards a new Worker alert to ntfy", async () => {
  const ntfy = fakeServices({
    alerts: [{ id: 7, at: "2026-10-20T17:55:00.000Z", title: "Lineup check failed", body: "Page had no lineup form", priority: 1, push: true }],
  });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });

  expect(ntfy.published).toMatchInlineSnapshot(`
    [
      {
        "message": "Page had no lineup form",
        "priority": 4,
        "title": "Lineup check failed",
        "topic": "test-topic",
      },
    ]
  `);
});

test("skips a Worker alert it already forwarded", async () => {
  const ntfy = fakeServices({
    alerts: [{ id: 7, at: "2026-10-20T17:40:00.000Z", title: "Lineup check failed", body: "Page had no lineup form", priority: 1, push: true }],
    alreadyOnTopic: [{ time: "2026-10-20T17:45:00.000Z", title: "Lineup check failed" }],
  });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });

  expect(ntfy.published).toEqual([]);
});

test("ignores Worker alerts older than 6 hours, which ntfy may have dropped from its cache", async () => {
  const ntfy = fakeServices({
    alerts: [{ id: 3, at: "2026-10-20T11:30:00.000Z", title: "Lineup check failed", body: "Page had no lineup form", priority: 1, push: true }],
  });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });

  expect(ntfy.published).toEqual([]);
});

test.each([
  { priority: 2, push: true, ntfyPriority: 5 },
  { priority: 1, push: true, ntfyPriority: 4 },
  { priority: 0, push: true, ntfyPriority: 3 },
  { priority: 0, push: false, ntfyPriority: 2 },
])("forwards Worker priority $priority (push $push) as ntfy priority $ntfyPriority", async ({ priority, push, ntfyPriority }) => {
  const ntfy = fakeServices({
    alerts: [{ id: 7, at: "2026-10-20T17:55:00.000Z", title: "Lineup check failed", body: "Page had no lineup form", priority, push }],
  });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });

  expect(ntfy.published.map((message) => message.priority)).toEqual([ntfyPriority]);
});

test("alerts when the Worker hasn't recorded a run in over 75 minutes", async () => {
  const ntfy = fakeServices({ runs: [{ startedAt: "2026-10-20T16:40:00.000Z" }, { startedAt: "2026-10-20T15:40:00.000Z" }] });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });

  expect(ntfy.published).toMatchInlineSnapshot(`
    [
      {
        "message": "No lineup run recorded in 80 min. Check the Worker (lineup-runner Skill)",
        "priority": 4,
        "title": "Lineup runner silent",
        "topic": "test-topic",
      },
    ]
  `);
});

test("repeats a watchdog alert only after 3 hours", async () => {
  const runs = [{ startedAt: "2026-10-20T12:00:00.000Z" }];
  const recentlySent = fakeServices({ runs, alreadyOnTopic: [{ time: "2026-10-20T15:30:00.000Z", title: "Lineup runner silent" }] });
  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });
  expect(recentlySent.published).toEqual([]);
  (globalThis.fetch as unknown as { mockRestore: () => void }).mockRestore();

  const sentLongAgo = fakeServices({ runs, alreadyOnTopic: [{ time: "2026-10-20T14:50:00.000Z", title: "Lineup runner silent" }] });
  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });
  expect(sentLongAgo.published.map((message) => message.title)).toEqual(["Lineup runner silent"]);
});

test.each([
  { alarm: "2026-10-20T17:40:00.000Z", message: "The Worker's 5-min alarm was due at 12:40p CT and hasn't fired, and cron didn't re-arm it" },
  { alarm: null, message: "The Worker has no alarm set, and cron didn't re-arm it" },
])("alerts when the Worker's alarm is $alarm", async ({ alarm, message }) => {
  const ntfy = fakeServices({ status: { alarm } });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });

  expect(ntfy.published).toEqual([{ topic: NTFY_TOPIC, title: "Lineup runner alarm stuck", message, priority: 4 }]);
});

test("alerts when the Worker is unreachable", async () => {
  const ntfy = fakeServices({ runnerDown: true });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });

  expect(ntfy.published).toMatchInlineSnapshot(`
    [
      {
        "message": "The watchdog couldn't read the Worker: GET /runs returned HTTP 503",
        "priority": 4,
        "title": "Lineup runner unreachable",
        "topic": "test-topic",
      },
    ]
  `);
});

test("reports how many pushes ntfy accepted and rejected", async () => {
  fakeServices({ runs: [{ startedAt: "2026-10-20T12:00:00.000Z" }], status: { alarm: null }, ntfyRejectsTitle: "Lineup runner alarm stuck" });

  const result = await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });

  expect(result).toEqual({ sent: 1, failed: 1 });
});

test("still pushes when it can't read what the topic already has", async () => {
  const ntfy = fakeServices({ runs: [{ startedAt: "2026-10-20T12:00:00.000Z" }], topicUnreadable: true });

  await runLineupWatchdog({ runnerUrl: RUNNER_URL, runToken: RUN_TOKEN, ntfyTopic: NTFY_TOPIC, now: NOW });

  expect(ntfy.published.map((message) => message.title)).toEqual(["Lineup runner silent"]);
});

function fakeServices({
  runs = [{ startedAt: "2026-10-20T17:30:00.000Z" }],
  status = { alarm: "2026-10-20T18:02:00.000Z" },
  alerts = [],
  alreadyOnTopic = [],
  runnerDown = false,
  ntfyRejectsTitle,
  topicUnreadable = false,
}: {
  runs?: { startedAt: string }[];
  status?: { alarm: string | null };
  alerts?: { id: number; at: string; title: string; body: string; priority: number; push: boolean }[];
  alreadyOnTopic?: { time: string; title: string }[];
  runnerDown?: boolean;
  ntfyRejectsTitle?: string;
  topicUnreadable?: boolean;
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
    if (url.origin === "https://ntfy.sh") {
      if (init?.method === "POST" && url.pathname === "/") {
        const message = JSON.parse(String(init.body));
        if (message.title === ntfyRejectsTitle) return Response.json({ code: 42908, http: 429, error: "limit reached: daily message quota reached" }, { status: 429 });
        published.push(message);
        return Response.json({ id: `m${published.length}`, time: Math.floor(NOW.getTime() / 1000), event: "message", ...message });
      }
      if (url.pathname === `/${NTFY_TOPIC}/json`) {
        if (topicUnreadable) return new Response("<html>502 Bad Gateway</html>", { status: 502 });
        const earlier = alreadyOnTopic.map(({ time, title }) => ({ event: "message", time: Math.floor(Date.parse(time) / 1000), title, message: "" }));
        const lines = [...earlier, ...published.map((message) => ({ event: "message", time: Math.floor(NOW.getTime() / 1000), ...message }))].map((message) => JSON.stringify(message));
        return new Response(lines.join("\n"));
      }
    }
    throw new Error(`Unexpected fetch ${url}`);
  }) as typeof fetch);
  return { published };
}
