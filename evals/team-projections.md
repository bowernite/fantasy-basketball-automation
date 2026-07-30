# Team projections — where each team finishes, and where its picks land

**Projections evaluated: 2026-07-29** (offseason, before the Sept '26 rookie draft).
**Draft-slot rule, slot notation and pick-ownership facts corrected 2026-07-30** — the
projections themselves were not re-run.

**Slots are written `1.01`–`1.12`** throughout, matching every other eval file and Dizzle's
prefixed rows. An earlier revision wrote slot 1 as `1.1` and slot 10 as `1.10`.

Purpose: when a pick shows up in a trade — "The Don's 2028 1st" — look up the
**originating** team's row and read off roughly where that pick lands. Picks move
constantly; this file is keyed to who *produces* the pick, never who holds it.

---

## How a finish becomes a pick slot

**`league-info` owns this rule — read it there, don't derive it here.** In summary: **top 4 by
`recordOverall.rank`** take slots 9–12 in reverse rank order, **not** by playoff advancement
and not by seed; **bottom 8 by record** fill slots 1–8 worst-to-best and then a **lottery
reorders them**, so a bottom-8 slot is a *prior* and must be read off the board.
`draftOrder[]` is **one array for all three rounds**, no snake.

`slot = 13 − rank`, which for the top 4 is **exact and reverses**:

| rank | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| slot | **1.12** | **1.11** | **1.10** | **1.09** |

⚠️ **The two bands are recorded differently in the table below, and it matters.** A top-4
projection resolves to a **single exact slot** (bolded). A bottom-8 projection resolves only
to the **range its rank range implies, marked "prior"** — the lottery can move it anywhere in
the band, so a point estimate there is a fabrication, not a rounding. It is not a small
difference: rank 9–12 spans slots 1.04→1.01, which on Dizzle's prefixed rows is board rank
30→11 and **VALUE 4,075 → 6,756, a 66% swing** (`evals/the-don.md`, `evals/boards-2026-07-29.md`).

⚠️ **Two rules this file used to state are false. Do not reinstate either.**

1. **"Only the top 4 make the playoffs."** The bracket is **6 teams, 3 rounds, top 2 seeds
   byed** (`league-info`, verified off `FetchLeagueScoreboard`), and its seeds tie-break on
   points-for rather than `rank`. The 4-team cut is the **draft** rule, a different cut — a
   team can play in the bracket and still pick 1.07/1.08. This matters directly downstream:
   `team-eval`'s **`Mₜ`** for a counterparty projected **6th** is a bubble **~0.8**, not the
   ~0.5 of a team just outside, which changes whether a deal is sellable at all.
2. **"Playoff teams are ordered by how far they advanced."** Nothing on the '26 board
   evidences it. `recordOverall.rank` is King Christopher **2** and Jesus Christ **3**, and
   `rank` does **not** tie-break on points-for — both went 14-5 and *Jesus* had the league's
   best PF (28,502 vs 27,320), yet ranks below. `13 − rank` then lands them at slots 11 and 10
   exactly, so the pair confirms the record rule, not an advancement rule.

**The '26 board, verified rank → slot** (`FetchLeagueDraftBoard?season=2026` `draftOrder[]`
against `FetchLeagueStandings?season=2025`): `13 − rank` is exact at **10 of 12** positions —
Pascals 1→1.12 · King 2→1.11 · Jesus 3→1.10 · Bathroom 4→1.09 · Yao 5→1.08 · Gutes 6→1.07 ·
Matthew 7→1.06 · Pharaoh 8→1.05 · Mongol 9→1.04 · Han 12→1.01. The **only** exception is a swap
of ranks **10 and 11**: SGA (10th) holds 1.02, The Don (11th) holds 1.03. That is the lottery
`league-info` describes — and it is **not round-1-only**, because the same single order runs in
all three rounds.

**Two cliffs matter, and neither is where people think:**

