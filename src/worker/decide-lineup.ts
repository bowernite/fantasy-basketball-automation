import { parseHTML } from "linkedom";
import { setLineup } from "../lineup/set-lineup";

export type LineupDecision =
  | { ok: true; formAction: string; body: string }
  | { ok: false; errors: string[] };

export async function decideLineup(html: string): Promise<LineupDecision> {
  const { document, Event } = parseHTML(html);
  addMissingFormControlBehavior(document);
  const form = document.querySelector<HTMLFormElement>("form[method=post]");
  if (!form) return { ok: false, errors: ["No lineup form on the page; the session may be logged out"] };

  const problems: string[] = [];
  // setLineup alerts every error before rethrowing it, so the alert already collected it
  await withPageGlobals({ document, Event, alert: (message: unknown) => problems.push(String(message)) }, setLineup).catch(() => {});
  if (problems.length > 0) return { ok: false, errors: problems };

  const fields = Array.from(form.querySelectorAll<HTMLInputElement | HTMLSelectElement>("input[name], select[name]"));
  const body = new URLSearchParams(fields.map((field) => [field.name, field.value])).toString();
  return { ok: true, formAction: form.getAttribute("action")!, body };
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
