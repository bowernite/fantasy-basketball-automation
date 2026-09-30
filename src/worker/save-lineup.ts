import { parseHTML } from "linkedom";
import type { LineupDecision } from "./decide-lineup";

const FLEAFLICKER_ORIGIN = "https://www.fleaflicker.com";
const SAVED_MESSAGE = "Lineup set successfully.";

export type SaveResult = { posted: boolean; problems: string[] };

export async function saveLineup(decision: Extract<LineupDecision, { ok: true }>, sessionHeaders: Record<string, string>): Promise<SaveResult> {
  if (decision.changes.length === 0) return { posted: false, problems: [] };
  const lineupUrl = `${FLEAFLICKER_ORIGIN}${decision.formAction}`;
  // The save can land even when its response is lost, so the reload below runs either way
  const problems = await fetch(lineupUrl, {
    method: "POST",
    headers: { ...sessionHeaders, "Content-Type": "application/x-www-form-urlencoded", Origin: FLEAFLICKER_ORIGIN, Referer: lineupUrl },
    body: decision.body,
    redirect: "manual",
  }).then(checkSaveResponse, (error) => [`Lineup save request failed: ${error}`]);
  const postedFields = new URLSearchParams(decision.body);
  const verifyProblems = await fetch(`${lineupUrl}?statType=0&week=${postedFields.get("week")}`, { headers: sessionHeaders }).then(
    (reload) => verifyReload(reload, postedFields),
    (error) => [`Couldn't verify the save: ${error}`],
  );
  problems.push(...verifyProblems);
  return { posted: true, problems };
}

async function verifyReload(reload: Response, postedFields: URLSearchParams) {
  if (reload.status !== 200) return [`Couldn't verify the save: reloading the lineup page returned HTTP ${reload.status}`];
  const html = await reload.text();
  if (!html.includes('href="/logout"')) return ["Couldn't verify the save: the reloaded lineup page is signed out"];
  const { document } = parseHTML(html);
  const reloadedDay = document.querySelector("input[name=week]")?.getAttribute("value");
  const postedDay = postedFields.get("week");
  if (reloadedDay !== postedDay) return [`Couldn't verify the save: the reloaded lineup page is day ${reloadedDay}, not day ${postedDay}`];
  return findUnsavedSlots(document, postedFields);
}

function findUnsavedSlots(document: Document, postedFields: URLSearchParams) {
  const postedSlots = [...postedFields].filter(([name]) => name.startsWith("status"));
  return postedSlots.flatMap(([name, postedValue]) => {
    const select = document.querySelector(`select[name="${name}"]`);
    if (!select) {
      const playerId = name.slice("status".length);
      const player = document.querySelector(`a[href$="-${playerId}"]`)?.textContent ?? `player ${playerId}`;
      return [`Couldn't verify ${player}'s slot: the reloaded page has no dropdown for them (locked or dropped?)`];
    }
    const savedOption = select.querySelector("option[selected]") ?? select.querySelector("option");
    if (savedOption?.getAttribute("value") === postedValue) return [];
    const player = select.closest("tr")?.querySelector(".player-text")?.textContent ?? name;
    const postedSlot = select.querySelector(`option[value="${postedValue}"]`)?.textContent ?? postedValue;
    return [`After saving, Fleaflicker shows ${player} in ${savedOption?.textContent}, not ${postedSlot}`];
  });
}

// An accepted save redirects with its message in `_gAlert`; a rejected one re-renders the page with an error banner
async function checkSaveResponse(response: Response) {
  if (response.status === 200) {
    const rejections = findErrorBanners(await response.text()).map((message) => `Fleaflicker rejected the lineup: ${message}`);
    if (rejections.length > 0) return rejections;
  }
  const location = response.headers.get("Location");
  const redirectAlert = location ? await readRedirectAlert(location) : undefined;
  if (redirectAlert === SAVED_MESSAGE) return [];
  const redirectTarget = location ? ` to ${new URL(location, FLEAFLICKER_ORIGIN).pathname}` : "";
  const alertText = redirectAlert ? `: ${redirectAlert}` : "";
  return [`Fleaflicker didn't confirm the save (HTTP ${response.status}${redirectTarget})${alertText}`];
}

// `_gAlert` is a base64url, zlib-compressed Java-serialized blob whose last string is the message
async function readRedirectAlert(location: string) {
  const encoded = new URL(location, FLEAFLICKER_ORIGIN).searchParams.get("_gAlert");
  if (!encoded) return undefined;
  const compressed = Uint8Array.from(atob(encoded.replaceAll("-", "+").replaceAll("_", "/")), (char) => char.charCodeAt(0));
  const serialized = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream("deflate"))).text();
  return serialized.split(/[\x00-\x1f]/).at(-1);
}

function findErrorBanners(html: string) {
  const { document } = parseHTML(html);
  return Array.from(document.querySelectorAll(".alert-danger"), (banner) => banner.textContent?.trim() ?? "");
}
