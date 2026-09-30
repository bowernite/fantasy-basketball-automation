---
description: Use when fetching Fleaflicker league data (rosters, ownership, rates, standings, scores, picks, trades, transactions, free agents, rules)
---

League `30579`, our team `161025` (both hardcoded in `extension/manifest.json`). Map owners/`team_id`s to Names via `team-info`.

## Fetch in a subagent

Every Fleaflicker call runs inside a dedicated `general-purpose` `Agent` (AGENTS.md §Subagents). Name the exact endpoints/params and the shape to hand back; the subagent returns only the parsed fields/table needed, not raw JSON or HTML.

One subagent per side/task, making its calls serially in-process (throttle, §Gotchas) — e.g. all of step 2 in `trades`, or a team's roster + profile calls. Split into multiple subagents only for independent tasks (e.g. two teams' situations), never to parallelize calls against Fleaflicker.

## Pick the right source

1. **Real NBA stats/news/projections** (averages, league-wide injuries, matchups) → web search (`looking-things-up`)
2. **League-specific data** (ownership, rosters, standings, scoring, waivers, transactions, our lineup, injury status) → JSON API below. No auth, no browser
3. **Browser** → last resort ([browser.md](./browser.md)), only when the data is genuinely needed *and* the API can't supply it: player news, defense-vs-position tooltips, setting a lineup. If the detour is only nice-to-have, skip it and say what was skipped

**On any trade question, fetch `FetchTrades` first.**

Never call `FetchTradeBlock` under any circumstance; trade-related data comes from `FetchTrades`, `FetchTeamPicks` and `FetchLeagueTransactions`.

# JSON API

Unauthenticated. `https://www.fleaflicker.com/api/<Endpoint>?sport=NBA&league_id=30579`

Signed-in fields, HTTP login and lineup saves (form or `/api/SetLineup`): `lineup-runner` Skill's [fleaflicker.md](../lineup-runner/fleaflicker.md).

| Endpoint | Extra params | Returns |
|---|---|---|
| `FetchLeagueStandings` | `season` | records, PF/PA, team id→name map |
| `FetchLeagueRosters` | — | every team's roster in one call — **bodies + ownership, no rates** |
| `FetchRoster` | `team_id`, `season`, `scoring_period` | one roster w/ lineup slots + per-game logs — **the only source of rates**, but `season=` is a snapshot |
| `FetchPlayerListing` | see below | player pool / free agents |
| `FetchPlayerProfile` | `player_id`, `season` | game log, ranks, owner |
| `FetchLeagueScoreboard` | `season`, `scoring_period` | matchups for a period |
| `FetchLeagueBoxscore` | `fantasy_game_id`, `scoring_period` | one matchup's detail, **one day at a time** |
| `FetchLeagueRules` | — | roster limits, roster positions, scoring categories |
| `FetchLeagueTransactions` / `FetchLeagueActivity` | | adds/drops/trades |
| `FetchLeagueDraftBoard` | `season` | draft order + picks |
| `FetchTeamPicks` | `team_id` | **current pick ownership, every future season** — `picks[].{season, slot.{round,slot,overall}, ownedBy, originalOwner, traded}`; a traded pick is listed under both teams (dedupe) |
| `FetchTrades` | `filter=TRADES_COMPLETED`, `result_offset` | **pending trades (default) and the full trade history** |

## `FetchTrades`

- Default = **live/pending** trades only; `filter=TRADES_COMPLETED` = history. No other `filter` value and **no `team_id`** (both 400)
- `resultTotal` is wrong (e.g. 1300 vs 21 actual): page `result_offset` (10/page) until a page comes back short
- **An approved trade is invisible to every other endpoint until it executes.** During the 24-hour review window `FetchLeagueDraftBoard` still shows a traded pick as the sender's with `tradeId: None`, and rosters still show the old owner. Check here before quoting either
- Pending-only fields: `numVetoesRequired`, `expiryIso`, `proposedOn` / `approvedOn` / `tentativeExecutionTime`, `chatChannel`, `description`
- `teams[]` has **2 or 3 entries** (three-team deals exist), each with `playersObtained[]`, `picksObtained[]`, `playersReleased[]` — releases are how a side over `maxRosterSize` fits the deal (`league-info`)
- `picksObtained[].{season, slot, ownedBy, originalOwner, traded, lost}` is a pick's trade history; for who holds it now read `FetchTeamPicks` (`FetchLeagueDraftBoard` returns `{}` for every season but the last completed draft and the next one)
  - `ownedBy` is the pick's **current** holder, rewritten in every past trade that carries it — who received it in that trade is the `teams[]` entry. A pick back with its originator drops `originalOwner`/`traded`/`lost` in every past trade too
  - `slot` as `{round}` alone → slot **undetermined**, not `0` (the one exception to missing key = 0)
  - `slot`/`overall` are the originator's **current-board** slot for every season, past and future — a 2027 2nd shows its owner's 2026 slot, a completed draft's pick shows today's slot, not where it went. Read as absent except for the next draft (Trap 2 applies here too)