- **The 4/5 boundary (1.09 vs 1.08) is nearly meaningless.** Anything from 4th to 7th
  produces a functionally identical, near-worthless pick.
- **The real cliff is 8th vs 9th** — only a bottom-4 finish reaches the lottery band
  where a franchise player is actually available.

**Season → draft mapping:** a '26-27 finish sets the **Sept '27** pick, '27-28 → Sept '28,
'28-29 → Sept '29. The Sept '26 draft is already locked off the '25-26 finish.

---

## Master table — projected finish, and the pick it produces

Ranges are the honest uncertainty; the bolded rank is the single most likely finish.
**Treat every rank as ±2–3** (see confidence section).

**Reading the slot columns:** a **bolded single slot** is exact given the rank — the bolded
rank is top-4, where `13 − rank` holds. A **range marked `(prior)`** is a bottom-8 projection:
the range is what the rank range implies before the lottery, and the lottery reorders inside
it. Never collapse a `(prior)` range to its midpoint.

| Originating team | '26-27 | → Sept '27 | '27-28 | → Sept '28 | '28-29 | → Sept '29 |
|---|---|---|---|---|---|---|
| **Pharaoh Mattankhamun-Ra** | 2–8 (**5**) | 1.05–1.11 (prior) | 1–5 (**3**) | **1.10** | 1–4 (**1**) | **1.12** |
| **The Don** | 2–8 (**6**) | 1.05–1.11 (prior) | 1–6 (**4**) | **1.09** | 1–5 (**2**) | **1.11** |
| **Matthew the Apostle** | 2–6 (**4**) | **1.09** | 1–5 (**1**) | **1.12** | 1–5 (**3**) | **1.10** |
| **Bathroom club** (us) | 1–5 (**2**) | **1.11** | 1–5 (**2**) | **1.11** | 1–6 (**4**) | **1.09** |
| **Mongol Khans Freak Militia** | 4–11 (**9**) | 1.02–1.09 (prior) | 4–10 (**8**) | 1.03–1.09 (prior) | 3–9 (**5**) | 1.04–1.10 (prior) |
| **The Gutes of Gotland** | 2–10 (**7**) | 1.03–1.11 (prior) | 3–10 (**7**) | 1.03–1.10 (prior) | 4–10 (**6**) | 1.03–1.09 (prior) |
| **Yao Ming Dynasty** | 4–10 (**8**) | 1.03–1.09 (prior) | 5–11 (**9**) | 1.02–1.08 (prior) | 5–11 (**7**) | 1.02–1.08 (prior) |
| **Jesus Christ and his Disciples** | 1–4 (**1**) | **1.12** | 2–7 (**5**) | 1.06–1.11 (prior) | 4–11 (**9**) | 1.02–1.09 (prior) |
| **Pascals of Pangea** | 1–5 (**3**) | **1.10** | 2–8 (**6**) | 1.05–1.11 (prior) | 3–11 (**10**) | 1.02–1.10 (prior) |
| **SGA-the-Great** | 9–12 (**12**) | 1.01–1.04 (prior) | 7–12 (**11**) | 1.01–1.06 (prior) | 5–12 (**8**) | 1.01–1.08 (prior) |
| **The Han Dybantsy** | 4–12 (**11**) | 1.01–1.09 (prior) | 3–11 (**10**) | 1.02–1.10 (prior) | 5–12 (**11**) | 1.01–1.08 (prior) |
| **King Christopher of Bavaria** | 4–11 (**10**) | 1.02–1.09 (prior) | 6–12 (**12**) | 1.01–1.07 (prior) | 6–12 (**12**) | 1.01–1.07 (prior) |

Sorted by '28-29 projection (i.e. roughly by where the league is heading).

### The short version

- **The three genuinely valuable pick sources are SGA-the-Great, King Christopher,
  and Han Dybantsy** — and only those three. Everyone else's most likely finish implies
  **1.04 or later**, the one exception being Pascals' Sept-'29 (projected 10th, so ~1.03) at
  the far edge of the window.
