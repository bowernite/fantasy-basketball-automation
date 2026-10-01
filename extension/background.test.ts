import { afterEach, describe, expect, test } from "bun:test";
import manifest from "./manifest.json";

type Tab = { id?: number };
type Injection = { tabId: number; files?: string[]; func?: () => void };

// Loads background.js fresh against a fake `chrome` (the only mocked edge) and
// returns handles to simulate the user's actions and inspect what ran in the tab.
let loadCount = 0;
async function setup({ activeTab }: { activeTab?: Tab } = {}) {
  const injections: Injection[] = [];
  const pageCalls: string[] = [];
  let onClicked: (tab: Tab) => void = () => {};
  let onCommand: (command: string) => void = () => {};

  // Stand-in for the page's global scope, as populated by the content script
  const pageWindow = {
    saveLineup: () => pageCalls.push("saveLineup"),
    goToPreviousDay: () => pageCalls.push("goToPreviousDay"),
    goToNextDay: () => pageCalls.push("goToNextDay"),
  } as Record<string, unknown>;

  (globalThis as any).chrome = {
    action: { onClicked: { addListener: (fn: typeof onClicked) => (onClicked = fn) } },
    commands: { onCommand: { addListener: (fn: typeof onCommand) => (onCommand = fn) } },
    tabs: {
      query: (_query: unknown, callback: (tabs: Tab[]) => void) =>
        callback(activeTab ? [activeTab] : []),
    },
    scripting: {
      executeScript: ({ target, files, func }: any) => {
        injections.push({ tabId: target.tabId, files, func });
        if (!func) return Promise.resolve([]);
        // Run the injected function as the page would
        (globalThis as any).window = pageWindow;
        try {
          return Promise.resolve([{ result: func() }]);
        } finally {
          delete (globalThis as any).window;
        }
      },
    },
  };

  await import(`./background.js?load=${loadCount++}`);

  return {
    injections,
    pageCalls,
    pageWindow,
    clickToolbarIcon: (tab: Tab) => onClicked(tab),
    pressShortcut: (command: string) => onCommand(command),
  };
}

afterEach(() => {
  delete (globalThis as any).chrome;
});

describe("toolbar icon", () => {
  test("runs the lineup script in the clicked tab", async () => {
    const { injections, clickToolbarIcon } = await setup();
    clickToolbarIcon({ id: 7 });
    await Bun.sleep(0);
    expect(injections.filter((i) => i.files)).toEqual([{ tabId: 7, files: ["dist/main.js"], func: undefined }]);
  });
});

describe("keyboard shortcuts", () => {
  test("run-script runs the page's own Set lineup when the page script is loaded", async () => {
    const { injections, pageCalls, pageWindow, pressShortcut } = await setup({ activeTab: { id: 3 } });
    pageWindow.runSetLineup = () => pageCalls.push("runSetLineup");

    pressShortcut("run-script");
    await Bun.sleep(0);

    expect(pageCalls).toEqual(["runSetLineup"]);
    expect(injections.filter((i) => i.files)).toEqual([]);
  });

  test("run-script runs the standalone lineup script when the page script isn't loaded", async () => {
    const { injections, pressShortcut } = await setup({ activeTab: { id: 3 } });
    pressShortcut("run-script");
    await Bun.sleep(0);
    expect(injections.filter((i) => i.files)).toEqual([{ tabId: 3, files: ["dist/main.js"], func: undefined }]);
  });

  test.each([
    ["save-lineup", "saveLineup"],
    ["previous-day", "goToPreviousDay"],
    ["next-day", "goToNextDay"],
  ])("%s calls only the page's %s in the active tab", async (command, pageFunction) => {
    const { injections, pageCalls, pressShortcut } = await setup({ activeTab: { id: 3 } });
    pressShortcut(command);
    expect(injections.map((i) => i.tabId)).toEqual([3]);
    expect(pageCalls).toEqual([pageFunction]);
  });

  test("page actions are a no-op, not an error, when the page script isn't loaded", async () => {
    const { pageWindow, pressShortcut, pageCalls } = await setup({ activeTab: { id: 3 } });
    for (const key of Object.keys(pageWindow)) delete pageWindow[key];
    for (const command of ["save-lineup", "previous-day", "next-day"]) {
      expect(() => pressShortcut(command)).not.toThrow();
    }
    expect(pageCalls).toEqual([]);
  });

  test.each(["run-script", "save-lineup", "previous-day", "next-day"])(
    "%s does nothing when there is no active tab",
    async (command) => {
      const { injections, pressShortcut } = await setup({ activeTab: undefined });
      pressShortcut(command);
      expect(injections).toEqual([]);
    }
  );

  test("an unknown command does nothing", async () => {
    const { injections, pressShortcut } = await setup({ activeTab: { id: 3 } });
    pressShortcut("something-else");
    expect(injections).toEqual([]);
  });

  test("every shortcut declared in the manifest does something", async () => {
    for (const command of Object.keys(manifest.commands)) {
      const { injections, pressShortcut } = await setup({ activeTab: { id: 3 } });
      pressShortcut(command);
      await Bun.sleep(0);
      expect(injections.length, `command "${command}" is declared but unhandled`).toBeGreaterThan(0);
    }
  });
});
