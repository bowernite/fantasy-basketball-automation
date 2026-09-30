import { expect, test } from "bun:test";
import { interpolateColors } from "./interpolate-colors";

const black = "rgb(0, 0, 0)";
const white = "rgb(200, 100, 50)";

test("returns the start color at 0 and the end color at 1", () => {
  expect(interpolateColors({ start: black, end: white }, 0)).toBe(black);
  expect(interpolateColors({ start: black, end: white }, 1)).toBe(white);
});

test("blends each channel linearly and rounds", () => {
  expect(interpolateColors({ start: black, end: white }, 0.5)).toBe("rgb(100, 50, 25)");
  expect(interpolateColors({ start: black, end: white }, 0.25)).toBe("rgb(50, 25, 13)");
});

test("hits each color stop exactly at its percentage", () => {
  const colors = {
    start: black,
    end: white,
    stops: [{ color: "rgb(10, 20, 30)", percentage: 0.5 }],
  };
  expect(interpolateColors(colors, 0.5)).toBe("rgb(10, 20, 30)");
  expect(interpolateColors(colors, 0)).toBe(black);
  expect(interpolateColors(colors, 1)).toBe(white);
});

test("blends only between the two neighboring stops", () => {
  const colors = {
    start: "rgb(0, 0, 0)",
    end: "rgb(255, 255, 255)",
    stops: [
      { color: "rgb(100, 0, 0)", percentage: 0.25 },
      { color: "rgb(100, 100, 0)", percentage: 0.75 },
    ],
  };
  expect(interpolateColors(colors, 0.125)).toBe("rgb(50, 0, 0)");
  expect(interpolateColors(colors, 0.5)).toBe("rgb(100, 50, 0)");
  expect(interpolateColors(colors, 0.875)).toBe("rgb(178, 178, 128)");
});

test("stop order in the input does not matter", () => {
  const stops = [
    { color: "rgb(100, 0, 0)", percentage: 0.25 },
    { color: "rgb(100, 100, 0)", percentage: 0.75 },
  ];
  const base = { start: "rgb(0, 0, 0)", end: "rgb(255, 255, 255)" };
  expect(interpolateColors({ ...base, stops: [...stops].reverse() }, 0.5)).toBe(
    interpolateColors({ ...base, stops }, 0.5)
  );
});
