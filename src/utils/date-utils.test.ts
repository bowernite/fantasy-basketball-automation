import { GlobalRegistrator } from "@happy-dom/global-registrator";
import {
  afterAll,
  afterEach,
  beforeAll,
  describe,
  expect,
  setSystemTime,
  test,
} from "bun:test";
import { getNumDaysInFuture, parseDateFromText } from "./date-utils";

const originalTZ = process.env.TZ;

beforeAll(() => GlobalRegistrator.register());
afterAll(() => {
  GlobalRegistrator.unregister();
  process.env.TZ = originalTZ;
});
afterEach(() => setSystemTime());

function ymd(date: Date | null) {
  return date && [date.getFullYear(), date.getMonth() + 1, date.getDate()];
}

describe("parseDateFromText (year of the viewed day)", () => {
  test("a date with a 2-digit year uses that year", () => {
    const now = new Date(2026, 11, 30);
    expect(ymd(parseDateFromText("12/30/25", now))).toEqual([2025, 12, 30]);
    expect(ymd(parseDateFromText("1/2/27", now))).toEqual([2027, 1, 2]);
  });

  test("a date without a year is in the current year mid-season", () => {
    expect(ymd(parseDateFromText("11/5", new Date(2026, 10, 20)))).toEqual([2026, 11, 5]);
    expect(ymd(parseDateFromText("2/14", new Date(2027, 1, 10)))).toEqual([2027, 2, 14]);
  });

  test("viewing early January from late December rolls into next year", () => {
    expect(ymd(parseDateFromText("1/2", new Date(2026, 11, 28)))).toEqual([2027, 1, 2]);
  });

  test("viewing late December from early January rolls into previous year", () => {
    expect(ymd(parseDateFromText("12/30", new Date(2027, 0, 3)))).toEqual([2026, 12, 30]);
  });

  test("finds the date inside surrounding text", () => {
    expect(ymd(parseDateFromText("Fri 3/7", new Date(2026, 2, 1)))).toEqual([2026, 3, 7]);
  });

  test("returns null when there is no date", () => {
    expect(parseDateFromText("Today", new Date(2026, 2, 1))).toBeNull();
    expect(parseDateFromText("", new Date(2026, 2, 1))).toBeNull();
  });
});

describe("getNumDaysInFuture (viewed day vs. today)", () => {
  function viewDay(dateButtonText: string, now: Date) {
    setSystemTime(now);
    document.body.innerHTML = `<a class="btn" data-toggle="dropdown">${dateButtonText}</a>`;
    return getNumDaysInFuture();
  }

  test("is 0 for today regardless of time of day", () => {
    process.env.TZ = "America/Chicago";
    expect(viewDay("Today", new Date(2026, 9, 30, 21, 45))).toBe(0);
    expect(viewDay("10/30", new Date(2026, 9, 30, 21, 45))).toBe(0);
  });

  test("is 1 for tomorrow and -1 for yesterday", () => {
    process.env.TZ = "America/Chicago";
    const now = new Date(2026, 9, 30, 15, 0);
    expect(viewDay("10/31", now)).toBe(1);
    expect(viewDay("10/29", now)).toBe(-1);
  });

  test("counts across a year boundary", () => {
    process.env.TZ = "America/Chicago";
    expect(viewDay("1/2", new Date(2026, 11, 30, 10, 0))).toBe(3);
  });

  test("counts from the league's (Central time) today on a machine running in UTC", () => {
    process.env.TZ = "UTC";
    // 9:30pm CT on 10/29 is already 10/30 in UTC
    const lateEveningInChicago = new Date("2026-10-30T02:30:00Z");
    expect(viewDay("10/29", lateEveningInChicago)).toBe(0);
    expect(viewDay("10/30", lateEveningInChicago)).toBe(1);
    expect(viewDay("Today", lateEveningInChicago)).toBe(0);
  });

  test("counts whole days across the spring-forward DST change (a 23h day)", () => {
    process.env.TZ = "America/Chicago";
    // DST starts Sun 2026-03-08 at 2am in Chicago, so Mar 8 -> Mar 9 is only 23h long
    expect(viewDay("3/8", new Date(2026, 2, 7, 12, 0))).toBe(1);
    expect(viewDay("3/9", new Date(2026, 2, 7, 12, 0))).toBe(2);
  });

  test("counts whole days across the fall-back DST change (a 25h day)", () => {
    process.env.TZ = "America/Chicago";
    expect(viewDay("11/2", new Date(2026, 10, 1, 12, 0))).toBe(1);
    expect(viewDay("11/3", new Date(2026, 10, 1, 12, 0))).toBe(2);
  });
});
