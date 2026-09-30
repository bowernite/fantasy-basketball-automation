import { expect, test } from "bun:test";
import {
  buildDefaultSlots,
  computeOptimalAssignments,
  type Candidate,
  type SlotLabel,
} from "./lineup-optimizer";

// League slots: PG · SG · G(PG|SG) · SF · PF · F/C(SF|PF|C) · C · ANY ×2
const ELIGIBLE_SLOTS: Record<string, SlotLabel[]> = {
  PG: ["PG", "G", "ANY"],
  "PG/SG": ["PG", "SG", "G", "ANY"],
  SG: ["SG", "G", "ANY"],
  SF: ["SF", "F/C", "ANY"],
  "SF/PF": ["SF", "PF", "F/C", "ANY"],
  PF: ["PF", "F/C", "ANY"],
  C: ["C", "F/C", "ANY"],
};

function candidate(id: string, position: string, score: number): Candidate {
  return { id, score, eligibleSlotLabels: ELIGIBLE_SLOTS[position] };
}

test("the default slots match the league's 9 starters", () => {
  expect(buildDefaultSlots().map((s) => s.label).toSorted()).toEqual(
    ["ANY", "ANY", "C", "F/C", "G", "PF", "PG", "SF", "SG"]
  );
});

test("starts every player in a legal slot when all 9 can fit", () => {
  const candidates = [
    candidate("pg", "PG", 30),
    candidate("sg", "SG", 29),
    candidate("pg2", "PG", 28),
    candidate("sf", "SF", 27),
    candidate("pf", "PF", 26),
    candidate("c1", "C", 25),
    candidate("c2", "C", 24),
    candidate("c3", "C", 23),
    candidate("c4", "C", 22),
  ];

  const result = computeOptimalAssignments(candidates, buildDefaultSlots());

  expect(result.assignments).toHaveLength(9);
  expect(result.totalScore).toBe(234);
  for (const a of result.assignments) {
    const c = candidates.find((c) => c.id === a.candidateId)!;
    expect(c.eligibleSlotLabels).toContain(a.slotLabel);
  }
  expect(new Set(result.assignments.map((a) => a.slotIndex)).size).toBe(9);
});

test("moves a dual-eligible guard to SG so three PG-only players can all start", () => {
  // Only PG, G and ANY×2 take PG-only players. If the PG/SG star takes PG or G,
  // one PG-only player (or the 3rd center) gets benched.
  const candidates = [
    candidate("star", "PG/SG", 50),
    candidate("pg1", "PG", 40),
    candidate("pg2", "PG", 39),
    candidate("pg3", "PG", 38),
    candidate("sf", "SF", 10),
    candidate("pf", "PF", 10),
    candidate("c1", "C", 10),
    candidate("c2", "C", 10),
    candidate("c3", "C", 10),
  ];

  const result = computeOptimalAssignments(candidates, buildDefaultSlots());

  expect(result.assignments).toHaveLength(9);
  expect(result.totalScore).toBe(217);
  const sgSlot = result.assignments.find((a) => a.slotLabel === "SG");
  expect(sgSlot?.candidateId).toBe("star");
});

test("benches the lowest scorers when more players are eligible than slots", () => {
  const candidates = [
    candidate("pg", "PG", 30),
    candidate("sg", "SG", 30),
    candidate("g", "PG/SG", 30),
    candidate("sf", "SF", 30),
    candidate("pf", "PF", 30),
    candidate("c", "C", 30),
    candidate("fc", "C", 30),
    candidate("any1", "SF/PF", 30),
    candidate("any2", "PG", 30),
    candidate("weak-pg", "PG", 5),
    candidate("weak-c", "C", 4),
  ];

  const result = computeOptimalAssignments(candidates, buildDefaultSlots());

  const started = result.assignments.map((a) => a.candidateId);
  expect(started).toHaveLength(9);
  expect(started).not.toContain("weak-pg");
  expect(started).not.toContain("weak-c");
  expect(result.totalScore).toBe(270);
});

test("a lower scorer who can fill an otherwise-empty slot beats a higher scorer who can't", () => {
  // 8 strong guards/wings + a weak center: benching the center would leave C empty
  const candidates = [
    candidate("pg1", "PG", 40),
    candidate("pg2", "PG", 40),
    candidate("sg1", "SG", 40),
    candidate("sg2", "SG", 40),
    candidate("sf1", "SF", 40),
    candidate("sf2", "SF", 40),
    candidate("pf1", "PF", 40),
    candidate("pf2", "PF", 40),
    candidate("sf3", "SF", 39),
    candidate("weak-c", "C", 1),
  ];

  const result = computeOptimalAssignments(candidates, buildDefaultSlots());

  const started = result.assignments.map((a) => a.candidateId);
  expect(started).toContain("weak-c");
  expect(started).not.toContain("sf3");
  expect(result.assignments).toHaveLength(9);
});

test("fills a slot with a zero-score player rather than leaving it empty", () => {
  // e.g. the only center is ruled OUT (score 0); the C slot should still be filled
  const candidates = [
    candidate("pg", "PG", 30),
    candidate("sg", "SG", 30),
    candidate("g", "PG", 30),
    candidate("sf", "SF", 30),
    candidate("pf", "PF", 30),
    candidate("fc", "PF", 30),
    candidate("any1", "SF", 30),
    candidate("any2", "SG", 30),
    candidate("out-c", "C", 0),
  ];

  const result = computeOptimalAssignments(candidates, buildDefaultSlots());

  expect(result.assignments).toHaveLength(9);
  expect(result.assignments.map((a) => a.candidateId)).toContain("out-c");
});

test("leaves only the unfillable slots empty on a short roster", () => {
  // No center-eligible player: C must stay empty, F/C goes to a forward
  const candidates = [
    candidate("pg", "PG", 30),
    candidate("sg", "SG", 29),
    candidate("sf", "SF", 28),
    candidate("pf", "PF", 27),
    candidate("pf2", "PF", 26),
  ];

  const result = computeOptimalAssignments(candidates, buildDefaultSlots());

  expect(result.assignments).toHaveLength(5);
  expect(result.assignments.map((a) => a.slotLabel)).not.toContain("C");
  expect(result.totalScore).toBe(140);
});