## `FetchPlayerListing`

- `filter.free_agent_only=true|false` is **required** (omitting it 403s). Also `filter.position_eligibility=PG|SG|SF|PF|C`, `sort=SORT_SEASON_TOTAL|SORT_SEASON_AVERAGE|SORT_SCHEDULE_PERIOD|SORT_SCORING_PERIOD|SORT_LAST_X_SHORT|SORT_LAST_X_LONG`, `result_offset=` (30/page; response carries `resultTotal` + `resultOffsetNext`)
- No `season` param — use `sort_season`
- Injury status: `proPlayer.injury` = `{typeAbbreviaition, description, severity, typeFull}` (their typo), e.g. `OFS / Finger / OUT / "Out for season"`. Present **only when injured** — absence means healthy. Valuing it is `Eval Definitions §Durability`'s call

## Rates: fantasy-point fields

- `seasonTotal` / `seasonAverage` (FPts), `lastX[]` (durations 1/5/10), `rankFantasy`, `seasonConsistency`, `seasonsStandartDeviation` come from `FetchPlayerListing` **and from `FetchRoster`, but only when `season` is passed**; omit it and every field except `lastX` disappears. For a known team, one `FetchRoster?season=` call beats paging the listing
- Games played = `seasonTotal / seasonAverage`; check it before trusting an average (small-sample scrubs top the average sort)
- `seasonAverage` is **already scored under this league's rules** and renders on every manager's roster page — treat it as shared information
- `rankFantasy` is keyed to season _totals_, so it craters for anyone who missed time and says nothing about their rate
- `rankDraft` (listing + roster players) is the _upcoming_ season's draft-board rank: only ~top-340 ranked, **not refreshed for offseason trades/signings**. Weak prior; verify role via web research before acting on it

## `FetchRoster` vs `FetchLeagueRosters`

