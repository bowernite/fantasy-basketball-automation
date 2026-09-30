# Fleaflicker facts for the runner

Verified 2026-09-30 over plain HTTP (laptop and Worker IPs) unless marked otherwise. Public read endpoints: `get-league-info` Skill.

## Login

- `POST https://www.fleaflicker.com/nba/login`, urlencoded `email`, `password`, `keepMe=true`. No CSRF token, captcha or 2FA seen, from a residential IP or a Worker
- Success: `303` to `/nba` and `Set-Cookie: cookieId=…` (the only cookie; ~500-day Max-Age; not HttpOnly). A first login with an empty jar adds a "cookies not enabled" `_gAlert`: ignore it and judge by the next GET
- Failure: `200` with the form re-rendered and `.alert-danger`. **That page echoes the email and password: never log or store a failed-login body**
- Every login mints a new `cookieId` and older ones keep working, so a runner login never signs the user out. No sign-in or new-device email was sent
- The API's models include `LOGIN_CAPTCHA_REQUIRED`, so a captcha is possible under load
- Signed in = the page has `href="/logout"` ("Sign Out"). A signed-out team page is a `200` with "Log In" and no selects, not a redirect
- `cookieId` also authenticates `/api/*`

## Lineup page

- `/nba/leagues/30579/teams/161025?statType=0&week=N`: `week` is the league day (scoring period); `statType=0` is the fantasy-stats view the extension requires (`statType=1`, season stats, makes it abort). No `week` = the current day (day 1 all preseason). Future days render the full form
- Form: `method=post` to the same path; hidden `teamId`, `week`; one `<select name="status<proPlayerId>">` per player. No token
- Option text and value: `PG 1`, `SG 2`, `G 3`, `SF 4`, `PF 8`, `C 16`, `F/C 28`, `ANY 31`, `Bench 0`. Only eligible slots are listed, `Bench` always last
- `window.pageData.allPositions` (signed in only) gives each slot's `numStart`: 9 starters (PG, SG, G, SF, PF, C, F/C, ANY ×2)
- Times: `local-time[datetime]` (tip) and `relative-time[datetime]` (news) are UTC; their visible text is in a display timezone, so read `datetime`
- Locked row (seen on a past-season public page; current-day signed-in markup unverified until the 10/20 capture): no select, a disabled `Locked` button in the cog cell, last cell `<span class="label label-success label-block"><span class="position">PG</span></span>` (bench: `label-danger`, `BN`)
- A tipped game's matchup is a plain boxscore link with no tooltip id, e.g. `<a href="/nba/boxscore?…">CHI<span class="pro-opp-matchup-info">L 125-136</span></a>`
- The site's JS keeps unsaved dropdown edits in cookie `lineup-<teamId>-<week>-NBA` and restores them on load, which can surprise a browser run

## Saving

- POST every named form field, urlencoded, with `Origin` and `Referer`
- Accepted: `303` whose `_gAlert` decodes to "Lineup set successfully." (`_gAlert` / `_fm`: base64url → zlib inflate → the text after the last control character)
- Rejected: `200` with `.alert-danger`, e.g. "You cannot assign more than 1 to the PG position (Cade Cunningham, Desmond Bane)." Nothing is saved
- An 8-starter lineup is accepted: the server doesn't enforce filled slots
- A save sets that day only; later days are unchanged
- Unknown: the response when a posted player has locked, and when a POST races a lock at tip

## Signed-in JSON API

- `FetchRoster?sport=NBA&league_id=30579&team_id=161025&scoring_period=N` signed in adds per slot `swappableWith[]` (legal swap partners) and `leaguePlayer.eligibleFor[]`; the response has `lineupPeriod.ordinal`, `eligibleLineupPeriods[].low.startEpochMilli` (day mapping) and `groups[]` (START ×9, bench). Injury tag: `proPlayer.injury.typeAbbreviaition` (sic); games: `requestedGames[].game.startTimeEpochMilli`. Past days return `eligibleFor: []`
- Hidden `GET /api/SetLineup?sport=NBA&league_id=30579&team_id=161025&scoring_period=N&player_id=A&swap_player_id=B` (mobile-app API): `A` and `B` trade slots for that day only; `200 {"successPlayerIds":[A,B]}` (camelCase, unlike the docs). Signed out: `403 "Not the owner of team …"`. Missing partner: `422`. The param for filling an empty slot is unknown. Documented failure types: `FAILURE_LOCKED_PLAYER`, `FAILURE_SLOT_ABOVE_MAX`, `FAILURE_ACTIVE_ROSTER_ABOVE_MAX`, `FAILURE_PLAYER_INELIGIBLE`, `FAILURE_ACTIVE_ABOVE_POSITION_MAX`
- Probing: an existing endpoint answers bad params with a JSON 4xx; a nonexistent one with an HTML 404
- Etiquette: the admin allows respectful automation (one request at a time); keep requests serial

## Injury sources

- Fleaflicker news is fresh, but its tags go stale: OFS/OUT tags stayed on players ESPN had day-to-day with return dates
- ESPN `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries`: `User-Agent: curl/…` gets 200; browser, custom or missing UAs get 403 (same from a Worker). Statuses are only `Out` / `Day-To-Day`, plus `details.returnDate` and `shortComment`
- The NBA's official report (`ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_HH_MM{AM|PM}.pdf`, ET, every 15 min on game days) is the authority with Q/D/P/Available, but it's a PDF. Not used
