# Eval Definitions

Single source of truth for every shared definition, formula and threshold used to value a
player, a team or a pick in this repo. **Nothing here is dated or team-specific** — no board
stamps, no measured `REPL` figures, no roster numbers. Those are measurements and belong
in the dated output that produced them (`evals/*.md`, `evals/teams/*/*.md`,
`evals/lineup-math/`).

**Cite this file by section (`Eval Definitions §X`) instead of restating any of it.** Test
before writing a sentence anywhere else in this repo: if it would be true and word-for-word
identical for every player, every team and every trade, it's a definition — cut it and cite
this file instead.

Load `eval-team` for when and how to apply this; `eval-pick` for picks; `trades` for
negotiation procedure; `my-team-situation` for our own roster's read. This file is the
formulas and thresholds those skills apply — it does not replace any of them.

# The three layers

Every eval publishes three things, side by side, never folded into one number:

| Layer | What it answers | Where it comes from |
|---|---|---|
| **BASE** | Market price, dynasty-wide — what he costs | External boards (§BASE) |
| **`Δw`** | Wins added to a specific roster, this season | The sim (§Δw) |
| **`SIT`** | How much a win is worth to that team right now | Judgment: contending / fringe / tanking (§SIT) |

**BASE owns everything multi-year** — trajectory, age, upside, risk: the boards price all
of it into the rank, and nothing in this repo re-derives or stacks on top of that
(objective: `CLAUDE.md` §Objective). **`Δw` owns our format** — scoring weights, the 9
daily slots, the real NBA calendar, this roster's shape. Neither replaces the other; the
gap between them is the signal, and `SIT` says which one the current season should listen
to.

**There is deliberately no exchange rate between BASE and `Δw`** — no constant converts
wins into BASE units, and none may be derived or remembered: any measured rate is a median
of a wide distribution, so a derived constant manufactures precision the inputs don't
have. A deal that needs one to look good is a tie (§VERDICT).

# At a glance

Plain-English gloss of every column and metric. Full definition and edge cases are in the
section of the same name below — read those before using any of these.

- **BASE** — blended dynasty board rank, converted to a value. Pure market price; no
  adjustment for injury, role, contract or age.
- **`FPts/G`** — fantasy points per game under our scoring, last season actual. Reporting
  only.
- **`FPts/Gp`** — projected per-game stats scored under our rules. The rate `Δw` runs on.
- **`GP`** — games played last season. A reporting column: never quote it as next season's
  availability, and never hand-feed it anywhere (`GPp` is the projection, and it reads the
  pool itself).
- **`Δw ours` / `Δw theirs`** — sim-measured wins added on that roster, this season.
- **`AGE`** — age in years, from date of birth.
- **`ELIG`** — position-eligibility slot group: centre, guard, or forward.
- **`SIT`** — a team's situation: contending / fringe / tanking.
- **`LATE`** — durability tiebreak for whether a player plays down the stretch and into
  the playoffs, not just how many games he plays overall.
- **`GET`** — how gettable a player is from his current owner. Judgment, not a value.
- **`ACQ`** — whether a player is realistically available to acquire at all, apart from
  what he's worth.
- **`σ`** — confidence that the sim's ordering of two adjacent rows is real, not noise.
- **VERDICT** — the accept/reject judgment for a concrete deal: `ΔBASE` and `Δw` read
  against `SIT`.

# BASE

Blended points-format dynasty board rank and nothing else. **No adjustment by us for
injury, durability, role, team situation, contract or aging** — the rank prices all six.
**This binds BASE only**: the rate and `GP` feeding `Δw` are projections (§Δw). BASE is the
market price, not the truth; divergence is the edge. Picks: `eval-pick`.

| Board          | Weight | Skill                |
| -------------- | ------ | -------------------- |
| Dizzle Points  | 40%    | `dizzle-dynasty`     |
| Hashtag Points | 35%    | `hashtag-basketball` |
| Hashtag crowd  | 25%    | `hashtag-basketball` |

Dynatyze (`dynatyze`) is too shallow to blend — reference only. Before adding a source,
count analysts, not boards (`eval-player`).

