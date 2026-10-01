import { afterEach, expect, test } from "bun:test";
import { reportProblem, setProblemHandler } from "./report-problem";

const originalAlert = globalThis.alert;
afterEach(() => {
  globalThis.alert = originalAlert;
});

// The headless lineup runner swaps in its own `alert` after this module has loaded, to collect problems
test("by default, a problem goes to whichever alert is in place when it's reported", () => {
  const problems: string[] = [];
  globalThis.alert = (message) => void problems.push(String(message));

  reportProblem("NaN weighted score for Naz Reid");

  expect(problems).toEqual(["NaN weighted score for Naz Reid"]);
});

test("once a page sets its own handler, problems go there instead of an alert", () => {
  const alerts: string[] = [];
  globalThis.alert = (message) => void alerts.push(String(message));
  const shown: string[] = [];
  setProblemHandler((message) => shown.push(message));

  reportProblem("NaN weighted score for Naz Reid");

  expect({ shown, alerts }).toEqual({ shown: ["NaN weighted score for Naz Reid"], alerts: [] });
});