- **King Christopher is the one the market hasn't repriced yet.** He finished **2nd by
  record** (so his Sept-'26 pick is 1.11 — already SGA's) and his stars still carry
  39–40 FPts price tags. He is a bottom-2 team by '27-28.
- **Our own 1sts are 1.09–1.11 every year of the window** — exact, not a prior, because we
  project top-4 all three years (2nd/2nd/4th → 1.11/1.11/1.09). Cheap currency — spend them,
  and never let a counterparty price our future 1st as a lottery ticket.

---

## Per-team notes

### Pharaoh Mattankhamun-Ra (Matthew7) — 9-11, 26,393 PF
Youngest strong roster in the league; oldest meaningful player is Queta at 27, so
there is **no decline cliff anywhere in the window**. Wembanyama (22, 50.4) and Jalen
Johnson (24, 48.2) are two of the four best assets in the league, with Barnes (24,
40.5) behind them. The 9-11 record came on ~200 lost player-games. The one real
weakness is depth — only 9 players at 25+ FPts/G, which genuinely hurts on a 5-game
NBA night — and that is exactly what fills in as their 20–23 year olds mature.
**The only path to a valuable Pharaoh pick is a Wembanyama injury**, which is not a
branch to be long. Dylan Harper (20) is the best non-top-3 asset.

### The Don (MitchBrault3) — 6-13, 22,996 PF
**The most mispriced team in the league.** 11th on record, 5th in raw top-14 talent.
The '25-26 GP column is a casualty list: Kessler 5, Topić 10, Franz 34, JJJ 48,
Keyonte 54, Luka 64. Median age ~24 with nothing that declines before '29. Kessler is
now cleared and starting next to a post-LeBron, max-usage Luka; Flagg won ROY.
Health normalisation alone is ~+3,500–4,500 net PF. On top of that they hold **four of the top
ten Sept-'26 ordinals** — 1.03 (own), 1.04 (Mongol's), 1.08 (Yao's), 1.10 (Jesus Christ's) — and
**1.09 (ours) makes five** once pending trade 483809 executes. Their own future 1sts are
back-of-round garbage — **1.09 exactly** off '27-28 and **1.11 exactly** off '28-29, with only
the Sept-'27 one still a prior (1.05–1.11, most likely ~1.07) — and the market is still
pricing them off a 6-13 record.
**Never buy their future firsts.** ⚠️ **They are not the win-now-vet counterparty this file
used to call them** (it named Kawhi/Butler/Kyrie/Turner/Poeltl) — that read contradicts the rest
of this paragraph. Everything above says *riser*: the age profile, the pick pile, and caveat 5
flagging them as consolidating firsts into a star. Their window opens **'27-28/'28-29**, by
which point a 35-year-old Kawhi's `Δwₜ` is 0 (`team-eval`). Three of those five names are *Core*
on `my-team-situation`'s current cut (one unbucketed post-execution), so the pitch also tripped
`trades`' walk-away. What they buy is a **young** star; anything we sell them starts from
*Prime sell* and is priced from their seat first (`trades` → *Pricing their side*).

### Matthew the Apostle (RoyceWhite) — 10-10, 27,563 PF
7th on record, **2nd in points-for** — the unluckiest team in the league over a 19-game
schedule, and the deepest. **20 players at 20+ FPts/G** is a structural edge in a
daily-lineup format, and nothing load-bearing ages out: every risk here is injury or
usage, not decline. The catch is the top end — no 45+ player except Maxey, whose usage
is under real threat now that Philadelphia added **both Jaylen Brown and LeBron**.
Ceiling is "consistently 2nd–3rd" unless Castle (21), Buzelis (21), Sarr or Edgecombe
breaks into the 40+ band. **The 1.06 they hold this September is the last pick of theirs
worth anything** — a projected 4th in '26-27 puts their next one at exactly 1.09.

