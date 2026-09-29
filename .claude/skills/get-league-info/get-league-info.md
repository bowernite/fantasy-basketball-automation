---
name: get-league-info
description: Get data out of the Fleaflicker fantasy NBA league (league 30579) — JSON API endpoints, field paths and gotchas.
---

# Fleaflicker league data

League `30579` ("The Dynasty League"), our team `161025` ("Bathroom club"). Both are hardcoded in `extension/manifest.json`.

## Fetch in a subagent

**Every Fleaflicker call runs inside a dedicated `Agent` call (`general-purpose`), never inline** (`CLAUDE.md` §*Subagents*). Name the exact endpoints/params and the shape to hand back; the subagent returns only the parsed fields/table needed, not raw JSON or HTML.

**One subagent per side/task, not one per endpoint.** The ~1/sec serial throttle (below) is real, so batch a whole fetch sequence (e.g. all of step 2 in `trades`, or a team's roster + profile calls) into a single subagent making its calls serially in-process. Split into multiple subagents only for genuinely independent tasks (e.g. two different teams' situations) — never to parallelize calls against Fleaflicker.

## Pick the right source

1. **Real NBA stats/news/projections** (player averages, injuries league-wide, matchups) → web search (`looking-things-up`).
2. **League-specific data** (ownership, rosters, standings, scoring, waivers, transactions, our lineup) → **Fleaflicker JSON API** below. No auth, no browser.
3. **Browser** → last resort, `browser.md` (this directory).

**Heavily prefer the API.** Reach for the browser only when the data is genuinely needed *and* the API demonstrably cannot supply it — player news, defense-vs-position tooltips, setting a lineup. **Not** injury status, which is in the API (below). Check the field paths first; if a browser detour is only nice-to-have, skip it and say what was skipped.

## JSON API (default — start here)

Unauthenticated. `https://www.fleaflicker.com/api/<Endpoint>?sport=NBA&league_id=30579`

| Endpoint                                          | Extra params                          | Returns                                                      |
| ------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------ |
| `FetchLeagueStandings`                            | `season`                              | records, PF/PA, team id→name map                             |
| `FetchLeagueRosters`                              | —                                     | every team's roster in one call — **bodies + ownership, no rates** |
| `FetchRoster`                                     | `team_id`, `season`, `scoring_period` | one roster w/ lineup slots + per-game logs — **the only source of rates**, but `season=` is a snapshot |
| `FetchPlayerListing`                              | see below                             | player pool / free agents                                    |
| `FetchPlayerProfile`                              | `player_id`, `season`                 | game log, ranks, owner                                       |
| `FetchLeagueScoreboard`                           | `season`, `scoring_period`            | matchups for a period                                        |
| `FetchLeagueBoxscore`                             | `fantasy_game_id`, `scoring_period`   | one matchup's detail, **one day at a time**                   |
| `FetchLeagueRules`                                | —                                     | roster limits, roster positions, scoring categories          |
| `FetchLeagueTransactions` / `FetchLeagueActivity` |                                       | adds/drops/trades                                            |
| `FetchLeagueDraftBoard`                           |                                       | draft order + picks                                          |
| `FetchTrades`                                     | `filter=TRADES_COMPLETED`, `result_offset` | **pending trades (default) and the full trade history** — see below |

**On any trade question, fetch `FetchTrades` first.**

**`FetchTradeBlock` is forbidden — never call it.** Do not fetch the trade block from
Fleaflicker under any circumstance.

### `FetchTrades`

Default = **live/pending** trades only; `filter=TRADES_COMPLETED` = history. No other
`filter` value and **no `team_id`** (both 400). `resultTotal` is wrong (reports 1300 against
21 actual) — page `result_offset` (10/page) until a page comes back short.

**An approved trade is invisible to every other endpoint until it executes.** During the
veto window `FetchLeagueDraftBoard` still shows a traded pick as the sender's with
`tradeId: None`, and rosters still show the old owner. Check here before quoting either.

