export function verifyPage() {
  return verifyOnFantasyStatsPage();
}

export function verifyOnFantasyStatsPage() {
  const url = window.location.href;
  const onFantasyStatsPage =
    url ===
    "https://www.fleaflicker.com/nba/leagues/30579/teams/161025?statType=0";
  if (!onFantasyStatsPage) {
    alert("Not on the fantasy stats page; aborting");
  }
  return false;
}
