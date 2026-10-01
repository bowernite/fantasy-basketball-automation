import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, expect, test } from "bun:test";
import { loadLineupPage, PAGE_URL } from "../../lineup/fixtures/lineup-page";
import { HAPPY_DOM_SETTINGS } from "../../lineup/fixtures/content-script";
import { showNotice } from "./notice";

beforeAll(() => GlobalRegistrator.register({ url: PAGE_URL, settings: HAPPY_DOM_SETTINGS }));
afterAll(() => GlobalRegistrator.unregister());

function rosterForm() {
  return document.querySelector("form[method='post']")!;
}

test("an error shows as an alert right above the roster", () => {
  loadLineupPage();

  showNotice({ kind: "error", message: "Couldn't set the lineup" });

  const notice = document.querySelector("[role=alert]")!;
  expect(notice.textContent).toContain("Couldn't set the lineup");
  expect(notice.compareDocumentPosition(rosterForm()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(document.querySelectorAll("[role=alert]")).toHaveLength(1);
});

test("a new notice replaces the last one; info is a polite status, not an alert", () => {
  loadLineupPage();

  showNotice({ kind: "error", message: "Couldn't set the lineup" });
  showNotice({ kind: "info", message: "Lineup set" });

  expect(document.querySelectorAll("[role=alert]")).toHaveLength(0);
  expect(Array.from(document.querySelectorAll("[role=status]"), (n) => n.textContent)).toEqual([
    expect.stringContaining("Lineup set"),
  ]);
});

test("without Fleaflicker's message box, the notice still lands right above the roster form", () => {
  loadLineupPage();
  document.getElementById("statusBox")!.remove();

  showNotice({ kind: "error", message: "Couldn't set the lineup" });

  expect(rosterForm().previousElementSibling!.getAttribute("role")).toBe("alert");
});

test("on a page without the roster form, the notice goes at the top of the roster area", () => {
  loadLineupPage({ loggedIn: false });

  showNotice({ kind: "error", message: "Couldn't save the lineup" });

  expect(document.getElementById("body-center-main")!.firstElementChild!.getAttribute("role")).toBe("alert");
});

test("a notice can offer the next step as a button", () => {
  loadLineupPage();
  const clicks: string[] = [];
  showNotice({ kind: "error", message: "Couldn't set the lineup", action: { label: "Retry", onClick: () => clicks.push("retry") } });

  Array.from(document.querySelectorAll("[role=alert] button")).find((b) => b.textContent === "Retry")!.click();

  expect(clicks).toEqual(["retry"]);
});

test("Dismiss closes the notice", () => {
  loadLineupPage();
  showNotice({ kind: "warning", message: "Couldn't read Naz Reid's score" });

  document.querySelector<HTMLButtonElement>("button[aria-label=Dismiss]")!.click();

  expect(document.querySelector("[role=alert]")).toBeNull();
});
