# Rookie Draft 2026

Draft held Mon 2026-09-28; slots set by the '25-26 finish. 3 rounds × 12, one order, no snake (`league-info`).

Sources, all live pulls on 2026-09-24:

- Class list: `FetchPlayerListing` (position-sliced, dedup'd), `isRookie:true` and `player_id ≥ 2851` → **93 players**. This is the driver list for the board below, not Dizzle's own "Rookie Ranks, Points" tab (70 rows) — that tab omits 23 of the 93 and includes several UDFA names outside the 93 (not usable here).
- Board: `FetchLeagueDraftBoard?season=2026`, `FetchTrades`. No picks made yet, no pending pick moves, and `Pending Trades.md` moves no picks.
- Dizzle `Dynasty Ranks, Points`, dated 7/10/2026, depth 466. Its `Rookie Ranks, Points` is dated 7/7/2026. Both predate Summer League.
- Hashtag expert `DDTYPE=POINT`, dated 14 Sep 2026, depth 774.
- Hashtag crowd `/keeper`, dated 24 Sep 2026, depth 759. No vote-convergence notice. Its pick rows now cover only the 2027 draft.
- Projections: Sleeper snapshot, 2026-09-12.

Ranks are sourced. BASE and VALUE are modelled (`Eval Definitions §Sourced vs modelled`).

## Our picks

Only **2.09**, which is ordinal **21** and chart label `1.21` (`eval-pick` §3). Our 1.09 belongs to The Don and our 3.09 to Mongol Khans (Henry).

VALUE is **645**, from Dizzle's `1.21 / Karim Lopez` prefix at rank 185. That is Dizzle alone, because the crowd board has no 2026 pick rows left. Dizzle's `Pick Values` band for 1.19–1.24 is `Top 170-200`.

**20 players go before us.** Chalk by BASE leaves Stirtz or Lopez. By Dizzle's class order it leaves Lopez.

The pick's year-1 value is about 0. Every rookie we could plausibly get projects at 11–19 FP/g, against a `REPL` of 23.9–25.1 (`My Team.md`), and the FA auction still offers backfill (`eval-pick` §6). So rank on BASE alone.

## Board

BASE = `V()` of each board's rank at `D` = 456, blended Dizzle 53.3% / Hashtag expert 46.7% (`BASE.md`). The crowd rank is printed in parentheses and is not blended.

A player missing from a board that reaches `D` counts as 0 on that board.

"Class #" is Dizzle's within-class order. It is not a board rank.

| # | Player | Tm | Pos | **BASE** | Dz | Exp | (Crowd) | Class # | FP/g proj | Flags |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Cameron Boozer | MEM | PF/C | **6655** | 11 | 12 | (15) | 1 | 35.5 | |
| 2 | Darryn Peterson | UTA | PG/SG | **5353** | 17 | 21 | (34) | 3 | 29.5 | college injuries |
| 3 | AJ Dybantsa | WAS | SF/PF | **5079** | 15 | 30 | (25) | 2 | 28.9 | |
| 4 | Caleb Wilson | CHI | SF/PF | **3819** | 30 | 37 | (21) | 4 | 30.4 | |
| 5 | Darius Acuff Jr. | SAC | PG/SG | **2640** | 50 | 58 | (68) | 5 | 28.0 | |
| 6 | Keaton Wagler | LAC | PG/SG | **2530** | 54 | 59 | (83) | 6 | 25.7 | |
| 7 | Mikel Brown Jr. | BKN | PG/SG | **2443** | 60 | 57 | (64) | 7 | 24.8 | |
| 8 | Kingston Flemings | ATL | PG/SG | **1894** | 69 | 88 | (100) | 8 | 20.3 | |
| 9 | Brayden Burries | MIL | PG/SG | **1594** | 95 | 87 | (88) | 9 | 22.9 | |
| 10 | Morez Johnson Jr. | DAL | PF/C | **1343** | 102 | 112 | (120) | 12 | 19.7 | |
| 11 | Yaxel Lendeborg | GSW | SF/PF | **1226** | 99 | 140 | (113) | 10 | 25.0 | 24 at debut |
| 12 | Aday Mara | OKC | C | **1071** | 101 | 181 | (184) | 11 | 14.5 | behind OKC depth |
| 13 | Hannes Steinbach | CHA | PF/C | **994** | 125 | 152 | (134) | 14 | 17.2 | |
| 14 | Ebuka Okorie | DET | PG/SG | **925** | 119 | 187 | (195) | 13 | 16.7 | |
| 15 | Dailyn Swain | CHI | SF/PF | **893** | 144 | 153 | (194) | 16 | 18.9 | |
| 16 | Nate Ament | MIL | SF/PF | **815** | 162 | 154 | (181) | 20 | 18.4 | slow year 1 expected |
| 17 | Allen Graves | TOR | SF/PF | **792** | 187 | 139 | (144) | 23 | 13.2 | both Hashtag boards higher than Dizzle |
| 18 | Christian Anderson | CHA | PG/SG | **749** | 153 | 188 | (185) | 18 | 15.6 | |
| 19 | Cameron Carr | LAL | PG/SG | **706** | 145 | 224 | (168) | 17 | 16.4 | |
| 20 | Labaron Philon | PHI | PG/SG | **632** | 161 | 229 | (121) | 19 | 12.4 | |
| 21 | Bennett Stirtz | OKC | PG/SG | **546** | 139 | 404 | (269) | 15 | 11.3 | split: Dizzle 139, expert 404; behind OKC depth |
| 22 | Karim Lopez | MEM | SF/PF | **542** | 185 | 235 | (214) | 21 | 13.3 | |
| 23 | Joshua Jefferson | BKN | SF/PF | **487** | 252 | 189 | (196) | 31 | 14.0 | |
| 24 | Tarris Reed Jr. | SAS | C | **475** | 186 | 280 | (268) | 22 | 13.9 | crowded SAS frontcourt |
| 25 | Zuby Ejiofor | ATL | PF/C | **441** | 227 | 234 | (377) | 26 | 12.9 | |
| 26 | Bruce Thornton | HOU | PG/SG | **414** | 206 | 287 | (341) | 24 | — | |
| 27 | Sergio De Larrea | DAL | PG/SG | **412** | 226 | 254 | (259) | 25 | 7.2 | |
| 28 | Jayden Quaintance | SAS | PF/C | **390** | 253 | 236 | (190) | 30 | 10.0 | knee |
| 29 | Koa Peat | PHX | SF/PF | **351** | 236 | 286 | (208) | 27 | 7.5 | |
| 30 | Richie Saunders | MEM | PG/SG | **349** | 255 | 261 | (288) | 33 | — | torn ACL; likely out most or all of '26-27; 25 years old |
| 31 | Alex Karaban | SAC | SF/PF | **338** | 270 | 252 | (331) | 34 | 14.1 | |
| 32 | Ryan Conwell | MIA | PG/SG | **331** | 274 | 253 | (260) | 35 | — | |
| 33 | Isaiah Evans | MIN | PG/SG | **325** | 254 | 281 | (199) | 32 | 7.0 | |
| 34 | Henri Veesaar | ATL | C | **321** | 276 | 258 | (—) | 36 | 12.5 | ACL (Fleaflicker) |
| 35 | Baba Miller | LAC | SF/PF | **317** | 277 | 260 | (392) | 37 | — | |
| 36 | Emanuel Sharp | SAC | PG/SG | **274** | 291 | 279 | (378) | 39 | — | |
| 37 | Meleek Thomas | CLE | SG/SF | **246** | 237 | 411 | (372) | 28 | 11.3 | split: Dizzle 237, expert 411 |
| 38 | Chris Cenac Jr. | BOS | PF/C | **244** | 240 | 405 | (355) | 29 | 13.4 | split: Dizzle 240, expert 405; raw |
| 39 | Jaron Pierre Jr. | NOP | PG/SG | **157** | — | 262 | (—) | 60 | — | not on Dizzle |
| 40 | Tyler Bilodeau | BKN | SF/PF | **156** | — | 263 | (261) | 48 | — | not on Dizzle |
| 41 | Trevon Brazile | DEN | SF/PF | **129** | — | 284 | (254) | 43 | — | not on Dizzle |
| 42 | Izaiyah Nelson | ORL | SF/PF | **128** | — | 285 | (—) | 46 | — | not on Dizzle |
| 43 | Ugonna Onyenso | DET | C | **87** | 337 | — | (—) | 44 | — | not on Hashtag expert |
| 44 | Braden Smith | IND | PG/SG | **82** | 342 | — | (428) | 40 | — | not on Hashtag expert |
| 45 | Malique Lewis | MIL | SF/PF | **27** | — | 406 | (318) | — | — | not on Dizzle |
| 46 | Felix Okpara | WAS | PF/C | **26** | — | 407 | (300) | 47 | — | not on Dizzle |
| 47 | Tobi Lawal | DAL | SF/PF | **26** | — | 408 | (482) | 55 | — | not on Dizzle |
| 48 | Michael Ajayi | CHA | SF/PF | **25** | — | 409 | (441) | — | — | not on Dizzle |
| 49 | Vsevolod Ishchenko | DAL | PG/SG | **24** | — | 410 | (364) | — | — | not on Dizzle |
| 50 | Dillon Mitchell | BOS | SF/PF | **23** | — | 412 | (379) | 45 | — | not on Dizzle |
| 51 | Tyler Nickel | NYK | SF/PF | **22** | — | 414 | (433) | 54 | — | not on Dizzle |
| 52 | Jack Kayil | NYK | PG/SG | **22** | — | 415 | (409) | 49 | — | not on Dizzle |

`—` means the player has no row on that board (or, in Class #, no row on Dizzle's rookie-class tab).

All 52 of the 93-player 2026 class with a nonzero BASE (a rank on Dizzle dynasty or Hashtag expert) are listed above. The other **41 have no rank on either board** (BASE 0) and are excluded: AK Okereke (LAL), Alpha Diallo (DEN), Boopie Miller (FA), Bryce Hopkins (DEN), Caleb Grill (BOS), Cameron Hildreth (IND), Carson Cooper (MEM), Chance McMillian (FA), Deivon Smith (FA), Ernest Udeh (CLE), Graham Ike (GSW), Hyunjung Lee (POR), Ibrahima Diallo (UTA), Ja'Kobi Gillespie (SAS), Jaden Bradley (TOR), Jayden Nunn (SAS), Jaylin Sellers (CHI), Josh Dix (OKC), Justin Harmon (UTA), Keonte Jones (DEN), Kobe Stewart (FA), Kylan Boswell (CHA), Lajae Jones (GSW), M.J. Iraldi (IND), Malik Dia (NOP), Maliq Brown (SAS), Meechie Johnson (LAL), Nick Martinelli (LAC), Otega Oweh (OKC), Peter Suder (FA), Quadir Copeland (HOU), Rafael Castro (HOU), Reese Dixon-Waters (DEN), Sean McNeil (FA), Solomon Washington (NOP), Terrell Brown (UTA), Tobe Awaka (CHI), Tre Donaldson (MIA), Trey Kaufman-Renn (MIN), Trey Townsend (FA), Wade Taylor (IND).

## At 2.09

Take the highest-BASE player still on the board.

- BASE rows 15–22 cover 893 → 542, and neighbouring rows sit about 50 apart. That is noise between boards, so treat any two players within about 100 BASE of each other as tied.
- To break a tie, lean on the two September Hashtag boards (expert and crowd), because Dizzle's ranks predate Summer League. Among the players we could plausibly get, that favours Graves.
- Positional fit is not a tiebreak here. `Format edges.md` item 3 only applies to a player who produces in year 1.
- Stirtz is a board split, so name the split if you take him.
