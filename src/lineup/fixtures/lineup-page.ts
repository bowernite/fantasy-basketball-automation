// Loads the real Fleaflicker lineup page (Tue 10/20/2026, opening night) into the happy-dom globals.
// Two real captures are combined: `teampage.html` (logged out, the "fantasy stats" view the app requires)
// supplies the page, and `teampage-logged-in.html` (logged in, but saved on the "season stats" view)
// supplies each player's real slot `<select>` and cog menu, moved into the matching row. Swap to a single
// file once a logged-in "fantasy stats" capture exists

import { readFileSync } from "node:fs";
import { join } from "node:path";

const PAGE_HTML = readFileSync(join(import.meta.dir, "teampage.html"), "utf8");
const LOGGED_IN_PAGE_HTML = readFileSync(join(import.meta.dir, "teampage-logged-in.html"), "utf8");

export const PAGE_URL = "https://www.fleaflicker.com/nba/leagues/30579/teams/161025";

export type LineupPageOptions = {
  // Rewrites an option's visible text, e.g. to simulate Fleaflicker renaming a slot
  optionText?: (slot: string) => string;
  // false: the fantasy stats page as saved logged out (e.g. an expired session): no slot selects
  loggedIn?: boolean;
};

export function loadLineupPage({ optionText = (slot) => slot, loggedIn = true }: LineupPageOptions = {}) {
  const [head, body] = headAndBody(PAGE_HTML);
  document.head.innerHTML = head;
  document.body.innerHTML = body;
  if (!loggedIn) return;

  const loggedInPage = document.createElement("div");
  loggedInPage.innerHTML = headAndBody(LOGGED_IN_PAGE_HTML)[1];
  const loggedInRows = new Map(playerRows(loggedInPage).map((row) => [playerHref(row), row]));

  for (const row of playerRows()) {
    const loggedInRow = loggedInRows.get(playerHref(row))!;
    const [cogCell, selectCell] = Array.from(loggedInRow.cells).slice(-2);
    row.cells[row.cells.length - 2].replaceWith(cogCell);
    row.cells[row.cells.length - 1].replaceWith(selectCell);

    const select = selectCell.querySelector("select")!;
    for (const option of select.options) option.text = optionText(option.text);
    // happy-dom 20.14 misreads the parsed `selected` option (value/selectedIndex); re-select it explicitly
    select.value = select.querySelector<HTMLOptionElement>("option[selected]")!.value;
  }
}

function headAndBody(html: string) {
  const [, head, body] = html.match(/<head>([\s\S]*)<\/head>\s*<body[^>]*>([\s\S]*)<\/body>/)!;
  return [head, body];
}

function playerHref(row: HTMLTableRowElement) {
  return row.querySelector(".player-text")!.getAttribute("href");
}

export function playerRows(root: ParentNode = document) {
  return Array.from(root.querySelectorAll("tr")).filter((row) => row.querySelector(".player-text"));
}

export function playerRow(name: string) {
  const row = playerRows().find((r) => r.querySelector(".player-text")!.textContent === name);
  if (!row) throw new Error(`No row for ${name}`);
  return row;
}

// A player whose game has started: no slot select, just "Locked" and the slot's label, as the logged-out
// page shows every row (guess: a logged-in locked row hasn't been captured)
export function lockPlayer(name: string) {
  const row = playerRow(name);
  const statusCell = row.cells[row.cells.length - 1];
  const slot = selectedText(statusCell.querySelector("select")!);
  row.cells[row.cells.length - 2].innerHTML =
    '<span class="btn btn-default btn-xs disabled btn-block">Locked</span>';
  statusCell.innerHTML =
    slot === "Bench"
      ? '<span class="label label-danger label-block"><span class="text-muted">BN</span></span>'
      : `<span class="label label-success label-block"><span class="position">${slot}</span></span>`;
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
  return selectedText(select);
}

// happy-dom's `selectedOptions` goes stale after `select.value = …`; `selectedIndex` doesn't
function selectedText(select: HTMLSelectElement) {
  return select.options[select.selectedIndex]?.text ?? "(no option selected)";
}

// Player name → slot, for every player not on the bench
export function startedLineup() {
  return Object.fromEntries(
    playerRows()
      .map((row) => {
        const name = row.querySelector(".player-text")!.textContent!;
        return [name, slotIn(row)] as const;
      })
      .filter(([, slot]) => slot !== "Bench" && slot !== "BN (locked)"),
  );
}

// An injury tag next to the player's name, as on the saved page (e.g. `OUT`, `DTD`)
export function giveInjuryTag(name: string, status: string) {
  playerRow(name)
    .querySelector(".player-name")!
    .insertAdjacentHTML("afterbegin", `<span class="injury text-red tt-content">${status}</span>`);
}

// A news icon as on the saved page, with its news shown in a Bootstrap tooltip (as on hover). Guess:
// the real page ships news in `#page-data`, but the app caches that once per page load, so a test
// can't add to it
export function givePlayerNews(name: string, newsHtml: string) {
  playerRow(name).querySelector(".player-icons")!.innerHTML =
    '<i class="fa fa-file-text-o right-icon tt-content text-blue"></i>' +
    `<div class="tooltip fade top in"><div class="tooltip-arrow"></div><div class="tooltip-inner">${newsHtml}</div></div>`;
}
