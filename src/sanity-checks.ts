import { getStatTypeDropdown } from "./page/page-querying";

export function verifyPage() {
  return verifyOnFantasyStatsPage();
}

export function verifyOnFantasyStatsPage() {
  const dropdown = getStatTypeDropdown();
  console.log('🟣 fantasy stats dropdown value: "', dropdown?.textContent, '"');
  const isOnFantasyStatsPage =
    dropdown?.textContent?.toLowerCase().trim() === "fantasy stats";
  if (!isOnFantasyStatsPage) {
    alert("Not on the fantasy stats page; aborting");
  }
  return isOnFantasyStatsPage;
}
