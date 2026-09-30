import { parseHTML } from "linkedom";
import { afterEach, describe, expect, it, vi } from "vitest";
import signedOutPage from "../lineup/fixtures/teampage.html?raw";
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

  it("reports Fleaflicker's reason when it rejects the lineup", async () => {
    const decision = await decideOpeningNight();
    // A rejected save re-renders the page with the error and the rejected values, and saves nothing
    fakeFleaflicker({
      onSave: (fleaflicker, body) =>
        new Response(withErrorBanner(withSlots(fleaflicker.page, slotsInBody(body)), "You cannot assign more than 1 to the PG position (Cade Cunningham, Desmond Bane).")),
    });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems).toMatchInlineSnapshot(`
      [
        "Fleaflicker rejected the lineup: You cannot assign more than 1 to the PG position (Cade Cunningham, Desmond Bane).",
        "After saving, Fleaflicker shows Naz Reid in C, not Bench",
        "After saving, Fleaflicker shows John Collins in F/C, not C",
        "After saving, Fleaflicker shows Neemias Queta in ANY, not F/C",
        "After saving, Fleaflicker shows Josh Giddey in Bench, not ANY",
      ]
    `);
  });

  it("reports players the reloaded page doesn't show where the save put them", async () => {
    const decision = await decideOpeningNight();
    const [firstMove] = Object.entries(slotsInBody(decision.body)).filter(([name, value]) => slotsOnPage(openingNightPage)[name] !== value);
    fakeFleaflicker({
      onSave: (fleaflicker, body) => {
        const response = acceptSave(fleaflicker, body);
        fleaflicker.page = withSlots(fleaflicker.page, { [firstMove[0]]: slotsOnPage(openingNightPage)[firstMove[0]]! });
        return response;
      },
    });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems).toMatchInlineSnapshot(`
      [
        "After saving, Fleaflicker shows Naz Reid in C, not Bench",
      ]
    `);
  });

  it("reports a save Fleaflicker didn't confirm", async () => {
    const decision = await decideOpeningNight();
    fakeFleaflicker({ onSave: () => new Response(null, { status: 303, headers: { Location: "https://www.fleaflicker.com/nba/login" } }) });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems[0]).toMatchInlineSnapshot(`"Fleaflicker didn't confirm the save (HTTP 303 to /nba/login)"`);
  });

  it("still checks the reloaded page when the save's response is lost", async () => {
    const decision = await decideOpeningNight();
    fakeFleaflicker({
      onSave: (fleaflicker, body) => {
        acceptSave(fleaflicker, body);
        throw new TypeError("Network connection lost");
      },
    });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems).toMatchInlineSnapshot(`
      [
        "Lineup save request failed: TypeError: Network connection lost",
      ]
    `);
  });

  it("still checks the reloaded page when the save's response can't be read", async () => {
    const decision = await decideOpeningNight();
    fakeFleaflicker({
      onSave: () => new Response(null, { status: 303, headers: { Location: "https://www.fleaflicker.com/nba/leagues/30579/teams/161025?week=1&_gAlert=not-a-real-alert" } }),
    });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems).toMatchInlineSnapshot(`
      [
        "Couldn't read Fleaflicker's save response: TypeError: Decompression failed.",
        "After saving, Fleaflicker shows Naz Reid in C, not Bench",
        "After saving, Fleaflicker shows John Collins in F/C, not C",
        "After saving, Fleaflicker shows Neemias Queta in ANY, not F/C",
        "After saving, Fleaflicker shows Josh Giddey in Bench, not ANY",
      ]
    `);
  });

  it("reports an unverified save when the reloaded page is signed out", async () => {
    const decision = await decideOpeningNight();
    fakeFleaflicker({
      onSave: (fleaflicker, body) => {
        const response = acceptSave(fleaflicker, body);
        fleaflicker.page = signedOutPage;
        return response;
      },
    });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems).toMatchInlineSnapshot(`
      [
        "Couldn't verify the save: the reloaded lineup page is signed out",
      ]
    `);
  });

  it("reports an unverified save when the reload fails", async () => {
    const decision = await decideOpeningNight();
    fakeFleaflicker({ onReload: () => new Response("<html><body>Service Unavailable</body></html>", { status: 503 }) });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems).toMatchInlineSnapshot(`
      [
        "Couldn't verify the save: reloading the lineup page returned HTTP 503",
      ]
    `);
  });

  it("reports an unverified save when the reload shows a different day", async () => {
    const decision = await decideOpeningNight();
    fakeFleaflicker({ onReload: (fleaflicker) => new Response(fleaflicker.page.replace('name="week" value="1"', 'name="week" value="2"')) });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems).toMatchInlineSnapshot(`
      [
        "Couldn't verify the save: the reloaded lineup page is day 2, not day 1",
      ]
    `);
  });

  it("reports a moved player the reloaded page has no dropdown for", async () => {
    const decision = await decideOpeningNight();
    const [firstMove] = Object.entries(slotsInBody(decision.body)).filter(([name, value]) => slotsOnPage(openingNightPage)[name] !== value);
    fakeFleaflicker({ onReload: (fleaflicker) => new Response(withoutSelect(fleaflicker.page, firstMove[0])) });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems).toMatchInlineSnapshot(`
      [
        "Couldn't verify Naz Reid's slot: the reloaded page has no dropdown for them (locked or dropped?)",
      ]
    `);
  });

  it("reports an unverified save when the reloaded page can't be read", async () => {
    const decision = await decideOpeningNight();
    const brokenBody = new ReadableStream({
      start: (controller) => controller.error(new TypeError("Body stream broke")),
    });
    fakeFleaflicker({ onReload: () => new Response(brokenBody) });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems).toMatchInlineSnapshot(`
      [
        "Couldn't verify the save: TypeError: Body stream broke",
      ]
    `);
  });

  it("reports an unverified save when the reload request fails", async () => {
    const decision = await decideOpeningNight();
    fakeFleaflicker({
      onReload: () => {
        throw new TypeError("Network connection lost");
      },
    });

    const result = await saveLineup(decision, SESSION);

    expect(result.problems).toMatchInlineSnapshot(`
      [
        "Couldn't verify the save: TypeError: Network connection lost",
      ]
    `);
  });
});

