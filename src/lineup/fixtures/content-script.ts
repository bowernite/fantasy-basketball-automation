// Runs the roster page's content script (`page-load__set-lineup.ts`) against the happy-dom globals

import { spyOn } from "bun:test";

export const HAPPY_DOM_SETTINGS = {
  disableJavaScriptFileLoading: true,
  disableCSSFileLoading: true,
  handleDisabledFileLoadingAsSuccess: true,
};

// One counter for every test file: bun shares the module cache across files, so a repeated query would reuse a cached run
let loads = 0;

// Each call re-runs the content script, like a fresh page load
export async function runContentScript() {
  await import(`../../../page-load__set-lineup.ts?load=${++loads}`);
  await Bun.sleep(0);
}

export function recordAlerts() {
  const alerts: string[] = [];
  spyOn(window, "alert").mockImplementation((message) => void alerts.push(String(message)));
  return alerts;
}
