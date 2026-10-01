const SILENT_AFTER_MS = 75 * 60_000;
const REPEAT_AFTER_MS = 3 * 60 * 60_000;
const ALARM_GRACE_MS = 15 * 60_000;
const FETCH_TIMEOUT_MS = 20_000;
/** Pushover priorities: 2 emergency, 1 high, 0 normal, -1 quiet (no sound) */
const EMERGENCY_PRIORITY = 2;
const QUIET_PRIORITY = -1;
const PUSHOVER_MAX_MESSAGE_LENGTH = 1024;
/** Older Worker alerts are stale news, and a lost state file re-forwards no further back than this */
const FORWARD_WINDOW_MS = 6 * 60 * 60_000;

interface WorkerAlert {
  id: number;
  at: string;
  title: string;
  body: string;
  priority: number;
  push: boolean;
  /** Every channel the Worker tried accepted it */
  delivered?: boolean;
}

interface PushoverCredentials {
  token: string;
  user: string;
}

interface Notification {
  title: string;
  message: string;
  priority: number;
  alertId?: number;
}

/** What earlier runs pushed, carried between runs */
export interface WatchdogState {
  forwardedAlertIds: number[];
  /** Watchdog alert title → ISO time last pushed */
  ownAlertsSentAt: Record<string, string>;
}

export async function runLineupWatchdog({
  runnerUrl,
  runToken,
  pushover,
  state = { forwardedAlertIds: [], ownAlertsSentAt: {} },
  now = new Date(),
}: {
  runnerUrl: string;
  runToken: string;
  pushover: PushoverCredentials;
  state?: WatchdogState;
  now?: Date;
}) {
  const nextState: WatchdogState = { forwardedAlertIds: [...state.forwardedAlertIds], ownAlertsSentAt: { ...state.ownAlertsSentAt } };
  const notifications: Notification[] = [];
  const raise = (title: string, message: string) => {
    const lastSentAt = state.ownAlertsSentAt[title];
    const sentRecently = lastSentAt !== undefined && now.getTime() - Date.parse(lastSentAt) < REPEAT_AFTER_MS;
    if (!sentRecently) notifications.push({ title, message, priority: 1 });
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
    nextState.forwardedAlertIds = state.forwardedAlertIds.filter((id) => alerts.some((alert) => alert.id === id));
    for (const alert of alerts) {
      if (alert.delivered || now.getTime() - Date.parse(alert.at) > FORWARD_WINDOW_MS) continue;
      if (!state.forwardedAlertIds.includes(alert.id)) notifications.push({ title: alert.title, message: alert.body, priority: alert.push ? alert.priority : QUIET_PRIORITY, alertId: alert.id });
    }
  } catch (error) {
    raise("Lineup runner unreachable", `The watchdog couldn't read the Worker: ${error instanceof Error ? error.message : error}`);
  }

  const result = { sent: 0, failed: 0 };
  for (const notification of notifications) {
    const accepted = await publish(pushover, notification);
    result[accepted ? "sent" : "failed"]++;
    if (!accepted) continue;
    if (notification.alertId === undefined) nextState.ownAlertsSentAt[notification.title] = now.toISOString();
    else nextState.forwardedAlertIds.push(notification.alertId);
  }
  return { ...result, state: nextState };
}

async function publish({ token, user }: PushoverCredentials, { title, message: fullMessage, priority }: Notification) {
  try {
    const message = fullMessage.length > PUSHOVER_MAX_MESSAGE_LENGTH ? `${fullMessage.slice(0, PUSHOVER_MAX_MESSAGE_LENGTH - 1)}…` : fullMessage;
    // Same retry/expire as the Worker's missed-tip alerts: re-alerts every minute for 30 min until acknowledged
    const emergency: Record<string, string> = priority === EMERGENCY_PRIORITY ? { retry: "60", expire: "1800" } : {};
    const body = new URLSearchParams({ token, user, title, message, priority: String(priority), ...emergency });
    const response = await fetch("https://api.pushover.net/1/messages.json", { method: "POST", body, signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) });
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

function formatCentralTime(iso: string) {
  const parts = new Intl.DateTimeFormat("en-US", { timeZone: "America/Chicago", hour: "numeric", minute: "2-digit" }).formatToParts(new Date(iso));
  const part = (type: string) => parts.find((p) => p.type === type)?.value;
  return `${part("hour")}:${part("minute")}${part("dayPeriod")?.[0].toLowerCase()} CT`;
}

if (import.meta.main) {
  const { LINEUP_RUNNER_URL, LINEUP_RUNNER_TOKEN, PUSHOVER_TOKEN, PUSHOVER_USER, WATCHDOG_STATE_FILE } = process.env;
  if (!LINEUP_RUNNER_URL || !LINEUP_RUNNER_TOKEN || !PUSHOVER_TOKEN || !PUSHOVER_USER || !WATCHDOG_STATE_FILE) {
    console.error("Set LINEUP_RUNNER_URL, LINEUP_RUNNER_TOKEN, PUSHOVER_TOKEN, PUSHOVER_USER and WATCHDOG_STATE_FILE");
    process.exit(1);
  }
  const pushover = { token: PUSHOVER_TOKEN, user: PUSHOVER_USER };
  if (process.argv.includes("--test")) {
    const accepted = await publish(pushover, { title: "TEST: Lineup watchdog (GitHub Actions)", message: "Test push from the GitHub Actions lineup watchdog via Pushover. No action needed", priority: 0 });
    console.log(accepted ? "Test push accepted" : "Test push failed");
    process.exit(accepted ? 0 : 1);
  }
  const stateFile = Bun.file(WATCHDOG_STATE_FILE);
  const state: WatchdogState | undefined = await stateFile.json().catch(() => undefined);
  const result = await runLineupWatchdog({ runnerUrl: LINEUP_RUNNER_URL, runToken: LINEUP_RUNNER_TOKEN, pushover, state });
  await Bun.write(stateFile, JSON.stringify(result.state));
  // Counts only: workflow logs are public
  console.log(`Pushed ${result.sent}, failed ${result.failed}${state ? "" : " (no saved state)"}`);
  if (result.sent + result.failed > 0) process.exit(1);
}
