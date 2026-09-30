const SILENT_AFTER_MS = 75 * 60_000;
const REPEAT_AFTER_MS = 3 * 60 * 60_000;
const ALARM_GRACE_MS = 15 * 60_000;
const FETCH_TIMEOUT_MS = 20_000;
/** Well inside ntfy.sh's 12 h message cache, which is how already-forwarded alerts are recognized */
const FORWARD_WINDOW_MS = 6 * 60 * 60_000;

interface WorkerAlert {
  id: number;
  at: string;
  title: string;
  body: string;
  priority: number;
  push: boolean;
}

interface TopicMessage {
  time: number;
  title?: string;
}

interface Notification {
  title: string;
  message: string;
  priority: number;
}

export async function runLineupWatchdog({ runnerUrl, runToken, ntfyTopic, now = new Date() }: { runnerUrl: string; runToken: string; ntfyTopic: string; now?: Date }) {
  const sent = await readTopic(ntfyTopic);
  const notifications: Notification[] = [];
  const raise = (title: string, message: string) => {
    const sentRecently = sent.some((sentMessage) => sentMessage.title === title && now.getTime() - sentMessage.time * 1000 < REPEAT_AFTER_MS);
    if (!sentRecently) notifications.push({ title, message, priority: 4 });
  };

  try {
    const { runs, status, alerts } = await readRunner(runnerUrl, runToken);
    const newestRunAt = Date.parse(runs[0]?.startedAt ?? "");
    const ranRecently = now.getTime() - newestRunAt <= SILENT_AFTER_MS;
    if (!ranRecently) {
      const minutesSinceRun = Math.round((now.getTime() - newestRunAt) / 60_000);
      raise("Lineup runner silent", `No lineup run recorded in ${minutesSinceRun} min. Check the Worker (lineup-runner Skill)`);
    }
    if (status.alarm === null) raise("Lineup runner alarm stuck", "The Worker has no alarm set, and cron didn't re-arm it");
    else if (now.getTime() - Date.parse(status.alarm) > ALARM_GRACE_MS) {
      raise("Lineup runner alarm stuck", `The Worker's 5-min alarm was due at ${formatCentralTime(status.alarm)} and hasn't fired, and cron didn't re-arm it`);
    }
    for (const alert of alerts) {
      if (now.getTime() - Date.parse(alert.at) > FORWARD_WINDOW_MS) continue;
      const alreadyForwarded = sent.some((message) => message.title === alert.title && message.time * 1000 >= Date.parse(alert.at));
      if (!alreadyForwarded) notifications.push({ title: alert.title, message: alert.body, priority: ntfyPriority(alert) });
    }
  } catch (error) {
    raise("Lineup runner unreachable", `The watchdog couldn't read the Worker: ${error instanceof Error ? error.message : error}`);
  }

  const result = { sent: 0, failed: 0 };
  for (const notification of notifications) {
    const accepted = await publish(ntfyTopic, notification);
    result[accepted ? "sent" : "failed"]++;
  }
  return result;
}

async function publish(ntfyTopic: string, notification: Notification) {
  try {
    const response = await fetch("https://ntfy.sh/", { method: "POST", body: JSON.stringify({ topic: ntfyTopic, ...notification }), signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) });
    return response.ok;
  } catch {
    return false;
  }
}

async function readRunner(runnerUrl: string, runToken: string) {
  const get = async <T>(path: string): Promise<T> => {
    const response = await fetch(`${runnerUrl}${path}`, { headers: { Authorization: `Bearer ${runToken}` }, signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) });
    if (!response.ok) throw new Error(`GET ${path} returned HTTP ${response.status}`);
    return response.json();
  };
  const [runs, status, alerts] = await Promise.all([get<{ startedAt: string }[]>("/runs"), get<{ alarm: string | null }>("/status"), get<WorkerAlert[]>("/alerts")]);
  return { runs, status, alerts };
}

/** Messages already on the topic (ntfy.sh keeps 12 h); empty if unreadable, so alerts err toward repeating */
async function readTopic(ntfyTopic: string): Promise<TopicMessage[]> {
  try {
    const response = await fetch(`https://ntfy.sh/${ntfyTopic}/json?poll=1&since=12h`, { signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) });
    if (!response.ok) return [];
    const lines = (await response.text()).split("\n").filter(Boolean);
    return lines.map((line) => JSON.parse(line)).filter((message) => message.event === "message");
  } catch {
    return [];
  }
}

/** ntfy priorities: 5 max, 4 high, 3 default, 2 low (silent) */
function ntfyPriority({ priority, push }: WorkerAlert) {
  if (!push) return 2;
  return priority + 3;
}

function formatCentralTime(iso: string) {
  const parts = new Intl.DateTimeFormat("en-US", { timeZone: "America/Chicago", hour: "numeric", minute: "2-digit" }).formatToParts(new Date(iso));
  const part = (type: string) => parts.find((p) => p.type === type)?.value;
  return `${part("hour")}:${part("minute")}${part("dayPeriod")?.[0].toLowerCase()} CT`;
}

if (import.meta.main) {
  const { LINEUP_RUNNER_URL, LINEUP_RUNNER_TOKEN, NTFY_TOPIC } = process.env;
  if (!LINEUP_RUNNER_URL || !LINEUP_RUNNER_TOKEN || !NTFY_TOPIC) {
    console.error("Set LINEUP_RUNNER_URL, LINEUP_RUNNER_TOKEN and NTFY_TOPIC");
    process.exit(1);
  }
  if (process.argv.includes("--test")) {
    const accepted = await publish(NTFY_TOPIC, { title: "Lineup watchdog test", message: "Test push from the GitHub Actions lineup watchdog. No action needed", priority: 3 });
    console.log(accepted ? "Test push accepted" : "Test push failed");
    process.exit(accepted ? 0 : 1);
  }
  const { sent, failed } = await runLineupWatchdog({ runnerUrl: LINEUP_RUNNER_URL, runToken: LINEUP_RUNNER_TOKEN, ntfyTopic: NTFY_TOPIC });
  // Counts only: workflow logs are public
  console.log(`Pushed ${sent}, failed ${failed}`);
  if (sent + failed > 0) process.exit(1);
}