### Bathroom club (us) — 12-8, 27,229 PF
Cade 25 / Duren 22 / Amen 23 / Giddey 23 / Edey 24 / Suggs 25 / Garland 26 is the best
sub-27 top-seven in the league, so the contending window and the young core are the
same thing. '26-27 net change is clearly positive: Kyrie and FVV return from zero
games, Edey goes from 11 GP to Memphis's centerpiece, plus organic growth — against
Butler's ACL, Kawhi's decay, Middleton and Turner. Damping caveat: with 12+ players
already above 30 FPts and only 9 nightly slots, marginal additions are worth less than
face value. Swing factors are Duren's RFA standoff, Edey's two ankle surgeries in nine
months, and Kawhi's frozen Toronto trade.

### Mongol Khans Freak Militia (henry12287) — 7-12, 24,292 PF
**The mid-first trap** — never bad enough to reach the lottery, never good enough to
contend. Edwards (25, ascending) is the real centerpiece, not Giannis. **Giannis is the
single most mispriced asset in the league**: elite rate (48.9) but 36 GP, two right-soleus
strains in one season, has topped 70 games once in seven years, now 32–34 across this
window on a Miami team built to peak in June. The market prices him top-3; in a
total-points-banked format he is top-8 to top-12. Their genuine path up is that
Knueppel, Filipowski and Rollins all had blockers removed *this same offseason*.
Drag: roughly eight roster slots producing nothing.

### The Gutes of Gotland (j0epa) — 11-9, 26,053 PF
**The widest range of any team**, because they posted 6th-best PF while losing ~200
rotation games (AD 20, Murray 14, Trae 16, PG 38, Booker 64). A healthy version is a
top-3 PF group. But the bounce-back is heavily offset: Bam's usage drops with Giannis
in Miami, PG is finished as a starter at 36, Murray may lose his job to Jeremiah Fears,
and Trae takes a usage haircut in Washington. The entire top 8 except Chet Holmgren
(24) is 29+. **Anthony Davis's availability is the biggest single variance item in this
whole exercise** — 20 GP, 33 years old, on a tanking Washington team that has both Sarr
and Ayton.

### Yao Ming Dynasty (Scal) — 11-8, 25,667 PF
Jokić (65.2 FPts/G) is the **only player in the league over 60** — 8 cleared 45 at 30+ GP and
3 cleared 50 (`evals/lineup-math/README.md` §*Is the incoming rate even purchasable?*) — a
structural edge nobody else has, and the reason their availability-adjusted baseline grades 1st. But behind him this is a pile of 26–33 year old mid-tier producers:
roughly 9 decliners against 4 risers, with **not one young player who projects as a
future 40+ FPts asset**. Ayton's collapse to backup C in Washington is already locked in;
don't let anyone price him at 26.7. Flat PF in a rising league means the rank drifts down.
**Jokić's health is the entire floor** — a 45-game Jokić season makes this a lottery team
outright, which is the fat left tail that makes their later picks worth buying.

### Jesus Christ and his Disciples (Brohard) — 14-5, 28,502 PF
**Best actual scoring team in the league two years running**, with three genuine 41+ FPts
anchors in Mitchell, Murray and KAT — nobody else has that. Lillard returning from a
zero-game season (~+1,700 PF) roughly cancels the combined drag of Embiid's usage loss,
Westbrook at 38, McCollum's decline and Wiggins next to Giannis. **The defining fact is
the pipeline: there isn't one.** No player under 26 with a top-30 tail, and both their
Sept '26 1st and 2nd are already traded. Seven players 32+, plus six more at 31 who all
cross 32 during '27-28 — a synchronised cliff. A '29 first from Brohard is a much better
buy than a '27 one.

