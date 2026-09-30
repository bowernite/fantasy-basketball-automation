// Loads the saved real Fleaflicker lineup page (`teampage.html`, Tue 10/20/2026, opening night)
// into the happy-dom globals, then adds what the logged-in owner sees: a slot `<select>` per player
// (option values per the lineup form: PG 1, SG 2, G 3, SF 4, PF 8, C 16, F/C 28, ANY 31, BN 0).
// The saved page is logged out, so the select markup is reconstructed, not copied

import { readFileSync } from "node:fs";
import { join } from "node:path";

const PAGE_HTML = readFileSync(join(import.meta.dir, "teampage.html"), "utf8");

export const PAGE_URL = "https://www.fleaflicker.com/nba/leagues/30579/teams/161025";

const SLOT_VALUES: [slot: string, value: number][] = [
  ["PG", 1],
  ["SG", 2],
  ["G", 3],
  ["SF", 4],
  ["PF", 8],
  ["F/C", 28],
  ["C", 16],
  ["ANY", 31],
];

const SLOTS_BY_POSITION: Record<string, string[]> = {
  "Point Guard": ["PG", "G", "ANY"],
  "Shooting Guard": ["SG", "G", "ANY"],
  "Small Forward": ["SF", "F/C", "ANY"],
  "Power Forward": ["PF", "F/C", "ANY"],
  Center: ["C", "F/C", "ANY"],
};

export type LineupPageOptions = {
  benchText?: string;
  // Rewrites an option's visible text, e.g. to simulate Fleaflicker renaming a slot
  optionText?: (slot: string) => string;
};

export function loadLineupPage({ benchText = "BN", optionText = (slot) => slot }: LineupPageOptions = {}) {
  const [, head, body] = PAGE_HTML.match(/<head>([\s\S]*)<\/head>\s*<body[^>]*>([\s\S]*)<\/body>/)!;
  document.head.innerHTML = head;
  document.body.innerHTML = body;

  for (const row of playerRows()) {
    const eligibility = row.querySelector(".player-info .position")!.getAttribute("title")!.split("/");
    const eligibleSlots = new Set(eligibility.flatMap((position) => SLOTS_BY_POSITION[position]));
    const statusCell = row.cells[row.cells.length - 1];
    const currentSlot = statusCell.textContent!.trim();

    const select = document.createElement("select");
    select.name = `status${row.querySelector(".player-text")!.id}`;
    select.className = "form-control input-sm";
    select.add(new Option(benchText, "0"));
    for (const [slot, value] of SLOT_VALUES) {
      if (eligibleSlots.has(slot)) {
        select.add(new Option(optionText(slot), String(value)));
      }
    }
    select.value = SLOT_VALUES.find(([slot]) => slot === currentSlot)?.[1].toString() ?? "0";

    row.cells[row.cells.length - 2].replaceChildren();
    statusCell.replaceChildren(select);
  }
}

export function playerRows() {
  return Array.from(document.querySelectorAll("tr")).filter((row) => row.querySelector(".player-text"));
}

export function playerRow(name: string) {
  const row = playerRows().find((r) => r.querySelector(".player-text")!.textContent === name);
  if (!row) throw new Error(`No row for ${name}`);
  return row;
}

// A player whose game has started: Fleaflicker shows "Locked" and no slot select
export function lockPlayer(name: string) {
  const row = playerRow(name);
  const statusCell = row.cells[row.cells.length - 1];
  const select = statusCell.querySelector("select")!;
  const slot = select.selectedOptions[0].text;
  row.cells[row.cells.length - 2].innerHTML =
    '<span class="btn btn-default btn-xs disabled btn-block">Locked</span>';
  statusCell.innerHTML = `<span class="label label-success label-block"><span class="position">${slot}</span></span>`;
}

// Gives a player a game on the viewed day (the fixture's bench players' teams are idle on opening night)
export function givePlayerGame(name: string, opponent: string) {
  playerRow(name).cells[2].innerHTML =
    `<div class="pro-opp-matchup"><a class="tt-content" href="/nba/boxscore?gameId=1">${opponent}` +
    `<span class="pro-opp-matchup-info"><span class="nowrap"><local-time datetime="2026-10-20T23:00:00Z">7:00 PM</local-time></span></span></a></div>`;
}

export function slotOf(name: string) {
  return slotIn(playerRow(name));
}

function slotIn(row: HTMLTableRowElement) {
  const select = row.querySelector("select");
  if (!select) return `${row.cells[row.cells.length - 1].textContent!.trim()} (locked)`;
  return select.selectedOptions[0]?.text ?? "(no option selected)";
}

// Player name → slot, for every player not on the bench
export function startedLineup() {
  return Object.fromEntries(
    playerRows()
      .map((row) => {
        const name = row.querySelector(".player-text")!.textContent!;
        return [name, slotIn(row)] as const;
      })
      .filter(([, slot]) => !slot.startsWith("BN")),
  );
}
