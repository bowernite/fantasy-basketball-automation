import { parseHTML } from "linkedom";
import { afterEach, describe, expect, it, vi } from "vitest";
import openingNightPage from "../lineup/fixtures/teampage-logged-in-fantasy-stats.html?raw";
import { decideLineup } from "./decide-lineup";
import { saveLineup } from "./save-lineup";

const SESSION = { Cookie: "cookieId=test-session" };
// Captured from a real accepted save; its `_gAlert` decodes to "Lineup set successfully."
const ACCEPTED_SAVE_LOCATION =
  "https://www.fleaflicker.com/nba/leagues/30579/teams/161025?_fm=eJxjYGBc8IX3_mFGAAzsA0Y&week=1&_gAlert=eJxjYGBc8IX3_uE1bxlYyxUYGMFQwiczL7W0QKE4tUShuDQ5ObW4OK00J6dSDwBMBA7h";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("saving a decided lineup", () => {
  it("posts the lineup and confirms the reloaded page shows it", async () => {
    const decision = await decideOpeningNight();
    const fleaflicker = fakeFleaflicker();

    const result = await saveLineup(decision, SESSION);

    expect(result).toMatchObject({ posted: true, problems: [] });
    expect(slotsOnPage(fleaflicker.page)).toEqual(slotsInBody(decision.body));
  });

  it("doesn't post when the lineup is already set", async () => {
    const alreadySetPage = withSlots(openingNightPage, slotsInBody((await decideOpeningNight()).body));
    const decision = await decideLineup(alreadySetPage);
    if (!decision.ok) throw new Error(decision.errors.join("\n"));
    const fleaflicker = fakeFleaflicker();

    const result = await saveLineup(decision, SESSION);

    expect(result).toEqual({ posted: false, problems: [] });
    expect(fleaflicker.posts).toEqual([]);
  });
});

async function decideOpeningNight() {
  const decision = await decideLineup(openingNightPage);
  if (!decision.ok) throw new Error(decision.errors.join("\n"));
  return decision;
}

// Serves the lineup page and saves posted lineups onto it, like Fleaflicker does for a signed-in owner
function fakeFleaflicker() {
  const fleaflicker = { page: openingNightPage, posts: [] as string[] };
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const request = new Request(input, init);
    if (new URL(request.url).host !== "www.fleaflicker.com") throw new Error(`Unexpected fetch: ${request.url}`);
    if (request.method === "GET") return new Response(fleaflicker.page);
    const body = await request.text();
    fleaflicker.posts.push(body);
    fleaflicker.page = withSlots(fleaflicker.page, slotsInBody(body));
    return new Response(null, { status: 303, headers: { Location: ACCEPTED_SAVE_LOCATION } });
  });
  return fleaflicker;
}

function slotsInBody(body: string) {
  return Object.fromEntries([...new URLSearchParams(body)].filter(([name]) => name.startsWith("status")));
}

function slotsOnPage(html: string) {
  const { document } = parseHTML(html);
  return Object.fromEntries(
    Array.from(document.querySelectorAll("select[name^=status]"), (select) => [select.getAttribute("name"), select.querySelector("option[selected]")?.getAttribute("value")]),
  );
}

function withSlots(html: string, slots: Record<string, string>) {
  const { document } = parseHTML(html);
  for (const [name, value] of Object.entries(slots)) {
    for (const option of document.querySelectorAll(`select[name="${name}"] option`)) option.toggleAttribute("selected", option.getAttribute("value") === value);
  }
  return document.toString();
}