**Assumed-through** (`strategy/Pending Trades.md`): treat as executed even when this
endpoint still lists them pending, or has no record. Overlay before quoting
ownership. `strategy/lineup-math/run fetch_data.py roster` does the same to the files (`assumed_trades.py`).
The wire does not win.

Pending-only fields: `numVetoesRequired`, `expiryIso`, `proposedOn` / `approvedOn` /
`tentativeExecutionTime`, `chatChannel`, `description`.

`teams[]` has **2 or 3 entries** (three-team deals exist), each with `playersObtained[]`,
`picksObtained[]`, `playersReleased[]` — releases are how a side over `maxRosterSize` fits
the deal (`league-info`).

`picksObtained[].{season, slot, ownedBy, originalOwner, traded, lost}` is the **only wire
source of pick ownership for any other season** — `FetchLeagueDraftBoard` returns `{}` for
every season but the last completed draft and the next one.

- `ownedBy` is the pick's **current** holder, rewritten in every past trade that carries it — never who received it in that trade (that's the `teams[]` entry). A pick back with its originator drops `originalOwner`/`traded`/`lost` in every past trade too.
- `slot` can be `{round}` alone → the slot is **undetermined**, not `0`. The one exception to
  "a missing key is a 0" below.
- `slot`/`overall` are the originator's **current-board** slot for every season, past and future — a 2027 2nd served at its owner's 2026 slot, a completed draft's pick at today's slot, not where it went. Read as absent except for the next draft — Trap 2 applies to this endpoint too.

`FetchPlayerListing` params: `filter.free_agent_only=true|false` (**required** — omitting it 403s), `filter.position_eligibility=PG|SG|SF|PF|C`, `sort=` one of `SORT_SEASON_TOTAL|SORT_SEASON_AVERAGE|SORT_SCHEDULE_PERIOD|SORT_SCORING_PERIOD|SORT_LAST_X_SHORT|SORT_LAST_X_LONG`, `result_offset=` (30/page; response carries `resultTotal` + `resultOffsetNext`). It has **no** `season` param — use `sort_season`.

Fantasy-point aggregates — `seasonTotal` / `seasonAverage` (FPts), `lastX[]` (durations 1/5/10), `rankFantasy`, `seasonConsistency`, `seasonsStandartDeviation` — come from this endpoint **and from `FetchRoster`, but only when `season` is passed**; omit it and every field except `lastX` disappears. For a known team, one `FetchRoster?season=` call beats paging the listing.

Games played = `seasonTotal / seasonAverage`; check it before trusting an average (small-sample scrubs top the average sort).

`seasonAverage` is **already scored under this league's rules** and renders on every manager's roster page — treat it as shared information. `rankFantasy` is keyed to season _totals_, so it craters for anyone who missed time and says nothing about their rate.

`FetchPlayerProfile`: player is under `player.proPlayer` (not top-level `proPlayer`). Both `detail.dob` (ms epoch, parse **UTC**) and `detail.age` exist — **use `dob`**; `age` is truncated to whole years and `Eval Definitions §Columns` forbids it. The `season` param **is honoured** — one season per call (verified: `season=2025` → 96 rows all 2025, `season=2024` → 88 all 2024). Counts exceed 82 because playoffs are included; filter on `games[].game.period.season` only if you passed no season. Per-game rows carry raw stats (incl. `Min`) **and** `games[].pointsActual.value` — fantasy points already scored. Never recompute them.

`FetchLeagueRosters` returns **`rosters[].players[]`** — a different shape from
`FetchRoster`'s `groups[].slots[].leaguePlayer`, with **no `seasonAverage` / `seasonTotal`
/ `rankFantasy`**, so it never yields rates. Use it for ownership,
`positionEligibility` and **body counts**; `FetchRoster?team_id=&season=` is the only path
to rates and `GP`.

