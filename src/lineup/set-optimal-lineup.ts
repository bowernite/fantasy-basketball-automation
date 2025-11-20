import type { Player } from "../page/get-players";
import { setPlayerPosition } from "./lineup-dom-actions";
import { stylePlayerAsStarted } from "../page/page-manipulation";
import {
  buildDefaultSlots,
  computeOptimalAssignments,
  type SlotLabel,
} from "../optimizer/lineup-optimizer";
import { getPlayerPredictedScore } from "../prioritization/score-weighting";

type Candidate = {
  id: string;
  score: number;
  eligibleSlotLabels: SlotLabel[];
  playerIndex: number;
};

function normalizeOptionTextToSlotLabel(text: string): SlotLabel | null {
  const t = text.trim().toUpperCase();
  if (t === "PG" || t === "SG" || t === "SF" || t === "PF" || t === "C") {
    return t as SlotLabel;
  }
  if (t === "G" || t === "F") return t as SlotLabel;
  if (t === "ANY" || t === "UTIL") return "ANY";
  return null;
}

function getEligibleSlotLabelsFromDropdown(player: Player): SlotLabel[] | null {
  const select = player.setPositionDropdown;
  if (!select) return null;
  const labels = Array.from(select.options)
    .map((o) => o.text)
    .filter((t) => t && !/^(bench|taxi|ir)$/i.test(t.trim()))
    .map((t) => normalizeOptionTextToSlotLabel(t))
    .filter((x): x is SlotLabel => Boolean(x));
  return Array.from(new Set(labels));
}

function buildCandidates(players: Player[]): Candidate[] {
  return players
    .map((p, idx) => {
      if (!p.setPositionDropdown || p.isIr || p.isTaxi) return null;
      const eligible = getEligibleSlotLabelsFromDropdown(p);
      if (!eligible || eligible.length === 0) return null;
      const [predictedScore, { weightedScore }] = getPlayerPredictedScore(p);

      // We need a secondary score, so that when there is a tie (i.e. players with no games), there is a deterministic fallback to break a tie (their 'weighted score', i.e. roughly their season average)
      // Fallback to 1, so that players with a predicted score of `0` *because of injury* are still prioritized over players with no games
      const primaryScore = p.todaysGame ? predictedScore || 1 : 0;
      const fallbackScore = weightedScore;
      const combinedScore = primaryScore * 1000 + fallbackScore;

      return {
        id: p.playerName,
        score: combinedScore,
        eligibleSlotLabels: eligible,
        playerIndex: idx,
      };
    })
    .filter((x): x is Candidate => x !== null);
}

function optionMatchesLabel(optionText: string, label: SlotLabel): boolean {
  const t = optionText.trim().toUpperCase();
  if (label === "ANY") return t === "ANY" || t === "UTIL";
  return t === label;
}

function findOptionValueForLabel(
  player: Player,
  label: SlotLabel
): string | null {
  const select = player.setPositionDropdown;
  if (!select) return null;
  for (const option of Array.from(select.options)) {
    const text = option.text || "";
    const isNonSlot = /^(bench|taxi|ir)$/i.test(text.trim());
    if (isNonSlot) continue;
    if (optionMatchesLabel(text, label)) {
      return option.value;
    }
  }
  return null;
}

export function setOptimalLineup(players: Player[]) {
  const slots = buildDefaultSlots();
  const candidates = buildCandidates(players);
  const { assignments } = computeOptimalAssignments(
    candidates.map((c) => ({
      id: c.id,
      score: c.score,
      eligibleSlotLabels: c.eligibleSlotLabels,
    })),
    slots
  );

  const startedIndexes = new Set<number>();
  for (const a of assignments) {
    const candidate = candidates.find((c) => c.id === a.candidateId);
    if (!candidate) continue;
    const player = players[candidate.playerIndex];
    const value = findOptionValueForLabel(player, a.slotLabel);
    if (!value) continue;
    setPlayerPosition(player, value);
    stylePlayerAsStarted(player);
    startedIndexes.add(candidate.playerIndex);
  }

  return {
    numStarted: startedIndexes.size,
  };
}
