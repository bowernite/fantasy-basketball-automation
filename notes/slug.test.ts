import { expect, test } from "bun:test";
import { slugify } from "./slug";

test("lowercases", () => {
  expect(slugify("Hello")).toBe("hello");
});

test("turns spaces into hyphens", () => {
  expect(slugify("hello big world")).toBe("hello-big-world");
});

test("strips punctuation", () => {
  expect(slugify("Hello, World! It's 2026.")).toBe("hello-world-its-2026");
});