**`V()` each board's rank, then weight-average the values** — never average ranks first.

```
D    = teams × roster_size          # rostered players; past D a player is free
a    = √D                           # rank a is worth half of rank 1
V(r) = 9999 × (a+1)/(D−1) × (D−r)/(a+r)     for r < D, else 0
```

`roster_size` = **the size in effect for the season being valued** (`league-info`); flag it
whenever current and announced differ. **BASE is comparable only within one `D`** — re-run
every eval when the league resizes.

## Depth and absence

Fetch every blended board as deep as it goes, record that depth (a dated fact — belongs in
the eval, not here), then per board per player:

|                                                      |                                                                  |
| ---------------------------------------------------- | ---------------------------------------------------------------- |
| rank < `D`                                           | `V(rank)`                                                        |
| rank ≥ `D`, or absent from a board that reaches `D`  | **0** — absence is a statement of value                          |
| absent from a board that stops short of `D`          | renormalise that board's weight away, **for that player only**   |

Renormalise only where absence and below-depth are indistinguishable.

⚠️ **A board that puts a player past `D` while another ranks him inside 200 is a
disagreement, not a price.** The blend still averages it, but hides the dispersion: a board
ranking a player past `D` is saying *he is not rosterable*. **Flag any row whose per-board
ranks straddle `D`** (§Output `split`). A row that's both split that way and a wide
low-BASE/high-`Δw` gap (§Δw) signals the boards pricing a role or career risk no column
here carries — never publish it as a buy without naming the split.

**Never divide by `VALUE`** — no BASE-normalised ratio, anywhere; compare in absolute terms.

# Columns

Alongside BASE, never folded in. Sources: `get-league-info`.

