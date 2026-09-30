import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { test, setSystemTime, spyOn } from "bun:test";
test("probe", async () => {
  const { loadLineupPage, PAGE_URL, playerRows } = await import("./src/lineup/fixtures/lineup-page");
  GlobalRegistrator.register({ url: PAGE_URL, settings: { disableJavaScriptFileLoading: true, disableCSSFileLoading: true, handleDisabledFileLoadingAsSuccess: true } });
  setSystemTime(new Date("2026-10-20T14:00:00Z"));
  for (const m of ["log","table","warn","clear"] as const) spyOn(console, m).mockImplementation(() => {});
  spyOn(window, "alert").mockImplementation((m) => console.error("ALERT", m));
  loadLineupPage();
  const withNews = playerRows().filter(r => r.querySelector(".fa-file-text")).map(r => [r.querySelector(".player-text")!.textContent, r.querySelector(".fa-file-text")!.closest("a,span")!.outerHTML.slice(0,300)]);
  console.error("NEWS", withNews);
  await import("./page-load__set-lineup.ts");
  await Bun.sleep(50);
  for (const r of playerRows()) {
    const b = r.querySelector("[data-predicted-score]") as HTMLElement;
    console.error(r.querySelector(".player-text")!.textContent, "|", b?.textContent, "|", b?.style.visibility, "|", JSON.stringify(b?.title), "| base", r.querySelector("[data-base-score]")?.textContent, "| inj", r.querySelector(".injury")?.textContent, "| bg", r.cells[1]?.style.backgroundColor);
  }
});
