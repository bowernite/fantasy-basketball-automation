# Eval Definitions

Single source of truth for every shared definition, formula and threshold used to value a player, a team or a pick. **Nothing here is dated or team-specific** — no board stamps, no measured `REPL` figures, no roster numbers. Those are measurements and belong in the dated output that produced them (`evals/teams/*/*.md`, `evals/lineup-math/`).

**Cite this file by section (`Eval Definitions §X`) instead of restating any of it.** The test before writing a sentence anywhere else: if it would be true and word-for-word identical for every player, every team and every trade, it's a definition — cut it and cite the section.

What an eval **publishes** is `Eval Template.md`. When and how to apply this: `eval-team` · picks `eval-pick` · negotiation `trades` · our own roster `evals/teams/my-team/My Team.md`.

# The three layers

Every eval publishes three things, side by side, never folded into one number:

| Layer | What it answers | Where it comes from |
|---|---|---|
| **BASE** | Market price, dynasty-wide — what he costs | External boards (§BASE) |
| **`Δw`** | Wins added to a specific roster, this season | The sim (§Δw) |
| **`SIT`** | How much a win is worth to that team right now | Judgment: contending / fringe / tanking (§SIT) |

**BASE owns everything multi-year** — trajectory, age, upside, risk: the boards price all of it into the rank, and nothing in this repo re-derives or stacks on top of that (`CLAUDE.md` §Objective). **`Δw` owns our format** — scoring weights, the 9 daily slots, the real NBA calendar, this roster's shape. The gap between them is the signal; `SIT` says which one the current season should listen to.

**There is deliberately no exchange rate between BASE and `Δw`** — no constant converts wins into BASE units, and none may be derived or remembered. A deal that needs one to look good is a tie (§VERDICT).

# At a glance

Plain-English gloss of every column and metric. Full definition and edge cases are in the section of the same name below — read those before using any of these.

- **`Boards`** — the per-board dynasty ranks behind BASE, one cell, blend order (§BASE).
- **BASE** — blended dynasty board rank, converted to a value. Pure market price; no adjustment for injury, role, contract or age.
- **`FPts/G proj (last)`** — one cell, two figures: **`FPts/Gp`**, projected per-game stats scored under our rules and the rate `Δw` runs on, then in parens **`FPts/G`**, last season actual under the same scoring — reporting only.
- **`GP proj (last)`** — one cell, two figures: **`GPp`**, the projected `GP` behind `Δw`, then in parens **`GP`**, games played last season — reporting only: never quote it as next season's availability, and never hand-feed it anywhere.
- **`Δw ours` / `Δw theirs`** — sim-measured wins added on that roster, this season.
- **`AGE`** — age in years, from date of birth.
- **`POS`** — position-eligibility slot group: center, guard, or forward.
- **`W20`–`W23`** — expected fantasy points in each bracket period, GP-adjusted.
- **`ΔP(title)`** — sim-measured change in title probability from a player being on the roster, by seed band. A different currency from `Δw`, never combined with it.
- **`SIT`** — a team's situation: contending / fringe / tanking.
- **`COST (perceived)`** — how gettable a player is from his current owner. Judgment, not a value.
- **`σ`** — confidence that the sim's ordering of two adjacent rows is real, not noise.
- **VERDICT** — the accept/reject judgment for a concrete deal: `ΔBASE` and `Δw` read against `SIT`.

# BASE

Blended points-format dynasty board rank and nothing else. **No adjustment by us for injury, durability, role, team situation, contract or aging** — the rank prices all six. **This binds BASE only**: the rate and `GP` feeding `Δw` are projections (§Δw). BASE is the market price, not the truth; divergence is the edge. Picks: `eval-pick`.

| Board          | Weight | Skill                |
| -------------- | ------ | -------------------- |
| Dizzle Points  | 40%    | `dizzle-dynasty`     |
| Hashtag Points | 35%    | `hashtag-basketball` |
| Hashtag crowd  | 25%    | `hashtag-basketball` |

