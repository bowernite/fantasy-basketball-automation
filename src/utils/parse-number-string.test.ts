import { expect, test } from "bun:test";
import { parseNumberString } from "./parse-number-string";

test("parses numbers with thousands separators and decimals", () => {
  expect(parseNumberString("1,234.5")).toBe(1234.5);
  expect(parseNumberString("1,234,567")).toBe(1234567);
  expect(parseNumberString("42.3")).toBe(42.3);
});

test("returns null for missing or empty text", () => {
  expect(parseNumberString(undefined)).toBeNull();
  expect(parseNumberString(null)).toBeNull();
  expect(parseNumberString("")).toBeNull();
});
