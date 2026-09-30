import { GlobalRegistrator } from "@happy-dom/global-registrator";
import { afterAll, beforeAll, expect, test } from "bun:test";
import { getPageDate, getPlayersTable } from "./page-querying";

beforeAll(() => GlobalRegistrator.register());
afterAll(() => GlobalRegistrator.unregister());

function errorFrom(fn: () => unknown) {
  try {
    fn();
  } catch (error) {
    return (error as Error).message;
  }
}

test("a page with no date dropdown throws an error saying none were found", () => {
  document.body.innerHTML = "<table></table>";

  expect(errorFrom(getPageDate)).toMatchInlineSnapshot(
    `"Tried to get page date but found 0 date buttons"`
  );
});

test("a page with two date dropdowns throws an error saying two were found", () => {
  document.body.innerHTML = `
    <a class="btn" data-toggle="dropdown">Today</a>
    <a class="btn" data-toggle="dropdown">1/18</a>`;

  expect(errorFrom(getPageDate)).toMatchInlineSnapshot(
    `"Tried to get page date but found 2 date buttons"`
  );
});

test("a page with several tables throws an error with the table count", () => {
  document.body.innerHTML = "<table></table><table></table>";

  expect(errorFrom(getPlayersTable)).toMatchInlineSnapshot(
    `"Expected exactly one table but found 2"`
  );
});
