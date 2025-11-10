export type SlotLabel = "PG" | "SG" | "SF" | "PF" | "C" | "G" | "F" | "ANY";

export type Slot = {
  id: string;
  label: SlotLabel;
};

export type Candidate = {
  id: string;
  score: number;
  eligibleSlotLabels: SlotLabel[];
};

export type Assignment = {
  candidateId: string;
  slotIndex: number;
  slotLabel: SlotLabel;
};

export type OptimizeResult = {
  assignments: Assignment[];
  totalScore: number;
};

export function buildDefaultSlots(): Slot[] {
  return [
    { id: "PG", label: "PG" },
    { id: "SG", label: "SG" },
    { id: "SF", label: "SF" },
    { id: "PF", label: "PF" },
    { id: "C", label: "C" },
    { id: "G", label: "G" },
    { id: "F", label: "F" },
    { id: "ANY#1", label: "ANY" },
    { id: "ANY#2", label: "ANY" },
  ];
}

function buildEligibilityMatrix(
  candidates: Candidate[],
  slots: Slot[]
): boolean[][] {
  const matrix: boolean[][] = Array.from({ length: candidates.length }, () =>
    Array(slots.length).fill(false)
  );

  for (let i = 0; i < candidates.length; i++) {
    const candidate = candidates[i];
    for (let s = 0; s < slots.length; s++) {
      const slot = slots[s];
      const canFill =
        slot.label === "ANY" ||
        candidate.eligibleSlotLabels.includes(slot.label) ||
        (slot.label === "G" &&
          (candidate.eligibleSlotLabels.includes("PG") ||
            candidate.eligibleSlotLabels.includes("SG"))) ||
        (slot.label === "F" &&
          (candidate.eligibleSlotLabels.includes("SF") ||
            candidate.eligibleSlotLabels.includes("PF")));
      matrix[i][s] = Boolean(canFill);
    }
  }
  return matrix;
}

export function computeOptimalAssignments(
  candidates: Candidate[],
  slots: Slot[]
): OptimizeResult {
  const numSlots = slots.length; // 9
  const numCandidates = candidates.length;
  if (numSlots === 0 || numCandidates === 0) {
    return { assignments: [], totalScore: 0 };
  }

  const eligibility = buildEligibilityMatrix(candidates, slots);

  const maxMask = 1 << numSlots;
  const dp = new Array<number[]>(numCandidates + 1);
  const choice = new Array<{ took: boolean; slot: number | null }[]>(
    numCandidates + 1
  );
  for (let i = 0; i <= numCandidates; i++) {
    dp[i] = new Array<number>(maxMask).fill(-Infinity);
    choice[i] = new Array<{ took: boolean; slot: number | null }>(maxMask);
  }
  dp[0][0] = 0;
  choice[0][0] = { took: false, slot: null };

  for (let i = 0; i < numCandidates; i++) {
    for (let mask = 0; mask < maxMask; mask++) {
      const current = dp[i][mask];
      if (current === -Infinity) continue;

      if (current > dp[i + 1][mask]) {
        dp[i + 1][mask] = current;
        choice[i + 1][mask] = { took: false, slot: null };
      }

      for (let s = 0; s < numSlots; s++) {
        if ((mask & (1 << s)) !== 0) continue;
        if (!eligibility[i][s]) continue;
        const nextMask = mask | (1 << s);
        const nextVal = current + (candidates[i].score || 0);
        if (nextVal > dp[i + 1][nextMask]) {
          dp[i + 1][nextMask] = nextVal;
          choice[i + 1][nextMask] = { took: true, slot: s };
        }
      }
    }
  }

  let bestMask = 0;
  let bestScore = -Infinity;
  let bestFilled = -1;
  for (let mask = 0; mask < maxMask; mask++) {
    const filled = countBits(mask);
    const score = dp[numCandidates][mask];
    if (score === -Infinity) continue;
    if (
      score > bestScore ||
      (score === bestScore && filled > bestFilled)
    ) {
      bestScore = score;
      bestMask = mask;
      bestFilled = filled;
    }
  }
  if (bestScore === -Infinity) {
    return { assignments: [], totalScore: 0 };
  }

  const assignments: Assignment[] = [];
  let i = numCandidates;
  let mask = bestMask;
  while (i > 0) {
    const c = choice[i][mask];
    if (!c) {
      i--;
      continue;
    }
    if (c.took && c.slot !== null) {
      assignments.push({
        candidateId: candidates[i - 1].id,
        slotIndex: c.slot,
        slotLabel: slots[c.slot].label,
      });
      mask = mask ^ (1 << c.slot);
    }
    i--;
  }
  assignments.reverse();

  return {
    assignments,
    totalScore: bestScore,
  };
}

function countBits(x: number): number {
  let n = 0;
  while (x) {
    x &= x - 1;
    n++;
  }
  return n;
}


