import { parseHTML } from "linkedom";
import { setLineup } from "../lineup/set-lineup";

export type LineupDecision =
  | { ok: true; formAction: string; body: string; starters: Starter[]; changes: Change[]; warnings: string[] }
  | { ok: false; errors: string[] };

type Starter = { player: string; slot: string; locked?: true };
type Change = { player: string; from: string; to: string };
/** Signed-in `FetchRoster` response for one day (only the fields read here) */
export type ApiRoster = { lineupPeriod: { ordinal: number }; groups: { slots: { position: { label: string }; leaguePlayer?: ApiPlayer }[] }[] };
type ApiPlayer = { proPlayer: { id: number; nameFull: string }; eligibleFor: { label: string }[] };
type LockedPlayer = { id: number; name: string; slot: string };
type LineupSlot = { mask: number; name: string; numStart: number; group: "START" | "BENCH" };

const BENCH_VALUE = "0";
const PAGE_TO_API_SLOT_LABEL: Record<string, string> = { Bench: "BN" };

export async function decideLineup(html: string, apiRoster?: ApiRoster): Promise<LineupDecision> {
  const { window, document, Event } = parseHTML(html);
  addMissingFormControlBehavior(document);
  const errorBanners = Array.from(document.querySelectorAll(".alert-danger"), (banner) => `The page shows an error: ${banner.textContent?.trim()}`);
  if (errorBanners.length > 0) return { ok: false, errors: errorBanners };
  const form = document.querySelector<HTMLFormElement>("form[method=post]");
  if (!form) return { ok: false, errors: ["No lineup form on the page; the session may be logged out"] };
  const selects = Array.from(form.querySelectorAll<HTMLSelectElement>("select[name^=status]"));
  const lockedPlayers = getLockedPlayers(form);
  if (apiRoster) {
    const disagreements = findPageApiDisagreements(form, selects, lockedPlayers, apiRoster);
    if (disagreements.length > 0) return { ok: false, errors: disagreements };
  }

  const slotsBefore = new Map(selects.map((select) => [select, getSlotLabel(select)]));
  const problems: string[] = [];
  const warnings: string[] = [];
  const pageGlobals = {
    window,
    document,
    Event,
    MouseEvent: Event,
    // No page scripts run here, so hovering never shows a tooltip; resolving waits at once also means no other request can run while these globals are swapped in
    setTimeout: (callback: () => void) => queueMicrotask(callback),
    alert: (message: unknown) => problems.push(String(message)),
    console: withWarningsCollected(withoutDebugOutput(console), warnings),
  };
  // Once every player is locked there's nothing to set, and the page may not have a Save Lineup button for the extension to find
  const everyPlayerLocked = selects.length === 0;
  if (!everyPlayerLocked) {
    await withPageGlobals(pageGlobals, setLineup).catch((error) => {
      const message = error instanceof Error ? error.message : String(error);
      if (!problems.includes(message)) problems.push(message);
    });
  }
  if (problems.length > 0) return { ok: false, errors: problems };

  const startingSlots = getStartingSlots(document);
  if (startingSlots.length === 0) return { ok: false, errors: ["No starting slots (allPositions) in the page data; can't check the lineup"] };
  const selectsWithoutSlot = selects.filter((select) => select.value === "");
  if (selectsWithoutSlot.length > 0) return { ok: false, errors: selectsWithoutSlot.map((select) => `${getPlayerName(select)} has no slot chosen`) };
  const slotCountProblems = findSlotCountProblems(startingSlots, selects, lockedPlayers);
  if (slotCountProblems.length > 0) return { ok: false, errors: slotCountProblems };

  const fields = Array.from(form.querySelectorAll<HTMLInputElement | HTMLSelectElement>("input[name], select[name]"));
  const body = new URLSearchParams(fields.map((field) => [field.name, field.value])).toString();
  const starters = startingSlots.flatMap((slot): Starter[] => [
    ...lockedPlayers.filter((player) => player.slot === slot.name).map((player) => ({ player: player.name, slot: slot.name, locked: true as const })),
    ...selects.filter((select) => select.value === String(slot.mask)).map((select) => ({ player: getPlayerName(select), slot: slot.name })),
  ]);
  const changes = selects
    .filter((select) => getSlotLabel(select) !== slotsBefore.get(select))
    .map((select) => ({ player: getPlayerName(select), from: slotsBefore.get(select)!, to: getSlotLabel(select) }));
  return { ok: true, formAction: form.getAttribute("action")!, body, starters, changes, warnings };
}