Dynatyze (`dynatyze`) is too shallow to blend — reference only. Before adding a source, count analysts, not boards (`eval-player` §*Caveats*).

**`V()` each board's rank, then weight-average the values** — never average ranks first.

```
D    = teams × roster_size          # rostered players; past D a player is free
a    = √D                           # rank a is worth half of rank 1
V(r) = 9999 × (a+1)/(D−1) × (D−r)/(a+r)     for r < D, else 0
```

`roster_size` = **the size in effect for the season being valued** (`league-info`); flag it whenever current and announced differ. **BASE is comparable only within one `D`** — re-run every eval when the league resizes.

**Never divide by BASE** — no BASE-normalised ratio, anywhere; compare in absolute terms.

## Depth and absence

Fetch every blended board as deep as it goes, record that depth (a dated fact — belongs in the eval), then per board per player:

| | |
| ---------------------------------------------------- | ---------------------------------------------------------------- |
| rank < `D`                                           | `V(rank)`                                                        |
| rank ≥ `D`, or absent from a board that reaches `D`  | **0** — absence is a statement of value                          |
| absent from a board that stops short of `D`          | renormalise that board's weight away, **for that player only**   |

Renormalise only where absence and below-depth are indistinguishable.

⚠️ **A board that puts a player past `D` while another ranks him inside 200 is a disagreement, not a price.** The blend still averages it, but hides the dispersion: a board ranking a player past `D` is saying *he is not rosterable*. **Flag any row whose per-board ranks straddle `D`** (`Eval Template.md`, `board split`). A row that is both split that way and a wide low-BASE/high-`Δw` gap signals the boards pricing a role or career risk no column here carries — never publish it as a buy without naming the split.

# Columns

Alongside BASE, never folded in. Sources: `get-league-info`.

