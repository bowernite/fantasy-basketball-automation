import { env, runInDurableObject } from "cloudflare:test";
import { expect, it, vi } from "vitest";

it("probe", async () => {
  const testSetTimeout = globalThis.setTimeout;
  vi.useFakeTimers({ toFake: ["setTimeout"] });
  const stub = env.RUNNER.getByName("probe");
  const same = await runInDurableObject(stub, () => globalThis.setTimeout === testSetTimeout);
  const faked = await runInDurableObject(stub, () => (globalThis.setTimeout as any).clock != null || String(globalThis.setTimeout).includes("clock"));
  console.error("PROBE", { same, faked, fakedHere: String(globalThis.setTimeout).slice(0, 80) });
  let fired = false;
  const p = runInDurableObject(stub, async () => { await new Promise((r) => setTimeout(r, 5000)); fired = true; });
  for (let i = 0; i < 20 && !fired; i++) { await vi.advanceTimersByTimeAsync(1000); await new Promise((r) => (vi as any).getRealSystemTime && r(null) || r(null)); }
  console.error("PROBE fired after loop", fired);
  vi.useRealTimers();
  expect(true).toBe(true);
});