| Col       | Source                                |                                                                                                                                                             |
| --------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FPts/G`  | `FetchRoster?season=` `seasonAverage` | last season **actual**, already scored under our rules — reporting only                                                                                     |
| `FPts/Gp` | `projections`                         | projected stats scored under our rules — **the rate `Δw` runs on**. Print it beside `FPts/G` so the divergence is visible                                    |
| `GP`      | `seasonTotal / seasonAverage`         | last season **actual** — reporting only                                                                                                                     |
| `GPp`     | `sim.project_gp`                      | the projection `Δw` runs on — print it beside `GP` so the divergence is visible                                                                             |
| `Δw ours` | `sim.py players` · `sim.incoming_wins` | sim-measured. Already ours → `players`. Not yet ours → `incoming_wins` against `basis()`, never a hand-edited roster file (§Δw)                              |
| `AGE`     | `FetchPlayerProfile` `detail.dob`     | ms epoch, parse **UTC**. Never `detail.age`. **As of the eval's derivation date** — one convention, everywhere                                              |
| `ELIG`    | `proPlayer.positionEligibility`       | multi-position is underpriced. Slot group, as `sim.py` maps it: `{C}` → centre · ⊆ `{PG,SG}` → guard · anything else → **forward** (so a PF/C is a forward) |
| `LATE`    | §LATE                                 | judgment                                                                                                                                                      |
| `GET`     | `trades` §*What other owners price on* | judgment — defined and owned there, not here. **Counterparty tables only** — meaningless on our own roster                                                   |
| `ACQ`     | §Δw                                   | judgment, cause named. **Both sides** — ours names our untouchables, theirs names theirs                                                                     |

**`σ` is never a table column** (§σ) — it's a footnote, not a row-by-row read.

**A player with no last-season sample has no `FPts/G`** — print `–`. He still has an
`FPts/Gp`. **Never print a projection in the actuals column**, and never the reverse.

BASE and `FPts/Gp` will disagree; that's the signal. A wide `FPts/G` → `FPts/Gp` gap is a
second one — the projection pricing a role change the last season cannot show.

**No format-fit column, and never a format-adjusted BASE.** Our scoring weights
(`league-info`) are already inside `FPts/G` and `FPts/Gp`; the structural half — eligibility, 9 daily
slots, NBA schedule — is already inside any sim `Δw`, which runs the real calendar. A third
column double-counts one or the other. Use the weights to _explain_ a BASE↔`FPts/G` gap,
never as a separate score. Reason about the profile directly only with no usable sample
(rookie, tiny `GP`, role change).

**Never diff a board rank against an our-format ranking.** The boards are dynasty and any
our-format ranking is one season, so the residual measures age, not format.

## Sourced vs modelled

The classification every eval must flag, enumerated once instead of relisted per file:

| Sourced (a market/API fact) | Modelled (we derived it) | Judgment (not a value) |
| --- | --- | --- |
| Per-board ranks, BASE's inputs | `FPts/Gp` (a sourced stat line, scored by us) | `GET` (`trades`) |
| `FPts/G`, `GP` (last season actual) | `GPp` (`sim.project_gp`) | `ACQ` (§Δw) |
| `AGE`, `ELIG` | `Δw` (theirs and ours) | `SIT` (§SIT) |
| Body counts, roster limits, wire facts (trade terms, dates) | `REPL` (sim-internal) | `LATE` (§LATE) |

**`FPts/Gp` is modelled, not sourced** — the stat line under it is someone else's forecast,
and both the scoring and the DD/TD estimate are ours. Cite it as a projection, never as a
price.

**A sourced price and a modelled figure never bracket a range** — BASE (sourced) and `Δw`
(modelled) are a gap to read, not an interval, and neither is a midpoint of the other.
File-specific sourced facts (e.g. a particular trade's terms) are additive to this table,
not a reason to re-derive it.

# `Δw` — wins added, sim-measured

`sim.py` prices a roster change in **expected wins over the 20 scored matchups**, on the
real NBA calendar, with optimal nightly lineups and projected `GP` on both sides.
`evals/lineup-math/method.md` and `findings.md` own the method, the measurements and the error
bars —
re-run it, never quote a remembered figure.

- **One season, one roster.** Multi-year value is BASE's, entirely (§The three layers).
  Never sum `Δw` over future seasons, never discount it, and never apply an aging term or
  age haircut inside a win delta — age is priced in BASE.
- **Compute it for every rostered player on every roster touched — never a shortlist,
  either side** (`sim.py --roster <team>.json players`). A blank reads as zero regardless
  of the caveat next to it; `–` must not appear in the column for a rostered player.
- **A player who is not ours yet gets `incoming_wins`, never a hand-edited roster file.**
  `sim.incoming_wins(sim.basis(), sim.our_roster("their.json"))` seats him in one of
  `basis()`'s padded slots and prices him against the same replacement body of his own slot
  group that `player_wins` prices a departure against — so `Δw ours` and `Δw theirs` are
  comparable and both read positive for a player worth having. **It refuses on a roster of
  38 real bodies** (ours, from Sept '26): with no pad left to spend, somebody we field has
  to go, and the candidates sit a rate point apart down where `replacement`'s line no longer
  ranks them — a coin flip that would still print as measured. Pass the 37 you would
  actually field, and name the body you dropped.
- **Never sum `Δw` across pieces.** It is marginal against the roster as it stands and
  sub-additive under the 9-slot cap — price a multi-piece side with one joint
  `sim.run(sim.swap(...))`, never by adding rows. A pick has BASE and no `Δw`: it enters
  a deal through `ΔBASE` alone (`eval-pick`).
- **Always state the counterfactual.** "If he vanished and the slot went empty" and "if we
  swapped X for him" differ by the whole value of X.
- **Compare rosters only at a common body count** — pad both to the `roster_size` being
  valued (`sim.basis()`). A roster measured short has a low replacement level and every
  player on it reads too valuable.
- **`Δw theirs` prices only what they give up inside a concrete deal.** It predicts
  neither our gain nor what they will accept (`trades` §*What other owners price on*) —
  never target, sort or shortlist off it, and never call a low figure "cheap to buy".
- **The rate behind `Δw` is projected, never posted** — a sourced per-game stat line scored
  under our rules (`projections`). It already prices a changed role, a returning injury and
  a rookie's step forward, so **never adjust it by hand for any of those**. A player the
  feed does not carry keeps last season's average and must publish `noproj` (§Output).
- **One source is a house view, not a market.** Where a projection and last season's
  `FPts/G` diverge widely, say which one the read leans on.
- **`Δw` still under-rates ascending youth** — one season, and a projection is a
  next-season forecast rather than a career curve; trajectory is BASE's job. Never read a
  low `Δw` on a young player as a sell signal.
- **A high-`Δw`/low-BASE row is either a format/roster edge or a rate the boards doubt.**
  Check the flags and the per-board ranks before calling it a buy — a gap you cannot
  explain is a finding about our inputs, not about the market. The boards and the
  projection are separate opinions; a row where they disagree is the finding.
- **Team-specific, never a price.** What to pay comes from `GET` and the negotiation, not
  from our `Δw`.

**Untouchable is a separate column, `ACQ`, not an excuse to skip `Δw`.** Mark
`✗ untouchable` + one-line cause (age/tier, declared keep) for names with no realistic
path — still compute `Δw` for them. `ACQ` is judgment, same tier as `GET` (`trades`) —
never summed, never in VERDICT.

# σ

`sim.py players` prints σ as the gap to a neighboring row, in sigmas of the sim's own
Monte-Carlo noise (3 independent 200-trial seed blocks). It measures whether the sim
resolves the *order* of two adjacent rows — nothing about tradeability.

- **State no order below ~2σ** — treat the rows as an unordered tie, and say which
  ordering σ belongs to (it can differ from the published sort).
- **Never a printed table column.** One footnote below the table naming the adjacent-pair
  ties (`Name/Name X.Xσ`). Above ~2σ the magnitude carries no further meaning.
- **Monte-Carlo resolution is not decision resolution.** A gap can clear 2σ and still be
  under ~0.1 wins — a real order, and too small to trade on.
- A decision that leans on one pair's ordering computes σ for that pair on demand.

# `SIT` — contending / fringe / tanking

One label per team — ours and any counterparty's — dated. Assign from standings
(`FetchLeagueStandings`) plus `evals/Team Projections.md`; ours is `my-team-situation`'s
to own. The projections carry ±2–3 ranks of noise, so the label is **coarse on purpose**:
where a team sits on a boundary, say so and carry both readings rather than forcing one.

What the label changes — what that team should pay up for and sell down:

| `SIT` | Up | Down | `LATE`? |
| -------------- | ---------------------- | ---------------------- | ------- |
| **Contending** | `Δw`, `FPts/G`, `GP` | `AGE`                  | yes     |
| **Fringe**     | `Δw` + BASE evenly   | —                      | some    |
| **Tanking**    | BASE, youth, ceiling   | `Δw`, `FPts/G`, `GP` | no      |

Prospects: weight the tail — `P(top-30 asset)`. Ceiling >> floor; a safe starter is
near-worthless to a tanker.

Fringe-now-contending-later changes what a team buys today — that read is
`Team Projections.md`'s, quoted with its date.

# VERDICT

Objective: **maximise `Σ P(title)` over the seasons we intend to contend**
(`CLAUDE.md` §Objective).

For a concrete deal, publish both deltas and judge them against our `SIT` — never fold
them into one number:

- **`ΔBASE`** — both sides on the same curve, picks included (`eval-pick`).
- **`Δw`** — one joint sim run per side of the actual pieces (§Δw): ours on our roster,
  theirs on theirs.

The rule, by our `SIT`:

- **Contending: buy wins.** Accept a modestly negative `ΔBASE` for a clearly positive,
  durable (`LATE`) `Δw`. BASE already contains the market's price on this season, so this
  is a deliberate premium on current production — which is why it is capped at
  **modestly** negative, never at "whatever the wins justify". **Never ship large BASE for
  small wins** — that sells the next decade for noise.
- **Fringe:** both deltas ≥ ~0, or pass. Wins that don't move title odds aren't worth BASE.
- **Tanking:** `ΔBASE` decides; `Δw` is ~irrelevant.

**If the verdict flips on how you weigh the two columns, it's a tie.** Report it as a tie
and decide on negotiation grounds — `GET`, deal shape, flags — or improve the deal. Never
invent a conversion rate to force a sign (§The three layers).

## Ranking two offers

Score each against the status quo — `ΔBASE` and joint-sim `Δw` per offer — and compare
column by column. An offer that wins both columns wins. Split columns → the `SIT` rule
above; still split → a tie, reported as one, never broken on narrative.

# `LATE` — _when_ games are missed

**Contenders-only tiebreak, never a discount on BASE, never sized** — don't cite
season-points math, which is blind to it. A durable trait; **never read it off one season.**
Causes, most predictive first: **age** · NBA team habitually out of it late · chronic
soft-tissue or load-management history. `✓✓` reliable · `✓` fine · `–` unknown · `✗` risk — and
**always name the cause**: block absences can remove a playoff window; team-incentive risk
carries no dynasty weight and needs rechecking yearly. Score off `AGE` and pool `GP` (`sim.py
gp`) in **rotation seasons** — a pool season at rate **≥ 15**; below that `GP` measures _role_,
not health. **The same call applies inside a qualifying season**: in a player's **first one
or two** seasons, an under-60 year spent earning a rotation spot (bench-to-starter climb,
DNP-CDs before he won minutes) measures _role_, not health, same as a sub-15-rate season —
don't count it toward `✗`/`✓` without checking; name the cause (injury vs. earning-time) for
every under-60 season cited. `✗` at **age ≥ 34**, a **whole season missed**, or **≥ half** the
rotation seasons under 60 GP · `–` under **3** rotation seasons · `✓✓` none under 60 · `✓`
otherwise. **Where discounting an earning-time season drops a player under the 3-season
floor, the read is `–`, never `✗`** — thin evidence is unknown, not risk.

⚠️ **Season `GP` is a durability screen, blind to timing** — it bounds `LATE`, never
evidences it. State that wherever the column is published. Nothing here measures
bracket-window availability, so `LATE` stays unsourced judgment: it may break a tie, and
it may never be sized, folded into `Δw`, or used to reprice a row on its own.

⚠️ **"NBA team habitually out of it late" is not scored in this repo** — no in-repo source
for NBA standings, and dynasty value gives team-incentive risk no weight beyond the tiebreak
above. Check by hand if a call turns on it.

⚠️ **A screen, not a verdict. It is blind to *when* in the season games were missed** — the
one thing `LATE`'s name promises and none of its inputs measure.

# Where our format pulls off consensus

**Deviate from the boards only where our scoring weights, the 9-slot cap or a roster's shape
make the answer differ from the market's — and only where the effect survives the stated
error bars (`evals/lineup-math/findings.md`).** Everything else is in BASE (§BASE): no column,
no discount, no model. Anything that can't name a direction and a magnitude is noise.
**The closed list:**

1. **`Δw`** — the 9-slot effect, computed rather than asserted. Value is bimodal: the
   middle tier is both what to trade _from_ and what to buy cheaply. Sub-replacement bodies
   still pay as bodies; never price them at 0.
2. **Body count is a price, and a steep one — so default to many small swaps.** At **equal
   BASE paid out**, N-for-1 at N≥3 is value-neutral to negative against the same BASE spent
   on separate 1-for-1s. Cap consolidation at 3-for-1, dregs only. **Compare the two shapes
   by joint sim at matched BASE** — never off rank alone, and never equate a board rank with
   an `FPts/G` figure. The price is **structural**, so **never present it as a backfill
   effect.** Backfill flips no sign; price a body by backfill availability at the moment it
   must be **fielded**, not when the trade is made. **Read the actual multiple off
   `evals/lineup-math/findings.md` §*Consolidation is not the lever*, never off a remembered
   number** — the ladder there is the measurement; this is only the rule.
3. **Multi-position eligibility**, and forwards over equal-rate guards/centres. **Already
   inside any sim `Δw` — never apply it on top of one.** A tiebreak only where no sim run
   exists (no usable sample), against _that_ roster's tightest slot group — recheck every
   time, never carry a count or a premium forward. **Read the size off
   `evals/lineup-math/findings.md` §*Positional premium*, never off a remembered number** — it is
   a fact about our roster's current shape, so it re-cuts whenever that changes.
4. **`LATE`** — above. Tiebreak.
5. **Light-night coverage — a property of the roster's coverage of the NBA calendar, not of a
   player.** So it is never a column, never in BASE, never a per-player premium, and
   **already inside any sim `Δw` for a player with a real NBA team — never apply it on top of
   one.** An **acquisition-time tiebreak only**, where the sim has no real team to run on (an
   auction candidate, an `fa` row, a `sim.star()` body): rank on `(rate − R) × GP` first, then
   among bodies close enough in projected rate at comparable `GP` prefer the NBA team covering
   **nights we don't already cover**. What pays is the count of distinct light nights the
   roster reaches, never a body's own night count, and **it saturates**.
   **Spent on the downside, not the upside**: a whole auction steered right is worth about the
   ~0.1-win floor — a real order still too small to trade on (§σ) — while stacking the seven on
   one schedule costs several times that. **A free ordering rule and nothing more** — never pay
   a pick, a body or a rate gap wider than the measured band for a schedule. The **rate-point
   threshold is a function of the body's grade**, roughly halving from auction grade to a real
   producer, so read the row that matches the body. It, the saturation point and what a steered
   auction is worth are measured in `evals/lineup-math/findings.md` §*Light-night coverage* —
   read them there, never off a remembered number, and treat them as re-cut every season.

# Durability

Our format prices a missed game the same way the boards do: **no format-derived injury
adjustment**, never stacked on BASE, and **no fragility discount** — lineup lock-in doesn't
change that. **Never accept less production to buy durability or lower variance**, and no
third penalty on a fragile star bought with bodies.

Spend the effort on **expected `GP`**, regressed hard and **identically on both sides of
every deal**:

- **Never hand-type `GP`, and never use current injury _status_** — a this-season fact in a
  dynasty league. Take it from `sim.py gp`, `--roster their.json` for a counterparty.
- **Last season's `GP` and rate only — no multi-season average, no age.** Neither beats one
  season. **`GP` is a defensible input, not a precise one** — never argue a trade on a few games.
- **`GP` is projected off last season's _actual_ rate, never the projected one** — that is
  the input the fit was built on, and a projected rate through it recalibrates every `GPp`
  in the study against a variable it never saw (`projections`).
- **Never take a published `GP` projection at face value.** Measured against what happened,
  external feeds run optimistic and compress the spread, and lose to `sim.project_gp` on the
  players we trade despite ordering players better than it does
  (`evals/lineup-math/findings.md` §*GP is the dominant input* owns the figures).
- **Flag, don't patch, two blind spots:** a fragment last season (**25 games or fewer** — the
  band has **no lower bound**, since a 5-game season is *present* in the pool rather than
  absent and is the thinnest evidence of all); and a whole missed season, absent from the fit
  rather than a zero — the projection is expected GP _given he plays_, blind to whole-year
  risk. **Both cap what a `Δw` built on them can claim** (§Δw), and the flag travels with the
  row (§Output).

The actual `GP` projection formula and its cross-validation are measured, not defined —
`evals/lineup-math/findings.md` §*GP is the dominant input* owns the coefficients; this file
owns only the rule for how to use them.

# Non-factors — canonical list, do not spend effort

Real-life contracts · NBA depth charts · same-NBA-team stacking · fragility concentration ·
absence _pattern_ for season points · variance from a normal-sized trade · **slot-group
balance as a standing target**. Never reach for a variance argument to justify a move that
doesn't pay in points. Same-NBA-team stacking is a non-factor **in its own right**; it enters
only as light-night coverage (§*Where our format pulls off consensus* 5). **Don't restate this
list elsewhere — cite this section.**

**Never name a roster's slot-group shape as a weakness, a buy criterion, a preferred return
or a walk-away** — `Δw` prices it already, and a shape count expires as the roster turns
over. §*Where our format pulls off consensus* 3 is its only sanctioned use.

# Output — what an eval publishes vs what it cites

**The player table starts within the first 10 lines of the file** — a one-line header (date,
roster identity), then the table. Everything else — the dated header stats, the
shape/read/picks sections — follows it. The table is what a reader opens the file for; don't
make them scroll past prose to reach it.

**An eval is a current-state snapshot, regenerated rather than amended.** No eval history
("moved from X to Y", "the previous version", "re-derived on"), no trade narrative (executed,
historical or reconciliation), no re-derivation commands. Roster composition is stated, not
justified; a pending trade that would change it gets one line above the table. See
`eval-team` §Output for the full cut list.

Header (still near the top, alongside/just after the table): date · every board's update
stamp **and depth** · the team's `SIT` · the `REPL` the sim used. These are measurements —
they belong in the eval, not here, even though the blend weights and curve that produced
them (§BASE) do not.

Table: per-board ranks, so outliers are traceable, then every §Columns column plus
`Δw ours` — `LATE` included, cause named. `–` = off that board, distinct from
board-withholds-ranks. Print the actual `GP` and note the projected `GP` behind `Δw`
wherever the two diverge. Re-derive from scratch; never copy an older eval's header or
columns. **No `σ` column** (§σ) — instead, one footnote below the table naming any
adjacent-pair ties under ~2σ.

**"Re-derive from scratch" binds modelled figures.** A sourced wire fact (pick ownership,
trade-block listing, trade terms) is quoted from its latest recorded fetch **with that
fetch's date**, and flagged unverified when it wasn't re-fetched this session — never
silently carried as current.

**Sort on BASE, both our roster and a counterparty's.** Never on `Δw theirs` — sort order
reads as buy priority. **Bold BASE and `Δw` only.** Where a counterparty eval names buy
targets, give each a gettability read (`trades`) — **never infer it from any of our own
value columns.**

**A flag travels with the row.** Any caveat an eval attaches to a player **must reappear
wherever that row is reused, in the table, not in prose below it.** A derived file that
reprints BASE and `Δw` without them is republishing a number its own source already
qualified, and the qualification is usually the reason the row looks interesting.

⚠️ **A flag qualifies a figure; it never resizes one.** Nothing here may be priced twice —
if an input already moves `Δw` or BASE, the flag on it says *how thin the evidence is*, not
*subtract more*. **Never discount a row for a flag it already carries**, and never add a
flag whose whole content is something a column already prices.

The canonical codes, one `flag` column, blank where none apply:

| | |
| --- | --- |
| `split` | per-board ranks straddle `D` — one board calls him unrosterable (§BASE) |
| `1brd`  | only one board contributes a nonzero value to BASE — renormalised away or hard 0 elsewhere (§BASE) |
| `frag`  | `GPp` projected off a season of ≤25 games (§Durability) |
| `miss`  | a whole season missing from pool history (§Durability) |
| `rotN`  | fewer than 3 pool seasons at rate ≥ 15 — the role itself is not yet evidenced (`sim.py players`) |
| `noproj`| no projection — the rate is **last season's average**, not a projected one (`projections`) |
| `stale` | a wire fact after the inputs — `GPp`/`FPts/Gp` cannot see it. Name the event |
| `bear`  | board-cheap but lineup-load-bearing, so not gettable at his board price (`trades`) |
| `fa`    | unsigned (no NBA team), so `Δw` runs on the sim's synthetic schedule (`sim.py players`) |
| `nopool`| no pool history at all — `GPp` falls back to the row's own actual line, or to the projection for a true rookie (`sim.py players`) |

`frag`, `miss` and `nopool` are evidence the **`GP`** behind `Δw` is thin; `noproj` is
evidence the **rate** is. Not merely caveats (§Δw).

**An eval file states only what is unique to it** — dated inputs (board stamps, depths,
`REPL`, `SIT`), the tables, and the team-specific read (`GET` calls, shape, what to buy,
picks). It never restates a definition, formula or methodology from this file; it cites
the section instead.