**`season=` on it is NOT ignored** — it swaps the live rosters for the same end-of-March
snapshot `FetchRoster?season=` gives (verified 2026-08-08: identical member sets, and 8
players on each side of the diff against live). **Omit it** for current ownership.

`FetchRoster?season=` returns the roster **as of that season's last lineup period** — a
historical snapshot that omits every later add (verified: 26 bodies against 28 live). **Never
count bodies from it**; use `FetchLeagueRosters`. Omitting `season` gives the live roster with
no rates.

On `FetchRoster` rows use **`seasonAverage`** for a rate, nothing else (absent = no games
played). `viewingActualPoints` is the *viewed lineup period* only (one day by default) and is
absent on most bench rows; `viewingActualPointsAverage` does **not** exist here — reaching for
it yields 0.00 for everyone, silently.

`groups[]`: `START` · unlabelled bench · `INJURED`. Only **filled** IR slots are rendered, so
group length is not the slot count, and an IR occupant often has **no `injury` field** —
healthy players sit parked there (`league-info` on `maxActive`).

`FetchLeagueStandings`: teams are under `divisions[].teams[]` (one division). Record rank
is `recordOverall.rank`; points for is `pointsFor.value` — **sort it yourself, there is no
PF rank field**. `recordOverall.rank` is **not the playoff seed** — seeds tie-break on PF
(`league-info`). `recordPostseason` is separate and excluded from PF. `draftPosition` is
derived as `13 − recordOverall.rank` and is **not authoritative** — where it disagrees
with `FetchLeagueDraftBoard`, the draft board wins (verified case exists).

**Fleaflicker omits zero/default fields entirely** — a missing key is a `0`, not an error
in your parse. Use `.get()`, never direct access. One exception: an absent
`picksObtained[].slot` (above) means *undetermined*. Two that bite:

- `recordOverall.wins` is **absent** for a team with no wins (`losses` is present).
- `items[].transaction.type` on `FetchLeagueTransactions` is absent for an **add** and
  present only for `TRANSACTION_DROP` / `CLAIM` / `TRADE` / `DRAFT` / `IMPORT` — so filtering
  for `TRANSACTION_ADD` returns nothing. Treat a typeless item as an add.

`FetchLeagueTransactions` further: 30/page, page `result_offset`. A pick row is
`transaction.draftPick.{season, round}` with **no `player` key, no slot and no originating
team** (`transaction.team` is the receiver) — naive parsing KeyErrors or drops every pick
silently. `transaction.tradeId` is the only thing grouping the legs of a multi-asset or
three-team deal; without it they read as unrelated. `bidAmount` + `waiverResolutionTeams`
appear on claims.

`FetchLeagueBoxscore` returns **one day**, defaulting to the period's last; pass
`scoring_period` and page `eligiblePeriods[]` to reconstruct a week. `pointsHome`/`pointsAway`
`.total` is the whole period, while the lineup rows are that one day.

`FetchLeagueRules` carries roster limits at top level — `maxRosterSize`, `maxActive`,
`numStarters`, `numBench`, `rosterPositions[]` (`league-info` reads them). Scoring lives
at `groups[].scoringRules[]`, as
`points.value` / `pointsPer.value` with `forEvery` — divide to get the per-unit weight.
Watch the abbreviation collision: **`FGM` is used for both field goals *made* and field
goals *missed*** (different category ids). Absent category = not scored.

Weekly team scores: `FetchLeagueScoreboard?season=&scoring_period=<low day ordinal of the
period>`. Enumerate the periods from `eligibleSchedulePeriods[]` rather than assuming;
verify the echoed `schedulePeriod.ordinal` matches what you asked for. Each game carries
`isPlayoffs` / `isConsolation` — exclude both to reproduce `pointsFor`, which reconciles
exactly. Those flags separate bracket games from regular-season ones and nothing more:
**never reconstruct the bracket's shape from them** — `league-info` owns it, and says why
the API cannot express it.

Gotchas:

