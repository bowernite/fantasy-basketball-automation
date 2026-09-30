import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, afterEach, beforeAll, beforeEach, expect, setSystemTime, spyOn, test } from "bun:test";
import { loadLineupPage, PAGE_URL, startedLineup } from "./fixtures/lineup-page";

beforeAll(() =>
  GlobalRegistrator.register({
    url: PAGE_URL,
    settings: { disableJavaScriptFileLoading: true, disableCSSFileLoading: true },
  }),
);
afterAll(() => GlobalRegistrator.unregister());

let alerts: string[];
beforeEach(() => {
  // Morning of the fixture's day, before any tip
  setSystemTime(new Date("2026-10-20T14:00:00Z"));
  alerts = [];
  spyOn(window, "alert").mockImplementation((message) => void alerts.push(String(message)));
});
afterEach(() => setSystemTime());

async function setLineupAndCollectProblems() {
  const { setLineup } = await import("./set-lineup");
  const problems = [...alerts];
  try {
    await setLineup();
  } catch (error) {
    problems.push(String(error));
  }
  return [...problems, ...alerts];
}

test("on the real opening-night page, starts everyone with a game and benches the idle starter", async () => {
  loadLineupPage();

  const problems = await setLineupAndCollectProblems();

  expect(problems).toEqual([]);
  expect(startedLineup()).toMatchInlineSnapshot();
});
