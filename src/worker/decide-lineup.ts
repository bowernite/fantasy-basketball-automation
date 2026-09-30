import { parseHTML } from "linkedom";
import { setLineup } from "../lineup/set-lineup";

export type LineupDecision =
  | { ok: true; formAction: string; body: string; starters: Starter[] }
  | { ok: false; errors: string[] };

type Starter = { player: string; slot: string };
/** Signed-in `FetchRoster` response for one day (only the fields read here) */
export type ApiRoster = { groups: { slots: { leaguePlayer?: { proPlayer: { id: number; nameFull: string } } }[] }[] };
type LineupSlot = { mask: number; name: string; numStart: number; group: "START" | "BENCH" };

const BENCH_VALUE = "0";

export async function decideLineup(html: string, apiRoster?: ApiRoster): Promise<LineupDecision> {
  const { document, Event } = parseHTML(html);
  addMissingFormControlBehavior(document);
  const form = document.querySelector<HTMLFormElement>("form[method=post]");
  if (!form) return { ok: false, errors: ["No lineup form on the page; the session may be logged out"] };
  const selects = Array.from(form.querySelectorAll<HTMLSelectElement>("select[name^=status]"));
  if (apiRoster) {
    const disagreements = findPageApiDisagreements(selects, apiRoster);
    if (disagreements.length > 0) return { ok: false, errors: disagreements };
  }

  const problems: string[] = [];
  const pageGlobals = {
    document,
    Event,
    alert: (message: unknown) => problems.push(String(message)),
    console: withoutDebugOutput(console),
  };
  await withPageGlobals(pageGlobals, setLineup).catch((error) => {
    if (!problems.includes(String(error))) problems.push(String(error));
  });
  if (problems.length > 0) return { ok: false, errors: problems };

  const startingSlots = getStartingSlots(document);
  if (startingSlots.length === 0) return { ok: false, errors: ["No starting slots (allPositions) in the page data; can't check the lineup"] };
  const emptySlotProblems = findFillableEmptySlots(startingSlots, selects);
  if (emptySlotProblems.length > 0) return { ok: false, errors: emptySlotProblems };

  const fields = Array.from(form.querySelectorAll<HTMLInputElement | HTMLSelectElement>("input[name], select[name]"));
  const body = new URLSearchParams(fields.map((field) => [field.name, field.value])).toString();
  const starters = startingSlots.flatMap((slot) =>
    selects.filter((select) => select.value === String(slot.mask)).map((select) => ({ player: getPlayerName(select), slot: slot.name })),
  );
  return { ok: true, formAction: form.getAttribute("action")!, body, starters };
}

function findPageApiDisagreements(selects: HTMLSelectElement[], apiRoster: ApiRoster) {
  const apiPlayerIds = new Set(apiRoster.groups.flatMap((group) => group.slots.flatMap((slot) => slot.leaguePlayer?.proPlayer.id ?? [])));
  return selects
    .filter((select) => !apiPlayerIds.has(Number(select.name.replace("status", ""))))
    .map((select) => `Page and API disagree: ${getPlayerName(select)} is on the page but not in the API roster`);
}

// The server saves an under-filled lineup without complaint, so this is the only guard against one
function findFillableEmptySlots(startingSlots: LineupSlot[], selects: HTMLSelectElement[]) {
  const benchSelects = selects.filter((select) => select.value === BENCH_VALUE);
  return startingSlots.flatMap((slot) => {
    const numFilled = selects.filter((select) => select.value === String(slot.mask)).length;
    if (numFilled >= slot.numStart) return [];
    const eligibleBenchPlayers = benchSelects.filter((select) => select.querySelector(`option[value="${slot.mask}"]`)).map(getPlayerName);
    if (eligibleBenchPlayers.length === 0) return [];
    return [`${slot.name} slot is empty (${numFilled}/${slot.numStart} filled) while eligible players sit on the bench: ${eligibleBenchPlayers.join(", ")}`];
  });
}

function getStartingSlots(document: Document): LineupSlot[] {
  const pageDataScript = document.getElementById("page-data")?.textContent ?? "";
  const pageDataJson = pageDataScript.match(/window\.pageData\s*=\s*(\{.*?\});/s)?.[1];
  const allPositions: LineupSlot[] = pageDataJson ? (JSON.parse(pageDataJson).allPositions ?? []) : [];
  return allPositions.filter((slot) => slot.group === "START");
}

function getPlayerName(select: HTMLSelectElement) {
  return select.closest("tr")?.querySelector(".player-text")?.textContent ?? select.name;
}

// The extension logs whole player objects (incl. DOM rows) and tables of them
function withoutDebugOutput(console: Console): Console {
  const debugMethods = new Set<PropertyKey>(["log", "table", "clear", "dir", "dirxml", "debug", "info"]);
  return new Proxy(console, {
    get(target, key) {
      if (debugMethods.has(key)) return () => {};
      const value = Reflect.get(target, key);
      return typeof value === "function" ? value.bind(target) : value;
    },
  });
}

async function withPageGlobals(globals: Record<string, unknown>, run: () => Promise<void>) {
  const saved = Object.fromEntries(Object.keys(globals).map((key) => [key, Reflect.get(globalThis, key)]));
  Object.assign(globalThis, globals);
  try {
    await run();
  } finally {
    Object.assign(globalThis, saved);
  }
}

// linkedom leaves out the parts of <select>/<option> the extension reads and writes
function addMissingFormControlBehavior(document: Document) {
  const selectPrototype = Object.getPrototypeOf(document.createElement("select"));
  const optionPrototype = Object.getPrototypeOf(document.createElement("option"));
  Object.defineProperty(optionPrototype, "text", {
    configurable: true,
    get(this: HTMLOptionElement) {
      return this.textContent;
    },
  });
  Object.defineProperty(selectPrototype, "selectedOptions", {
    configurable: true,
    get(this: HTMLSelectElement) {
      const selected = this.querySelector("option[selected]") ?? this.querySelector("option");
      return selected ? [selected] : [];
    },
  });
  Object.defineProperty(selectPrototype, "value", {
    configurable: true,
    get(this: HTMLSelectElement) {
      return this.selectedOptions[0]?.getAttribute("value") ?? "";
    },
    set(this: HTMLSelectElement, value: string) {
      for (const option of this.querySelectorAll("option")) option.toggleAttribute("selected", option.getAttribute("value") === value);
    },
  });
}
