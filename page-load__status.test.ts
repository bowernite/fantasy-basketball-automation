import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, beforeEach, expect, setSystemTime, spyOn, test } from "bun:test";
import { givePlayerNews, loadLineupPage, PAGE_URL, playerRow } from "./src/lineup/fixtures/lineup-page";
import { getPlayerStatusFromRow } from "./src/page/player-status";
import { HAPPY_DOM_SETTINGS, recordAlerts, runContentScript } from "./src/lineup/fixtures/content-script";

beforeAll(() => GlobalRegistrator.register({ url: PAGE_URL, settings: HAPPY_DOM_SETTINGS }));
afterAll(() => {
  setSystemTime();
  GlobalRegistrator.unregister();
});

beforeEach(() => {
  setSystemTime(new Date("2026-10-20T14:00:00Z"));
  for (const method of ["log", "table", "clear", "warn"] as const) spyOn(console, method).mockImplementation(() => {});
  recordAlerts();
});

const BONA_PROBABLE_NEWS =
  '<div class="news-text"><h5>Adem Bona Probable Tuesday</h5>' +
  '<em><relative-time datetime="2026-10-20T12:00:00Z">Tue 10/20/26 8:00 AM</relative-time></em>' +
  "<p>Philadelphia 76ers center Adem Bona (knee) is probable for Tuesday's game against the Knicks.</p></div>";

test("injury news that upgrades an OUT player shows the new status and the news' age", async () => {
  loadLineupPage();
  givePlayerNews("Adem Bona", BONA_PROBABLE_NEWS);

  await runContentScript();

  expect(statusAfterName("Adem Bona")?.textContent).toMatchInlineSnapshot(`"Probable 2h"`);
});

test("a refined status hides Fleaflicker's own tag but leaves it for setting the lineup to read", async () => {
  loadLineupPage();
  givePlayerNews("Adem Bona", BONA_PROBABLE_NEWS);

  await runContentScript();

  const nativeTag = playerRow("Adem Bona").querySelector<HTMLElement>(".injury")!;
  expect(getComputedStyle(nativeTag).display).toBe("none");
  expect(getPlayerStatusFromRow(playerRow("Adem Bona"))).toBe("OUT");
});

test("refined statuses read as words, risks in orange", async () => {
  loadLineupPage();
  givePlayerNews("Adem Bona", newsSaying("Adem Bona is probable for Tuesday's game"));
  givePlayerNews("Shaedon Sharpe", newsSaying("Shaedon Sharpe is questionable for Tuesday's game"));
  givePlayerNews("Mark Williams", newsSaying("Mark Williams is doubtful for Tuesday's game"));
  givePlayerNews("Kyrie Irving", newsSaying("Kyrie Irving will not play Tuesday"));
  givePlayerNews("Zach Edey", newsSaying("Zach Edey has been cleared to play Tuesday"));

  await runContentScript();

  const shown = ["Adem Bona", "Shaedon Sharpe", "Mark Williams", "Kyrie Irving", "Zach Edey"].map((name) => {
    const tag = statusAfterName(name) as HTMLElement | undefined;
    return `${name}: ${tag?.textContent} (${tag && getComputedStyle(tag).color})`;
  });
  expect(shown).toMatchInlineSnapshot(`
    [
      "Adem Bona: Probable 1h (#5F6A77)",
      "Shaedon Sharpe: Questionable 1h (#A84A00)",
      "Mark Williams: Doubtful 1h (#A84A00)",
      "Kyrie Irving: Out 1h (#A84A00)",
      "Zach Edey: Available 1h (#26313D)",
    ]
  `);
});

test("running again on the same page shows the status once", async () => {
  loadLineupPage();
  givePlayerNews("Adem Bona", BONA_PROBABLE_NEWS);

  await runContentScript();
  await runContentScript();

  expect(playerRow("Adem Bona").querySelectorAll(".ffx-status")).toHaveLength(1);
});

test("without news, Fleaflicker's own tag stays as is, in orange", async () => {
  loadLineupPage();

  await runContentScript();

  const nativeTag = playerRow("Kyrie Irving").querySelector<HTMLElement>(".injury")!;
  expect(nativeTag.textContent).toBe("OFS");
  expect(getComputedStyle(nativeTag).color).toBe("#A84A00");
  expect(statusAfterName("Kyrie Irving")).toBeUndefined();
});

function newsSaying(sentence: string) {
  return (
    '<div class="news-text"><em><relative-time datetime="2026-10-20T13:00:00Z">Tue 10/20/26 9:00 AM</relative-time></em>' +
    `<p>${sentence}.</p></div>`
  );
}

function statusAfterName(name: string) {
  const nextToName = playerRow(name).querySelector(".player-text")!.nextElementSibling;
  return nextToName?.classList.contains("ffx-status") ? nextToName : undefined;
}