- **Rate-limited**: sustained rapid requests 403 every endpoint for ~1 min. Throttle to ~1/sec, serial — no thread pools. A sudden 403 on a URL that just worked is throttling, not a bad param.
- An unknown param returns an **HTML 400 page, not JSON**. If parsing fails, that's why — check the param name.
- The response echoes its own enums (`eligibleSorts`, `eligibleFilterPositions`, `sortSeasons`, `eligibleLineupPeriods`) — read those instead of guessing.
- `scoring_period` / `week` is a **1-indexed day ordinal from opening day**, not a calendar date. Map it via `eligibleLineupPeriods[].low.startEpochMilli`.
- Seasons are start-year (`2025` = '25-26). Current season may be empty in the offseason — fall back to the prior year.
- `rankDraft` (on listing + roster players) is the _upcoming_ season's draft-board rank — forward-looking, but only ~top-340 are ranked and it is **not refreshed for offseason trades/signings**. Treat as a weak prior; verify role via web research before acting on it.
- `percentOwnedRatio` is Fleaflicker-wide, not this league.
- `proTeamAbbreviation: "FA"` means unsigned in the NBA — distinct from unowned in our league.
- **Injury status IS in the API** — `proPlayer.injury` on `FetchPlayerListing`:
  `{typeAbbreviaition, description, severity, typeFull}` (their typo, not ours), e.g.
  `OFS / Finger / OUT / "Out for season"`. Present **only when injured** — absence means
  healthy, not missing data. No browser needed for it. What to do with it for valuation is
  `Eval Definitions §Durability`'s call, not a fetching concern.
- No player news or opponent-strength data in the API.

### Draft boards, and two traps

**`FetchLeagueDraftBoard?season=N`** is the draft held in the N offseason, drafting the
year-N NBA rookie class, feeding season N (the `'N-(N+1)` campaign). There is **no season
field in the response body at all** — the label is the query param and nothing else. Only
the last completed draft and the next one exist; other seasons return `{}`.

- **Trap 1 — the label is ambiguous in conversation.** "A 2028 1st" can mean the draft
  held in Sept 2028 or the one Fleaflicker labels for the `'27-28` season. Resolve it
  explicitly by naming **the season whose finish sets the slot** — a season's finish sets
  the *following* offseason's draft (`league-info`). Say which you mean in any output.
- **Trap 2 — placeholder slots.** The site displays pick rows for future drafts with slots
  copied from the last finish. They look like data and are not. **Read a displayed future
  slot as absent** and project it from `strategy/Team Projections.md` instead
  (`eval-pick`). This endpoint is the safer read — it returns `{}` rather than a fake —
  but **`FetchTrades` does serve the fake**.

Structure: `rows[].cells[].slot.{round,slot,overall}` · `rows[].cells[].team` is the
**current** owner while `draftOrder[]` (index = slot) is the **original** owner ·
`tradeId` + `fromOtherTeam: true` mark acquired picks · no `player` key = pick unmade.
`draftOrder[]` is **one array for all three rounds** — no snake, and round-1 lottery
positioning carries into rounds 2 and 3 (`league-info` owns the order rule). Its `rosters`
payload omits `rankDraft`. **A pick moved by an approved-but-unexecuted trade still shows as
the sender's with `tradeId: None`** — cross-check `FetchTrades`.

## Offseason

- The incoming rookie class sits in the **free-agent pool** before the rookie draft runs (`isRookie: true`, zero prior-season stats). Confirm league rules before treating them as addable.
- **The FA-add lock is invisible to the API** (`league-info` for the window — releases and
  trades stay open during it). `FetchLeagueTransactions` still lists offseason adds and drops, `FetchPlayerListing?filter.free_agent_only=true` still reports the whole pool, and `transactionStatus.locked` is an empty `{}` on **every** player, rostered and free-agent alike. **There is no wire-live check here — don't invent one.**

# Notes

- `team-info` maps team owner username → real name.