- `FetchLeagueRosters` returns `rosters[].players[]` (a different shape from `FetchRoster`'s `groups[].slots[].leaguePlayer`) with **no `seasonAverage` / `seasonTotal` / `rankFantasy`**. Use it for ownership, `positionEligibility` and **body counts**. `FetchRoster?team_id=&season=` is the only path to rates and `GP`
- `season=` on `FetchLeagueRosters` is **not ignored**: it swaps the live rosters for the same end-of-March snapshot `FetchRoster?season=` gives (verified 2026-08-08). **Omit it** for current ownership
- `FetchRoster?season=` returns the roster **as of that season's last lineup period**, omitting every later add (verified: 26 bodies vs 28 live). Count bodies from `FetchLeagueRosters` only. Omitting `season` gives the live roster with no rates
- On `FetchRoster` rows the rate is **`seasonAverage`** (absent = no games played). `viewingActualPoints` is the *viewed lineup period* only (one day by default) and absent on most bench rows; `viewingActualPointsAverage` does **not** exist here and silently yields 0.00 for everyone
- `groups[]`: `START` · unlabelled bench

## `FetchPlayerProfile`

- Player is under `player.proPlayer` (not top-level `proPlayer`)
- Age: use `detail.dob` (ms epoch, parse **UTC**); `detail.age` is truncated to whole years and `Eval Definitions §Columns` forbids it
- `season` **is honoured**, one season per call (verified). Counts exceed 82 because playoffs are included; filter on `games[].game.period.season` only if you passed no season
- Per-game rows carry raw stats (incl. `Min`) **and** `games[].pointsActual.value` — fantasy points already scored; use them as-is

## `FetchLeagueStandings`

- Teams are under `divisions[].teams[]` (one division). Record rank = `recordOverall.rank`; points for = `pointsFor.value` — **sort PF yourself, there is no PF rank field**
- `recordOverall.rank` is **not the playoff seed** (`league-info`). `recordPostseason` is separate and excluded from PF
- `draftPosition` (= `13 − recordOverall.rank`) is **not authoritative** — where it disagrees with `FetchLeagueDraftBoard`, the board wins (verified case exists)

## `FetchLeagueTransactions`

- 30/page, page `result_offset`
- `items[].transaction.type` is absent for an **add**, present only for `TRANSACTION_DROP` / `CLAIM` / `TRADE` / `DRAFT` / `IMPORT` — filtering for `TRANSACTION_ADD` returns nothing. Treat a typeless item as an add
- A pick row is `transaction.draftPick.{season, round}` with **no `player` key, no slot and no originating team** (`transaction.team` is the receiver) — naive parsing KeyErrors or silently drops every pick
- `transaction.tradeId` is the only thing grouping the legs of a multi-asset or three-team deal
- `bidAmount` + `waiverResolutionTeams` appear on claims

## Scores: `FetchLeagueScoreboard` / `FetchLeagueBoxscore`

- Weekly team scores: `FetchLeagueScoreboard?season=&scoring_period=<low day ordinal of the period>`. Enumerate periods from `eligibleSchedulePeriods[]`; verify the echoed `schedulePeriod.ordinal` matches what you asked for
- Each game carries `isPlayoffs` / `isConsolation` — exclude both to reproduce `pointsFor`, which reconciles exactly. Take the bracket's shape from `league-info` only, never from these flags
- `FetchLeagueBoxscore` returns **one day**, defaulting to the period's last; pass `scoring_period` and page `eligiblePeriods[]` to reconstruct a week. `pointsHome`/`pointsAway` `.total` is the whole period, while the lineup rows are that one day

## `FetchLeagueRules`

- Roster limits at top level: `maxRosterSize`, `maxActive`, `numStarters`, `numBench`, `rosterPositions[]` (`league-info` reads them)
- Scoring at `groups[].scoringRules[]` as `points.value` / `pointsPer.value` with `forEvery` — divide to get the per-unit weight. Absent category = not scored
- **`FGM` is used for both field goals *made* and field goals *missed*** (different category ids)
- `waiverType`, `defaultWaiverBudget`, `maxKeepers` come on `FetchLeagueStandings`' `league` object; the transaction limit, trade deadline and tiebreakers only on the rules page (`league-info`)

## Draft boards and two traps

`FetchLeagueDraftBoard?season=N` is the draft held in the N offseason, drafting the year-N NBA rookie class, feeding season N (the `'N-(N+1)` campaign). The response body has **no season field** — the label is the query param only. Only the last completed draft and the next one exist; other seasons return `{}`.

- **Trap 1 — the label is ambiguous in conversation.** "A 2028 1st" can mean the draft held in Sept 2028 or the one Fleaflicker labels for the `'27-28` season. Resolve it by naming **the season whose finish sets the slot** (`league-info` §Drafting), and say which you mean in any output
- **Trap 2 — placeholder slots.** The site displays future-draft pick rows with slots copied from the last finish; they look like data and are not. **Read a displayed future slot as absent** and project it from `strategy/Team Projections.md` (`eval-pick`). This endpoint returns `{}` rather than a fake, but **`FetchTrades` serves the fake**

Structure: `rows[].cells[].slot.{round,slot,overall}` · `rows[].cells[].team` is the **current** owner while `draftOrder[]` (index = slot) is the **original** owner · `tradeId` + `fromOtherTeam: true` mark acquired picks · no `player` key = pick unmade. `draftOrder[]` is one array for every round (order rule: `league-info` §Drafting). Its `rosters` payload omits `rankDraft`. A pick moved by an approved-but-unexecuted trade still shows as the sender's with `tradeId: None` — cross-check `FetchTrades`.

## Gotchas

- **Rate-limited**: sustained rapid requests 403 every endpoint for ~1 min. Throttle to ~1/sec, serial, single-threaded. A sudden 403 on a URL that just worked is throttling, not a bad param
- **Missing key = `0`**: Fleaflicker omits zero/default fields entirely, so parse with `.get()`. E.g. `recordOverall.wins` is absent for a team with no wins (`losses` is present). Exception: absent `picksObtained[].slot` = undetermined
- An unknown param returns an **HTML 400 page, not JSON** — if parsing fails, check the param name
- The response echoes its own enums (`eligibleSorts`, `eligibleFilterPositions`, `sortSeasons`, `eligibleLineupPeriods`) — read those instead of guessing
- `scoring_period` / `week` is a **1-indexed day ordinal from opening day**, not a calendar date. Map it via `eligibleLineupPeriods[].low.startEpochMilli`
- Seasons are start-year (`2025` = '25-26). Current season may be empty in the offseason — fall back to the prior year
- `percentOwnedRatio` is Fleaflicker-wide, not this league
- `proTeamAbbreviation: "FA"` = unsigned in the NBA, distinct from unowned in our league
- No player news or opponent-strength data in the API

## Offseason

- The incoming rookie class sits in the **free-agent pool** before the rookie draft runs (`isRookie: true`, zero prior-season stats). Confirm league rules before treating them as addable
- **The FA-add lock is invisible to the API** (window: `league-info` §Offseason transaction lock). `FetchLeagueTransactions` still lists offseason adds and drops, `FetchPlayerListing?filter.free_agent_only=true` still reports the whole pool, and `transactionStatus.locked` is an empty `{}` on **every** player. There is no wire-live check; use the window `league-info` states