### Pascals of Pangea (mBone) — 15-4, 27,462 PF, champions
Won the title, and their two biggest '26-27 variables both point **up**: Markkanen's 42
GP was Utah actively tanking him (that tank is over) and Sabonis returns from meniscus
repair. Clingan (22) **led the entire NBA in offensive rebounds** — in a format where
OReb counts double, that's the single best format fit on any contender's roster.
But eight players are 32+, with DeRozan and Harden both currently unsigned, and that's
~2,500–4,000 PF/season sourced from players who'll be gone or near-zero by '28-29.
Clingan is the only young piece with a genuine 40+ tail. Hardest team on this list to
pry anything loose from — they just won, and the pick they produce is **1.12 this September
(locked, on the board) and exactly 1.10 the next** on a projected 3rd. Only their Sept-'29
pick (projected 6th) enters prior territory.

### SGA-the-Great (KIMJONIL) — 7-12, 22,658 PF
**The only structurally bad team in the league** — dead last in top-14 talent and last in
top-9 by 33 points, with *no availability excuse* (their availability-weighted rank is
essentially their raw rank). Two stars and a cliff: the third-best player scored 28.1.
Median age ~23, but fourteen 16–25 FPts players is not a substitute for six 30+ ones when
you must fill nine slots nightly. **Their own future 1sts are the most valuable in the
league over this window — better than Han's, because Han bounces back and they don't.**
Their 1.02 is a blue-chip; the five 2nds are volume, not quality (a player who tops out at
18 FPts/G has zero value here, and five of them is not one good player). **Live risk:
the owner trades SGA (28) or Şengün (24)** — that deepens the tank and makes their '28/'29
1sts better still.

### The Han Dybantsy (t27marino) — 0-19, 20,159 PF
**The 0-19 is a health artifact, not a talent floor** — they were 9-10-1 / 23,198 PF (7th)
in '24-25. Haliburton missed all 82; Tatum played 16. Tatum returned from the Achilles at
21.8/10.0/5.3 and **just inherited Jaylen Brown's usage** now that Brown is in Philadelphia;
Haliburton is "extremely optimistic" for opening night; NAW won Most Improved. **Do not pay
1.01-adjacent prices for their future firsts.** That said, the bounce has a ceiling: even
using healthy '25-26 rates, their raw top-14 talent still grades 11th of 12, and the bench
is rotting (Lopez 38, Clarkson 34, McConnell 34, Dunn 32) with only Egor Dëmin behind it.
Mid-lottery at best. **The right move is to sell that 0-19 perception, not buy it.**

### King Christopher of Bavaria (chris96) — 14-5, 27,320 PF
**The cliff is already here, not "a year or two" out** — this is the single biggest
correction in the file. The offseason gutted them: DiVincenzo tore his Achilles (−2,157 PF,
he was their 82-game iron man), Vučević signed in Orlando as the **backup** center,
Yabusele **left the NBA** for Panathinaikos, Bruce Brown is unsigned, and Jrue Holiday is
buried behind Morant and Lillard. LeBron (41) is in Philadelphia on a 2yr/$8M deal he has
publicly framed as his last — assume '26-27 is it. Curry (38) is losing months to knee
issues; only Durant is genuinely flat rather than declining. Net ≈ **24,500–25,500 PF**,
which would have been **9th in PF** last year — and the league is rising beneath them.
Dyson Daniels (23, 2nd in the NBA in steals, signed through 2029-30) is the lone
long-horizon asset. **He is the seller to target and his stars still price on last
year's numbers.**

---

## Confidence and how to use this

**Rank precision is low; direction is high.** A 19-game schedule is enormously noisy —
Matthew the Apostle finished **7th on record with the 2nd-best points-for**. Every
most-likely rank here should be read as **±2–3**, and PF is the load-bearing signal, not
W-L. What this file is good for is the *shape*: which teams are rising into the top and
which are falling into the lottery. What it is not good for is the difference between a
5th- and a 7th-place finish.

**Where the ranks came from.** Four agents each projected three teams in depth, then I
reconciled them into a single valid 1–12 ordering per season. That reconciliation was
necessary — projecting in isolation, they collectively placed four different teams at
"2nd" in '26-27, and rank is zero-sum. Where I moved a number away from the specialist
agent's estimate, the disagreement is worth knowing:

