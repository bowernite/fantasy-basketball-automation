import type { Player } from "../types";

export const PLAYER_STATUS_SELECTOR = ".injury";

export function getPlayersTable() {
  const tables = document.querySelectorAll("table");
  if (tables.length !== 1) {
    console.error("Expected exactly one table, found", tables);
    throw new Error("Expected exactly one table");
  }
  return tables[0];
}

export function getStatTypeDropdown() {
  // 1: average/total. 2: season, fantasy, daily, last 5, etc. 3: previous year. 4: year selector
  const dropdownTriggers = document.querySelectorAll<HTMLAnchorElement>(
    ".btn-toolbar a.dropdown-toggle"
  );
  let statTypeDropdown: HTMLAnchorElement | undefined;
  dropdownTriggers.forEach((dropdownTrigger) => {
    if (statTypeDropdown) return;
    const dropdownMenu = dropdownTrigger.nextElementSibling;
    if (dropdownMenu?.textContent?.toLowerCase().includes("fantasy stats")) {
      statTypeDropdown = dropdownTrigger;
    }
  });

  return statTypeDropdown;
}

export function lineupHasChanges() {
  return (
    document.body.textContent
      ?.toLowerCase()
      .includes("click save lineup to save your changes".toLowerCase()) ?? false
  );
}

export function getSaveLineupButton() {
  const buttons = Array.from(
    document.querySelectorAll<HTMLButtonElement>("button[type='submit']")
  );
  const saveButton = buttons.find((button) =>
    button.textContent?.toLowerCase().includes("save lineup")
  );
  return saveButton;
}

export function getPageDate() {
  const allButtons = document.querySelectorAll("a.btn[data-toggle='dropdown']");
  const buttonsWithDates = Array.from(allButtons).filter((button) => {
    const text = button.textContent?.toLowerCase().trim() ?? "";
    return text.match(/\d{1,2}\/\d{1,2}(?:\/\d{2})?/) || text === "today";
  });
  if (buttonsWithDates.length !== 1) {
    console.error(
      `Tried to get page date but found ${buttonsWithDates.length} date buttons`,
      buttonsWithDates
    );
    throw new Error("Tried to get page date but found multiple date buttons");
  }
  const dateText = buttonsWithDates[0].textContent?.toLowerCase().trim() ?? "";
  if (dateText === "today") {
    return new Date(new Date().setHours(0, 0, 0, 0));
  }
  const dateMatch = dateText.match(/(\d{1,2}\/\d{1,2})(?:\/\d{2})?/);
  if (!dateMatch) {
    console.error("Could not find date in button text");
    throw new Error("Could not find date in button text");
  }
  const [month, day] = dateMatch[1].split("/").map(Number);
  return new Date(new Date().getFullYear(), month - 1, day);
}

function getDateDropdownButton() {
  const allButtons = document.querySelectorAll("a.btn[data-toggle='dropdown']");
  const buttonsWithDates = Array.from(allButtons).filter((button) => {
    const text = button.textContent?.toLowerCase().trim() ?? "";
    return text.match(/\d{1,2}\/\d{1,2}(?:\/\d{2})?/) || text === "today";
  });

  if (buttonsWithDates.length === 1) {
    return buttonsWithDates[0];
  }
  return null;
}

export function getPreviousDayButton() {
  const dateDropdown = getDateDropdownButton();
  if (!dateDropdown) return;

  const container = dateDropdown.parentElement; // div.btn-group
  if (!container) return;

  const prevButton = container.previousElementSibling;
  if (
    prevButton instanceof HTMLAnchorElement &&
    prevButton.querySelector(".fa-chevron-left")
  ) {
    return prevButton;
  }
}

export function getNextDayButton() {
  const dateDropdown = getDateDropdownButton();
  if (!dateDropdown) return;

  const container = dateDropdown.parentElement; // div.btn-group
  if (!container) return;

  const nextButton = container.nextElementSibling;
  if (
    nextButton instanceof HTMLAnchorElement &&
    nextButton.querySelector(".fa-chevron-right")
  ) {
    return nextButton;
  }
}

export function getPlayerNameCell(player: Player) {
  return player.row.querySelector<HTMLTableCellElement>("td:first-child");
}

export function getPlayerNameEl(player: Player) {
  const cell = getPlayerNameCell(player);
  if (!cell) return;
  return cell.querySelector<HTMLElement>(".player");
}
