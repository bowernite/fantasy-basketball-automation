import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, beforeEach, expect, setSystemTime, spyOn, test } from "bun:test";
import { loadLineupPage, PAGE_URL } from "../../lineup/fixtures/lineup-page";
import { HAPPY_DOM_SETTINGS, recordAlerts, runContentScript } from "../../lineup/fixtures/content-script";

beforeAll(() => GlobalRegistrator.register({ url: PAGE_URL, settings: HAPPY_DOM_SETTINGS }));
afterAll(() => {
  setSystemTime();
  GlobalRegistrator.unregister();
});

beforeEach(() => {
  setSystemTime(new Date("2026-10-20T14:00:00Z"));
  for (const method of ["log", "table", "clear", "warn"] as const) spyOn(console, method).mockImplementation(() => {});
  recordAlerts();
});

test("the overlay's stylesheet, with its color tokens, is added once however many times the content script runs", async () => {
  loadLineupPage();

  await runContentScript();
  await runContentScript();

  const sheets = document.head.querySelectorAll("style[data-ffx]");
  expect(sheets).toHaveLength(1);
  expect(sheets[0].textContent).toContain("--ffx-ink: #26313D");
});