function findPageApiDisagreements(form: HTMLFormElement, selects: HTMLSelectElement[], lockedPlayers: LockedPlayer[], apiRoster: ApiRoster) {
  const pageDay = Number(form.querySelector<HTMLInputElement>("input[name=week]")?.value);
  const apiDay = apiRoster.lineupPeriod.ordinal;
  if (pageDay !== apiDay) return [`Page and API disagree: the page is day ${pageDay} but the API roster is day ${apiDay}`];
  const apiSlotsByPlayerId = new Map(apiRoster.groups.flatMap((group) => group.slots.flatMap((slot) => (slot.leaguePlayer ? [[slot.leaguePlayer.proPlayer.id, slot] as const] : []))));
  const pagePlayerIds = new Set([...selects.map(getPlayerId), ...lockedPlayers.map((player) => player.id)]);
  const apiOnly = [...apiSlotsByPlayerId.entries()].filter(([id]) => !pagePlayerIds.has(id)).map(([, slot]) => slot.leaguePlayer!.proPlayer.nameFull);
  return [
    ...apiOnly.map((name) => `Page and API disagree: ${name} is in the API roster but not on the page`),
    ...lockedPlayers.flatMap((player) => {
      const apiSlot = apiSlotsByPlayerId.get(player.id);
      const pageSlot = toApiSlotLabel(player.slot);
      if (!apiSlot) return [`Page and API disagree: ${player.name} (locked) is on the page but not in the API roster`];
      return pageSlot === apiSlot.position.label ? [] : [`Page and API disagree: ${player.name} (locked) is in ${pageSlot} on the page but ${apiSlot.position.label} in the API`];
    }),
    ...selects.flatMap((select) => {
      const name = getPlayerName(select);
      const apiSlot = apiSlotsByPlayerId.get(getPlayerId(select));
      if (!apiSlot) return [`Page and API disagree: ${name} is on the page but not in the API roster`];
      const pageEligibility = Array.from(select.querySelectorAll("option"), (option) => toApiSlotLabel(option.textContent ?? "")).sort().join(", ");
      const apiEligibility = apiSlot.leaguePlayer!.eligibleFor.map((slot) => slot.label).sort().join(", ");
      const pageSlot = toApiSlotLabel(getSlotLabel(select));
      return [
        ...(pageEligibility === apiEligibility ? [] : [`Page and API disagree: ${name} can go in ${pageEligibility} on the page but ${apiEligibility} in the API`]),
        ...(pageSlot === apiSlot.position.label ? [] : [`Page and API disagree: ${name} is in ${pageSlot} on the page but ${apiSlot.position.label} in the API`]),
      ];
    }),
  ];
}

// The server saves an under-filled lineup without complaint, and rejects the whole save when a slot is over-filled (e.g. around a locked starter)
function findSlotCountProblems(startingSlots: LineupSlot[], selects: HTMLSelectElement[], lockedPlayers: LockedPlayer[]) {
  const benchSelects = selects.filter((select) => select.value === BENCH_VALUE);
  return startingSlots.flatMap((slot) => {
    const starters = [
      ...lockedPlayers.filter((player) => player.slot === slot.name).map((player) => `${player.name} (locked)`),
      ...selects.filter((select) => select.value === String(slot.mask)).map(getPlayerName),
    ];
    if (starters.length > slot.numStart) return [`${slot.name} slot is over-filled (${starters.length}/${slot.numStart}): ${starters.join(", ")}`];
    if (starters.length === slot.numStart) return [];
    const eligibleBenchPlayers = benchSelects.filter((select) => select.querySelector(`option[value="${slot.mask}"]`)).map(getPlayerName);
    if (eligibleBenchPlayers.length === 0) return [];
    return [`${slot.name} slot is empty (${starters.length}/${slot.numStart} filled) while eligible players sit on the bench: ${eligibleBenchPlayers.join(", ")}`];
  });
}

// A locked player's row has no select, just his slot's label in the last cell
function getLockedPlayers(form: HTMLFormElement): LockedPlayer[] {
  const playerRows = Array.from(form.querySelectorAll("tr")).filter((row) => row.querySelector(".player-text"));
  return playerRows
    .filter((row) => !row.querySelector("select"))
    .map((row) => {
      const playerLink = row.querySelector(".player-text")!;
      const id = Number(playerLink.getAttribute("href")?.match(/-(\d+)$/)?.[1]);
      return { id, name: playerLink.textContent ?? "", slot: row.lastElementChild?.textContent?.trim() ?? "" };
    });
}

function getStartingSlots(document: Document): LineupSlot[] {
  const pageDataScript = document.getElementById("page-data")?.textContent ?? "";
  const pageDataJson = pageDataScript.match(/window\.pageData\s*=\s*(\{.*?\});/s)?.[1];
  const allPositions: LineupSlot[] = pageDataJson ? (JSON.parse(pageDataJson).allPositions ?? []) : [];
  return allPositions.filter((slot) => slot.group === "START");
}

function toApiSlotLabel(pageLabel: string) {
  return PAGE_TO_API_SLOT_LABEL[pageLabel] ?? pageLabel;
}

function getSlotLabel(select: HTMLSelectElement) {
  return select.selectedOptions[0]?.textContent ?? "";
}

function getPlayerId(select: HTMLSelectElement) {
  return Number(select.name.replace("status", ""));
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

function withWarningsCollected(console: Console, warnings: string[]): Console {
  return new Proxy(console, {
    get(target, key) {
      if (key === "warn") return (...args: unknown[]) => warnings.push(args.map(String).join(" "));
      return Reflect.get(target, key);
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
  const selectsSetToNoOption = new WeakSet<HTMLSelectElement>();
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
      const selected = this.querySelector("option[selected]") ?? (selectsSetToNoOption.has(this) ? null : this.querySelector("option"));
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
      if (!this.querySelector("option[selected]")) selectsSetToNoOption.add(this);
    },
  });
}