| Col       | Source                                |                                                                                                                                                             |
| --------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Boards`  | §BASE's three boards                  | each board's rank for that player, blend order, one cell — so outliers stay traceable                                                                       |
| `FPts/G proj (last)` | `projections` · `FetchRoster?season=` `seasonAverage` | `FPts/Gp` then `FPts/G` in parens, one cell, so the divergence is visible. The projection is **the rate `Δw` runs on**; the actual is reporting only |
| `GP proj (last)` | `sim.project_gp` · `seasonTotal / seasonAverage` | `GPp` then `GP` in parens, one cell. The projection is what `Δw` runs on; the actual is reporting only                                       |
| `Δw ours` | `sim.py players` · `sim.incoming_wins` | sim-measured. Already ours → `players`. Not yet ours → `incoming_wins` against `basis()`, never a hand-edited roster file (§Δw)                              |
| `AGE`     | `FetchPlayerProfile` `detail.dob`     | ms epoch, parse **UTC**. Never `detail.age`. **As of the eval's derivation date** — one convention, everywhere                                              |
| `POS`    | `proPlayer.positionEligibility`       | multi-position is underpriced. Slot group, as `sim.py` maps it: `{C}` → center · ⊆ `{PG,SG}` → guard · anything else → **forward** (so a PF/C is a forward) |
| `W20`–`W23` | `sim.py weeks`                      | expected points in bracket period *n* = `FPts/Gp` × that player's NBA games inside the period × `GPp` ÷ his NBA team's games (§ΔP(title)). `–` with no projection or no NBA team |
| `COST (perceived)` | §COST (perceived)            | judgment. **Counterparty tables only** — meaningless on our own roster                                                                                       |

**`σ` is never a table column** (§σ) — a footnote, not a row-by-row read.

**A player with no last-season sample has no `FPts/G`** — print `–` inside the parens. He still has an `FPts/Gp`. **Never print a projection in the actuals position**, and never the reverse.

BASE and `FPts/Gp` will disagree; that's the signal. A wide `FPts/G` → `FPts/Gp` gap is a second one — the projection pricing a role change the last season cannot show.

**No format-fit column, and never a format-adjusted BASE.** Our scoring weights (`league-info`) are already inside `FPts/G` and `FPts/Gp`; the structural half — eligibility, 9 daily slots, NBA schedule — is already inside any sim `Δw`, which runs the real calendar. A third column double-counts one or the other. Use the weights to _explain_ a BASE↔`FPts/G` gap, never as a separate score. Reason about the profile directly only with no usable sample (rookie, tiny `GP`, role change).

**Never diff a board rank against an our-format ranking.** The boards are dynasty and any our-format ranking is one season, so the residual measures age, not format.

## Sourced vs modelled

The classification every eval must flag:

| Sourced (a market/API fact) | Modelled (we derived it) | Judgment (not a value) |
| --- | --- | --- |
| Per-board ranks, BASE's inputs | `FPts/Gp` (a sourced stat line, scored by us) | `COST (perceived)` (§COST (perceived)) |
| `FPts/G`, `GP` (last season actual) | `GPp` (`sim.project_gp`) | `SIT` (§SIT) |
| `AGE`, `POS` | `Δw` (theirs and ours) | |
| Body counts, roster limits, wire facts (trade terms, dates) | `REPL` (sim-internal) | |
| | `W20`–`W23`, `ΔP(title)` (§ΔP(title)) | |

**`FPts/Gp` is modelled, not sourced** — the stat line under it is someone else's forecast, and both the scoring and the DD/TD estimate are ours. Cite it as a projection, never as a price.

**A sourced price and a modelled figure never bracket a range** — BASE and `Δw` are a gap to read, not an interval, and neither is a midpoint of the other. File-specific sourced facts (e.g. a particular trade's terms) are additive to this table, not a reason to re-derive it.

# `Δw` — wins added, sim-measured

`sim.py` prices a roster change in **expected wins over the 20 periods Fleaflicker scores as regular**, on the real NBA calendar, with optimal nightly lineups and projected `GP` on both sides. ⚠️ **That is 19 regular-season matchups plus bracket R1**, which the wire cannot label (`league-info` §*Matchup periods*) — one basis, deliberately: the horizon is 20 matchups, the regular season is not. `evals/lineup-math/method.md` and `findings.md` own the method, the measurements, the error bars and what that basis costs — re-run it, never quote a remembered figure.

- **One season, one roster.** Multi-year value is BASE's, entirely. Never sum `Δw` over future seasons, never discount it, and never apply an aging term or age haircut inside a win delta.
- **Compute it for every rostered player on every roster touched — never a shortlist, either side** (`sim.py --roster <team>.json players`). A blank reads as zero regardless of the caveat next to it; `–` must not appear in the column for a rostered player.
- **A player who is not ours yet gets `incoming_wins`, never a hand-edited roster file.** `sim.incoming_wins(sim.basis(), sim.our_roster("their.json"))` seats him in one of `basis()`'s padded slots and prices him against the same replacement body of his own slot group that `player_wins` prices a departure against — one counterfactual and one sign, so both columns read positive for a player worth having. ⚠️ **That is not comparability.** Each is fitted against its own roster's `R` and those run rate points apart between teams, so **`Δw ours` is the only cross-team-comparable column** and the theirs−ours gap is not a number: never rank, sort or shortlist a target on it. **It refuses on a roster with no pad left**: with every slot real, somebody we field has to go, and the candidates sit a rate point apart down where `replacement`'s line no longer ranks them — a coin flip that would still print as measured. Pass the roster you would actually field, and name the body you dropped.
- **Never sum `Δw` across pieces.** It is marginal against the roster as it stands and sub-additive under the 9-slot cap — price a multi-piece side with one joint `sim.run(sim.swap(...))`, never by adding rows. A pick has BASE and no `Δw`: it enters a deal through `ΔBASE` alone (`eval-pick`).
- **Always state the counterfactual.** "If he vanished and the slot went empty" and "if we swapped X for him" differ by the whole value of X.
- **Compare rosters only at a common body count** — pad both to the `roster_size` being valued (`sim.basis()`). A roster measured short has a low replacement level and every player on it reads too valuable.
- **`Δw theirs` prices only what they give up inside a concrete deal.** It predicts neither our gain nor what they will accept (§COST (perceived)) — never target, sort or shortlist off it, and never call a low figure "cheap to buy".
- **The rate behind `Δw` is projected, never posted** — a sourced per-game stat line scored under our rules (`projections`). It already prices a changed role, a returning injury and a rookie's step forward, so **never adjust it by hand for any of those**. A player the feed does not carry keeps last season's average and must publish `no projection`.
- **One source is a house view, not a market.** Where a projection and last season's `FPts/G` diverge widely, say which one the read leans on.
- **`Δw` still under-rates ascending youth** — one season, and a projection is a next-season forecast rather than a career curve. Never read a low `Δw` on a young player as a sell signal.
- **A high-`Δw`/low-BASE row is either a format/roster edge or a rate the boards doubt.** Check the flags and the per-board ranks before calling it a buy — **a gap you cannot explain is a finding about our inputs, not about the market.**
- **Team-specific, never a price.** What to pay comes from `COST (perceived)` and the negotiation.

**Untouchable is not an excuse to skip `Δw`** — compute it for names with no realistic path too.

# `ΔP(title)` — bracket-week value

Periods 20–23 are the bracket rounds; which of them bind depends on seed (`league-info` §*Matchup periods*). The column names spell this season's window out because a table header has to — **the round count and the window themselves come off a `sim.py weeks` or `playoffs` run, which derives and asserts both, never off this page or off a remembered shape.**

**Two reports, and most evals need only the cheap one.** `sim.py weeks` prints `W20`–`W23` and nothing else — closed-form arithmetic, no Monte Carlo, any roster. `sim.py playoffs` adds `ΔP(title)` and costs ~350 simulated seasons. **Run `playoffs` for our roster; run `weeks` for a counterparty** (§*Counterparty title reads*).

**`W20`–`W23`** (§Columns) are the per-player inputs: `FPts/Gp` × the NBA games that player's team plays inside the period × the share of the season `GPp` projects him available for. That share is the same one the sim draws behind `ΔP(title)`, so the two agree on what a body is available for. They are **expectations, not what he scores if he plays** — a fragile star and an ironman on one rate are different numbers here. They are points, never wins: never fed into `Δw`'s units, read against the 0.1-win floor, or compared to a season rate.

⚠️ **`W20`–`W23` and `ΔP(title)` both carry availability, so never add them.** Each is a complete read of the bracket window in its own currency; summing them counts the same GP haircut twice on top of mixing currencies (§*`ΔP(title)` and `Δw` are different currencies*).

**`ΔP(title)`** is the change in probability of winning the title from a player being on the roster, measured by `sim.py playoffs` against a replacement body of his own slot group — the same counterfactual `Δw` uses — **in percentage points**, as the report prints it. Report **the band matching the roster's projected PF rank**; name a second band only where a call turns on the seed. Re-run it, never quote a remembered figure; `evals/lineup-math/tldr.md` §*Bracket weeks* owns the measured multiplier and `method.md` §*The 0.1-win floor* its error bars.

⚠️ **`P(title)` and `ΔP(title)` are different numbers.** `P(title)` is the whole roster's odds of winning; `ΔP(title)` is one player's contribution to them. A block headed with one and filled with the other is the commonest error on these files — name which you are printing.

⚠️ **`ΔP(title)` and `Δw` are different currencies and are never combined.** `Δw` is in wins over §Δw's 20-period basis; `ΔP(title)` in percentage points of title probability. **Never sum, net, average or exchange them**, and never read one against the other's thresholds. No conversion constant exists or may be derived.

⚠️ **The two bases overlap at period 20.** §Δw's 20 periods include bracket R1, so `W20`'s points and the 5–8 band's first round are **already inside every `Δw` on the page** — adding a bracket read to a win read counts that week twice on top of mixing currencies.

- **What it may do:** decide a bracket-window question — which of two comparable bodies to field, hold or acquire when the rest of the read is level.
- **What it may not do:** reprice BASE, adjust `Δw`, resize a row, or stand in for either decision column in VERDICT.
- **One season, one roster**, as `Δw`. A multi-piece side gets one joint run — `sim.roster_title(after, before)` — never added rows.
- Moot at `SIT` tanking.
- **Not a table column** — a short block below the player table.

## Counterparty title reads

**A counterparty eval does not get a `ΔP(title)` block.** It answers one question — are they contending, and do they think they are — and two cheaper sources already do:

- **Projected season PF and rank** ("5th of 12, 27,155"), off their roster file on our basis. One number, and it is the league's own seeding rule.
- **`SIT`** (§SIT) for whether they *behave* like a contender. No sim answers that at any price.

Their `P(title)`, seed bands, `μ_us`, field mean and survivor opponent decide nothing we do — we do not price on their sim, and they do not price on ours. **Where the two disagree — `SIT` contending against a bottom-band PF rank — say so in one line and move on.** The mechanism behind a bracket number belongs in `evals/lineup-math/findings.md`, never in a team file.

# σ

`sim.py players` prints σ as the gap to a neighbouring row, in sigmas of the sim's own Monte-Carlo noise (3 independent 200-trial seed blocks). It measures whether the sim resolves the *order* of two adjacent rows — nothing about tradeability.

- **State no order below ~2σ** — treat the rows as an unordered tie, and say which ordering σ belongs to (it can differ from the published sort).
- **Never a printed table column.** One footnote below the table naming the adjacent-pair ties (`Name/Name X.Xσ`). Above ~2σ the magnitude carries no further meaning.
- **Monte-Carlo resolution is not decision resolution.** A gap can clear 2σ and still be under ~0.1 wins — a real order, and too small to trade on.
- A decision that leans on one pair's ordering computes σ for that pair on demand.

# `SIT` — contending / fringe / tanking

One label per team — ours and any counterparty's — dated. Assign from standings (`FetchLeagueStandings`) plus `evals/Team Projections.md`; ours is `evals/teams/my-team/My Team.md`'s to own. The projections carry ±2–3 ranks of noise, so the label is **coarse on purpose**: where a team sits on a boundary, say so and carry both readings rather than forcing one.

What the label changes — what that team should pay up for and sell down:

| `SIT` | Up | Down |
| -------------- | ---------------------- | ---------------------- |
| **Contending** | `Δw`, `FPts/G`, `GP` | `AGE`                  |
| **Fringe**     | `Δw` + BASE evenly   | —                      |
| **Tanking**    | BASE, youth, ceiling   | `Δw`, `FPts/G`, `GP` |

Prospects: weight the tail — `P(top-30 asset)`. Ceiling >> floor; a safe starter is near-worthless to a tanker.

Fringe-now-contending-later changes what a team buys today — that read is `Team Projections.md`'s, quoted with its date.

# `COST (perceived)` — what they'll take

**What a player's owner will accept for him, never what he's worth.** It sets the units to negotiate in and is the only predictor of gettability we have. **Counterparty tables only** — meaningless on our own roster.

Assume an owner prices on **recent `FPts/G` (2–3 seasons, recency-weighted) + `AGE` + their own `SIT`**; some also weigh BASE. Their `SIT` flips the sign on age — a rebuilder sells old-and-productive cheap and refuses youth at any price, a contender the reverse.

**Judgment, not a computed column** — coarse `high` / `mid` / `low` per name, off columns already sourced. Never publish it as a value, never sum it, never put it in VERDICT (it may only break a tie the rule already declares). **Slot-group counts are not a `COST (perceived)` input** (§*Non-factors*).

- **`COST (perceived)` low + high worth-to-us** (`Δw` read against BASE) is the target list.
- **`COST (perceived)` high + high worth-to-us** means pay up or walk — not a mispricing.
- **Board-cheap but lineup-load-bearing** (`load-bearing`, `Eval Template.md`) is not gettable at his board price — name the tension before anchoring low.
- **A gap you cannot explain is a finding about our inputs, not about the market** — check the board straddle (§BASE) and the row's flags (§Δw) first.

⚠️ **Every `COST (perceived)` read predates talking to them.** It is a guess about an owner, not a fact about him, and the same applies to any "what they want" line in a team eval.

# VERDICT

Objective: **maximise `Σ P(title)` over the seasons we intend to contend** (`CLAUDE.md` §Objective).

For a concrete deal, publish both deltas and judge them against our `SIT` — never fold them into one number:

- **`ΔBASE`** — both sides on the same curve, picks included (`eval-pick`).
- **`Δw`** — one joint sim run per side of the actual pieces (§Δw): ours on our roster, theirs on theirs.

The rule, by our `SIT`:

- **Contending: buy wins.** Accept a modestly negative `ΔBASE` for a clearly positive `Δw`. BASE already contains the market's price on this season, so this is a deliberate premium on current production — capped at **modestly** negative, never at "whatever the wins justify". **Never ship large BASE for small wins.**
- **Fringe:** both deltas ≥ ~0, or pass. Wins that don't move title odds aren't worth BASE.
- **Tanking:** `ΔBASE` decides; `Δw` is ~irrelevant.

**If the verdict flips on how you weigh the two columns, it's a tie.** Report it as a tie and decide on negotiation grounds — `COST (perceived)`, deal shape, flags — or improve the deal. Never invent a conversion rate to force a sign.

## Ranking two offers

Score each against the status quo — `ΔBASE` and joint-sim `Δw` per offer — and compare column by column. An offer that wins both columns wins. Split columns → the `SIT` rule above; still split → a tie, reported as one, never broken on narrative.

# Durability

Our format prices a missed game the same way the boards do: **no format-derived injury adjustment**, never stacked on BASE, and **no fragility discount** — lineup lock-in doesn't change that. **Never accept less production to buy durability or lower variance**, and no third penalty on a fragile star bought with bodies.

Spend the effort on **expected `GP`**, regressed hard and **identically on both sides of every deal**:

- **Never hand-type `GP`, and never use current injury _status_** — a this-season fact in a dynasty league. Take it from `sim.py gp`, `--roster their.json` for a counterparty.
- **Last season's `GP` and rate only — no multi-season average, no age.** Neither beats one season. **`GP` is a defensible input, not a precise one** — never argue a trade on a few games.
- **`GP` is projected off last season's _actual_ rate, never the projected one** — that is the input the fit was built on, and a projected rate through it recalibrates every `GPp` in the study against a variable it never saw (`projections`).
- **Never take a published `GP` projection at face value.** Measured against what happened, external feeds run optimistic and compress the spread, and lose to `sim.project_gp` on the players we trade despite ordering players better than it does (`evals/lineup-math/tldr.md` §*GP is the dominant input* owns the figures).
- **Flag, don't patch, two blind spots:** a fragment last season (**25 games or fewer** — the band has **no lower bound**, since a 5-game season is *present* in the pool rather than absent and is the thinnest evidence of all); and a whole missed season, absent from the fit rather than a zero — the projection is expected GP _given he plays_, blind to whole-year risk. **Both cap what a `Δw` built on them can claim**, and the flag travels with the row.
- **A rotation season is a pool season at rate ≥ 15** — below that, `GP` measures _role_, not health. Fewer than 3 rotation seasons is thin evidence the role itself holds up (`Nyr role` flag, `Eval Template.md`). The same call applies inside a qualifying season: a player's first one or two seasons, an under-60 year spent earning a rotation spot (bench-to-starter climb, DNP-CDs before he won minutes) measures role, not health — name the cause (injury vs. earning-time) for every under-60 season cited.

The `GP` projection formula and its cross-validation are measured, not defined — `evals/lineup-math/tldr.md` §*GP is the dominant input* owns the coefficients; this file owns only the rule for how to use them.

# Where our format pulls off consensus

**Deviate from the boards only where our scoring weights, the 9-slot cap or a roster's shape make the answer differ from the market's — and only where the effect survives the stated error bars (`evals/lineup-math/findings.md`).** Everything else is in BASE: no column, no discount, no model. Anything that can't name a direction and a magnitude is noise. **The closed list:**

1. **`Δw`** — the 9-slot effect, computed rather than asserted. Value is bimodal: the middle tier is both what to trade _from_ and what to buy cheaply. Sub-replacement bodies still pay as bodies; never price them at 0.
2. **Body count is a price, and a steep one — so default to many small swaps.** At **equal BASE paid out**, N-for-1 at N≥3 is value-neutral to negative against the same BASE spent on separate 1-for-1s. Cap consolidation at 3-for-1, dregs only. **Compare the two shapes by joint sim at matched BASE** — never off rank alone, and never equate a board rank with an `FPts/G` figure. The price is **structural**, so **never present it as a backfill effect.** Backfill flips no sign; price a body by backfill availability at the moment it must be **fielded**, not when the trade is made. **Read the actual multiple off `evals/lineup-math/tldr.md` §*Consolidation is not the lever*, never off a remembered number.**
3. **Multi-position eligibility**, and forwards over equal-rate guards/centers. **Already inside any sim `Δw` — never apply it on top of one.** A tiebreak only where no sim run exists (no usable sample), against _that_ roster's tightest slot group — recheck every time, never carry a count or a premium forward. **Read the size off `evals/lineup-math/tldr.md` §*Positional premium*, never off a remembered number** — it is a fact about our roster's current shape, so it re-cuts whenever that changes.
4. **Light-night coverage — a property of the roster's coverage of the NBA calendar, not of a player.** So it is never a column, never in BASE, never a per-player premium, and **already inside any sim `Δw` for a player with a real NBA team — never apply it on top of one.** An **acquisition-time tiebreak only**, where the sim has no real team to run on (an auction candidate, a `free agent` row, a `sim.star()` body): rank on `(rate − R) × GP` first, then among bodies close enough in projected rate at comparable `GP` prefer the NBA team covering **nights we don't already cover**. What pays is the count of distinct light nights the roster reaches, never a body's own night count, and **it saturates**. **Spent on the downside, not the upside**: a whole auction steered right is worth about the ~0.1-win floor — a real order still too small to trade on (§σ) — while stacking the seven on one schedule costs several times that. **A free ordering rule and nothing more** — never pay a pick, a body or a rate gap wider than the measured band for a schedule. The **rate-point threshold is a function of the body's grade**, roughly halving from auction grade to a real producer, so read the row that matches the body. It, the saturation point and what a steered auction is worth are measured in `evals/lineup-math/tldr.md` §*Light-night coverage* — read them there, never off a remembered number, and treat them as re-cut every season.

# Non-factors — canonical list, do not spend effort

Real-life contracts · NBA depth charts · same-NBA-team stacking · fragility concentration · absence _pattern_ for season points · variance from a normal-sized trade · **slot-group balance as a standing target**. Never reach for a variance argument to justify a move that doesn't pay in points. Same-NBA-team stacking is a non-factor **in its own right**; it enters only as light-night coverage (§*Where our format pulls off consensus* 4). **Don't restate this list elsewhere — cite this section.**

**Never name a roster's slot-group shape as a weakness, a buy criterion, a preferred return or a walk-away** — `Δw` prices it already, and a shape count expires as the roster turns over. §*Where our format pulls off consensus* 3 is its only sanctioned use.
