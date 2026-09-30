import { describe, expect, it } from "vitest";
import fantasyStatsPage from "../lineup/fixtures/teampage-logged-in-fantasy-stats.html?raw";
import { parseGameTips, planTick } from "./lineup-schedule";

describe("planTick", () => {
  it("runs today's lineup 40 min before an 8a tip", () => {
    const tipTables = [{ day: 3, fetchedAt: "2026-10-22T12:05:00Z", tips: [{ at: "2026-10-22T13:00:00Z", players: ["Cade Cunningham"] }] }];
    const ledger = [{ startedAt: "2026-10-22T12:05:00Z", ok: true, days: [3, 4] }];

    expect(planTick(new Date("2026-10-22T12:20:00Z"), 3, tipTables, ledger).runDays).toEqual([3]);
  });

  it("waits for the T-15 target once the T-40 run succeeded", () => {
    const tipTables = [{ day: 3, fetchedAt: "2026-10-22T12:20:00Z", tips: [{ at: "2026-10-22T13:00:00Z", players: ["Cade Cunningham"] }] }];
    const ledger = [
      { startedAt: "2026-10-22T12:05:00Z", ok: true, days: [3, 4] },
      { startedAt: "2026-10-22T12:20:00Z", ok: true, days: [3] },
    ];

    expect(planTick(new Date("2026-10-22T12:25:00Z"), 3, tipTables, ledger).runDays).toEqual([]);
    expect(planTick(new Date("2026-10-22T12:45:00Z"), 3, tipTables, ledger).runDays).toEqual([3]);
  });

  it("retries a failed T-15 run until 3 min before tip", () => {
    const tipTables = [{ day: 3, fetchedAt: "2026-10-22T12:20:00Z", tips: [{ at: "2026-10-22T13:00:00Z", players: ["Cade Cunningham"] }] }];
    const ledger = [
      { startedAt: "2026-10-22T12:05:00Z", ok: true, days: [3, 4] },
      { startedAt: "2026-10-22T12:20:00Z", ok: true, days: [3] },
      { startedAt: "2026-10-22T12:45:00Z", ok: false, days: [3] },
    ];

    expect(planTick(new Date("2026-10-22T12:50:00Z"), 3, tipTables, ledger).runDays).toEqual([3]);
    expect(planTick(new Date("2026-10-22T12:58:00Z"), 3, tipTables, ledger).runDays).toEqual([]);
  });

  it("runs today and tomorrow at :05 past every hour", () => {
    const tipTables = [{ day: 3, fetchedAt: "2026-10-22T13:05:00Z", tips: [] }];
    const ledger = [{ startedAt: "2026-10-22T13:05:00Z", ok: true, days: [3, 4] }];

    expect(planTick(new Date("2026-10-22T14:04:00Z"), 3, tipTables, ledger).runDays).toEqual([]);
    expect(planTick(new Date("2026-10-22T14:05:00Z"), 3, tipTables, ledger).runDays).toEqual([3, 4]);
  });

  it("still runs the hourly after a run that only covered today", () => {
    const tipTables = [{ day: 3, fetchedAt: "2026-10-22T13:05:00Z", tips: [] }];
    const ledger = [
      { startedAt: "2026-10-22T13:05:00Z", ok: true, days: [3, 4] },
      { startedAt: "2026-10-22T14:06:00Z", ok: true, days: [3] },
    ];

    expect(planTick(new Date("2026-10-22T14:10:00Z"), 3, tipTables, ledger).runDays).toEqual([3, 4]);
  });

  it("gives two tips 30 min apart their own T-40 and T-15 runs", () => {
    const tipTables = [
      {
        day: 3,
        fetchedAt: "2026-10-22T12:05:00Z",
        tips: [
          { at: "2026-10-22T13:00:00Z", players: ["Cade Cunningham"] },
          { at: "2026-10-22T13:30:00Z", players: ["Naz Reid"] },
        ],
      },
    ];
    const hourlyRun = { startedAt: "2026-10-22T12:05:00Z", ok: true, days: [3, 4] };
    const tipRunsAt = (...times: string[]) => times.map((time) => ({ startedAt: `2026-10-22T${time}:00Z`, ok: true, days: [3] }));

    expect(planTick(new Date("2026-10-22T12:20:00Z"), 3, tipTables, [hourlyRun]).runDays).toEqual([3]);
    expect(planTick(new Date("2026-10-22T12:45:00Z"), 3, tipTables, [hourlyRun, ...tipRunsAt("12:20")]).runDays).toEqual([3]);
    expect(planTick(new Date("2026-10-22T12:50:00Z"), 3, tipTables, [hourlyRun, ...tipRunsAt("12:20", "12:45")]).runDays).toEqual([3]);
    expect(planTick(new Date("2026-10-22T13:05:00Z"), 3, tipTables, [{ ...hourlyRun, startedAt: "2026-10-22T13:05:00Z" }, ...tipRunsAt("12:20", "12:45", "12:50")]).runDays).toEqual([]);
    expect(planTick(new Date("2026-10-22T13:15:00Z"), 3, tipTables, [{ ...hourlyRun, startedAt: "2026-10-22T13:05:00Z" }, ...tipRunsAt("12:20", "12:45", "12:50")]).runDays).toEqual([3]);
  });

  it("keeps hourly runs on local :05 across the 11/1/26 fall-back", () => {
    const tipTables = [{ day: 13, fetchedAt: "2026-11-01T06:05:00Z", tips: [] }];
    const ranAt = (startedAt: string) => [{ startedAt, ok: true, days: [13, 14] }];

    // 1:05a CDT, then the repeated 1:05a CST an hour later
    expect(planTick(new Date("2026-11-01T07:04:00Z"), 13, tipTables, ranAt("2026-11-01T06:05:00Z")).runDays).toEqual([]);
    expect(planTick(new Date("2026-11-01T07:05:00Z"), 13, tipTables, ranAt("2026-11-01T06:05:00Z")).runDays).toEqual([13, 14]);
  });

  it("runs today and flags the tip table when today's is missing", () => {
    const ledger = [{ startedAt: "2026-10-22T12:05:00Z", ok: true, days: [3, 4] }];

    expect(planTick(new Date("2026-10-22T12:10:00Z"), 3, [], ledger)).toMatchObject({ runDays: [3], tipTableStale: true });
  });

  it("runs today and flags the tip table when today's is over 2h old", () => {
    const ledger = [{ startedAt: "2026-10-22T12:05:00Z", ok: true, days: [3, 4] }];
    const tipTableFetchedAt = (fetchedAt: string) => [{ day: 3, fetchedAt, tips: [] }];

    expect(planTick(new Date("2026-10-22T12:10:00Z"), 3, tipTableFetchedAt("2026-10-22T10:10:00Z"), ledger)).toMatchObject({ runDays: [], tipTableStale: false });
    expect(planTick(new Date("2026-10-22T12:10:00Z"), 3, tipTableFetchedAt("2026-10-22T10:09:00Z"), ledger)).toMatchObject({ runDays: [3], tipTableStale: true });
  });

  it("reports a passed tip with no successful run in the 45 min before it", () => {
    const tipTables = [
      {
        day: 3,
        fetchedAt: "2026-10-22T12:05:00Z",
        tips: [
          { at: "2026-10-22T13:00:00Z", players: ["Cade Cunningham", "Naz Reid"] },
          { at: "2026-10-22T13:30:00Z", players: ["Desmond Bane"] },
        ],
      },
    ];
    const ledger = [
      { startedAt: "2026-10-22T12:14:00Z", ok: true, days: [3, 4] },
      { startedAt: "2026-10-22T12:20:00Z", ok: false, days: [3] },
      { startedAt: "2026-10-22T12:45:00Z", ok: true, days: [4] },
    ];

    expect(planTick(new Date("2026-10-22T13:00:00Z"), 3, tipTables, ledger).missedTips).toEqual([
      { at: "2026-10-22T13:00:00Z", day: 3, players: ["Cade Cunningham", "Naz Reid"] },
    ]);
  });

  it("reports a tip 10 min out with no successful run since 45 min before it", () => {
    const tipTables = [{ day: 3, fetchedAt: "2026-10-22T12:05:00Z", tips: [{ at: "2026-10-22T13:00:00Z", players: ["Cade Cunningham"] }] }];
    const ledger = [
      { startedAt: "2026-10-22T12:14:00Z", ok: true, days: [3] },
      { startedAt: "2026-10-22T12:45:00Z", ok: false, days: [3] },
    ];

    expect(planTick(new Date("2026-10-22T12:49:00Z"), 3, tipTables, ledger).missedTips).toEqual([]);
    expect(planTick(new Date("2026-10-22T12:50:00Z"), 3, tipTables, ledger).missedTips).toEqual([{ at: "2026-10-22T13:00:00Z", day: 3, players: ["Cade Cunningham"] }]);
  });

  it("reports no missed tip when a run succeeded in the window", () => {
    const tipTables = [{ day: 3, fetchedAt: "2026-10-22T12:05:00Z", tips: [{ at: "2026-10-22T13:00:00Z", players: ["Cade Cunningham"] }] }];
    const ledger = [{ startedAt: "2026-10-22T12:16:00Z", ok: true, days: [3] }];

    expect(planTick(new Date("2026-10-22T13:05:00Z"), 3, tipTables, ledger).missedTips).toEqual([]);
  });

  it("ignores tip tables from before today", () => {
    const tipTables = [
      { day: 2, fetchedAt: "2026-10-21T23:05:00Z", tips: [{ at: "2026-10-21T23:00:00Z", players: ["Cade Cunningham"] }] },
      { day: 3, fetchedAt: "2026-10-22T12:05:00Z", tips: [] },
    ];
    const ledger = [{ startedAt: "2026-10-22T12:05:00Z", ok: true, days: [3, 4] }];

    expect(planTick(new Date("2026-10-22T12:10:00Z"), 3, tipTables, ledger).missedTips).toEqual([]);
  });

  it("points the next alarm at the next tip target, missed-tip check or hourly run, whichever is sooner", () => {
    const tipTables = [{ day: 3, fetchedAt: "2026-10-22T12:05:00Z", tips: [{ at: "2026-10-22T13:00:00Z", players: ["Cade Cunningham"] }] }];

    expect(planTick(new Date("2026-10-22T12:20:00Z"), 3, tipTables, []).nextTarget).toEqual(new Date("2026-10-22T12:45:00Z"));
    expect(planTick(new Date("2026-10-22T12:45:00Z"), 3, tipTables, []).nextTarget).toEqual(new Date("2026-10-22T12:50:00Z"));
    expect(planTick(new Date("2026-10-22T12:50:00Z"), 3, tipTables, []).nextTarget).toEqual(new Date("2026-10-22T13:05:00Z"));
    expect(planTick(new Date("2026-10-22T11:30:00Z"), 3, tipTables, []).nextTarget).toEqual(new Date("2026-10-22T12:05:00Z"));
  });
});

describe("parseGameTips", () => {
  it("reads each game's tip time and players from the team page", () => {
    expect(parseGameTips(fantasyStatsPage)).toMatchInlineSnapshot(`
      [
        {
          "at": "2026-10-20T19:00:00.000Z",
          "players": [
            "Cade Cunningham",
            "John Collins",
            "Neemias Queta",
          ],
        },
        {
          "at": "2026-10-20T23:00:00.000Z",
          "players": [
            "Anfernee Simons",
            "Adem Bona",
            "Andre Drummond",
          ],
        },
        {
          "at": "2026-10-21T01:30:00.000Z",
          "players": [
            "De'Aaron Fox",
            "Devin Vassell",
          ],
        },
      ]
    `);
  });
});