| Team | Specialist said | Filed here | Why I moved it |
|---|---|---|---|
| The Han Dybantsy '26-27 | 7th | 11th | Even at full health their raw top-14 talent grades 11th of 12 — the health bounce is real but lands them mid-table at best, not 7th. |
| King Christopher '26-27 | 7th | 10th | The agent's own PF estimate (24,500–25,500) was a **9th**-place PF number *last* year; the league rises beneath them. |
| Yao Ming Dynasty | ~6th | 8th–9th | Their availability-adjusted baseline grades **1st in the league** on Jokić alone, which is in real tension with a 6th-place projection. Split the difference; flagged below. |
| Gutes of Gotland '26-27 | 5th | 7th | Healthy raw top-14 talent is 8th; the injury bounce-back is partly offset by four separate usage downgrades. |

**Unresolved tension worth watching: Yao Ming.** Two independently computed
availability-adjusted baselines both rank them the strongest roster in the league,
driven entirely by Jokić. The projection says 8th–9th and falling. Both can't be right.
The bear case (a decaying supporting cast in a rising league) is the one filed here, but
if Jokić plays 75 games this is a top-4 team and their picks are worthless.

**Global caveats:**

1. **This is where picks LAND, not who OWNS them.** The draft board serves only the upcoming
   draft (`FetchLeagueDraftBoard?season=2027` returns `{}`), but **`FetchTrades` does carry
   future ownership** — `originalOwner` names the team a traded pick originates from (verified
   on pending trade 483809: of the two 2027 2nds coming to us, one is The Don's own and one is
   King Christopher's). ⚠️ Its `slot` values for a future season are **placeholders keyed to
   the current order**; the '27 order is set by the '26-27 finish.
   **Corrected — two of these were previously reversed.** Traded '26 firsts, read off
   `draftOrder[]` vs the round-1 cells: Mongol's → **The Don** · Yao Ming's → **The Don** ·
   **Jesus Christ's → The Don** · **King Christopher's → SGA-the-Great**.
   **Verify ownership on `FetchTrades` before trading on any row above.**
2. **The 2027 draft class is a clear step down from 2026.** ESPN calls it "indeterminate";
   no prospect currently projects as a guaranteed lottery pick, the high-school class
   underwhelmed, NIL kept talent in college, and international supply is thin. **Discount
   2027 firsts against 2026 firsts** independently of where they land.
3. **The 2026 class is strong** — 3–5 likely All-Stars, headlined by Dybantsa / Peterson /
   Boozer / Caleb Wilson. Dynasty-fantasy consensus reorders to **Boozer #1** (biggest usage
   vacuum in the class — Memphis traded away Morant, Bane *and* JJJ). Under this league's
   weights, Caleb Wilson is arguably the best fit (1.5 stl + 1.4 blk ≈ +7.3 FPts/night,
   and his 25.9% college 3P is near-costless here). Class depth thins hard after rookie
   pick ~20.
4. **Rookies barely move the needle in year 1.** From '25-26 only Cooper Flagg (37.3)
   cleared 33 FPts; most rookies sat under 20, i.e. below the useful-filler band. **A '26
   draft haul is a '27-28 / '28-29 asset.**
5. **Owner behaviour is not modelled** and is the largest unmodelled variable. Several
   flagged scenarios — The Don consolidating four firsts into a second star, KIMJONIL
   selling SGA, chris96 finally selling his vets — would each move a projection 2–4 places.
6. Ages and NBA situations were web-verified as of 2026-07-29 (the API carries no age,
   injury, news, or projection data). One digest error found: Moritz Wagner is on ORL,
   not BKN.

**Source detail:** full per-team workups (rosters, ages, health, swing factors) live in
the session scratchpad as `proj_A.md` (Pascals, Jesus Christ, King Christopher),
`proj_B.md` (Bathroom club, Yao Ming, Gutes), `proj_C.md` (Matthew, Pharaoh, Mongol),
`proj_D.md` (SGA-the-Great, The Don, Han Dybantsy).