async function decideOpeningNight() {
  const decision = await decideLineup(openingNightPage);
  if (!decision.ok) throw new Error(decision.errors.join("\n"));
  return decision;
}

// Serves the lineup page and saves posted lineups onto it, like Fleaflicker does for a signed-in owner
function fakeFleaflicker({
  onSave = acceptSave,
  onReload = (fleaflicker) => new Response(fleaflicker.page),
}: { onSave?: (fleaflicker: FakeFleaflicker, body: string) => Response; onReload?: (fleaflicker: FakeFleaflicker) => Response } = {}) {
  const fleaflicker: FakeFleaflicker = { page: openingNightPage, posts: [] };
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const request = new Request(input, init);
    if (new URL(request.url).host !== "www.fleaflicker.com") throw new Error(`Unexpected fetch: ${request.url}`);
    if (request.method === "GET") return onReload(fleaflicker);
    const body = await request.text();
    fleaflicker.posts.push(body);
    return onSave(fleaflicker, body);
  });
  return fleaflicker;
}

type FakeFleaflicker = { page: string; posts: string[] };

function acceptSave(fleaflicker: FakeFleaflicker, body: string) {
  fleaflicker.page = withSlots(fleaflicker.page, slotsInBody(body));
  return new Response(null, { status: 303, headers: { Location: ACCEPTED_SAVE_LOCATION } });
}

function withErrorBanner(html: string, message: string) {
  return html.replace('<form action="/nba/leagues', `<div class="alert alert-danger">${message}</div><form action="/nba/leagues`);
}

function withoutSelect(html: string, name: string) {
  const { document } = parseHTML(html);
  document.querySelector(`select[name="${name}"]`)!.remove();
  return document.toString();
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
