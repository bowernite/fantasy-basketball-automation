Entry point for any trade question. This file owns the **procedure** and **pricing their side**; `negotiation.md` (this directory) owns running the negotiation. Every format-derived formula and threshold lives in `evals/Definitions/Eval Definitions.md` — cite it, don't re-derive.

# Procedure

1. **Frame it.** Which question: _evaluate an offer_ · _originate a buy_ · _shop one of ours_ · _scout a partner_. Name our `SIT` (`evals/teams/my-team/My Team.md`) and theirs (`Eval Definitions §SIT`), each dated.
2. **Fetch** (`get-league-info`, **one subagent for all of this work**) — **only what a current eval doesn't already carry**; 2.1 always:
   1. **`FetchTrades` — always, first.** A pending trade makes the draft board and every roster stale until it executes. Also the only source of pick ownership beyond the two drafts the board serves (`filter=TRADES_COMPLETED`), of the veto window, and of this league's actual deal shapes. Ask the user if they want to do this at the start.
   2. `FetchLeagueRosters` for **body counts** both sides (step 3), then `FetchRoster?team_id=&season=` per team — the only source of rates and `GP`.
   3. `FetchLeagueStandings?season=` for `SIT`. (only necessary if team eval file doesn't already have these, which it should)
   4. `FetchLeagueDraftBoard` if picks are in play. (only necessary if team eval file doesn't already have these, which it should)
   5. `FetchLeagueTransactions` — what this owner has been doing. Not a wire-live check. Ask the user at the start if we want to do this or not.
4. Evaluate it, per team eval files
5. **Value both sides** — `eval-player`, `eval-pick` — onto the same curve. Publish BASE and columns separately.
6. **Score our side.** **Simulate the actual pieces** (`Eval Definitions §Δw`) before recommending anything. Start with `evals/lineup-math/run sim.py --help` — it names every report, which of them a counterparty's roster can be run through, and how long the slow ones take; run what that says answers the question, and read the numbers off the run rather than from here. The `import sim` path in `evals/lineup-math/README.md` is for hypothetical shapes on **ours**. State the counterfactual.
7. **Price the bodies** for the delta in body-count: break-even rate · backfill regime · our roster-depth floor.
8. **Score both deltas against our `SIT`** (`Eval Definitions §SIT`): publish `ΔBASE` and `Δw (season)` side by side; a tie reported as a tie. **`ΔP(title)` is not a third delta** — it may only break a tie when `Δw (season)` alone is ambiguous (`Bracket value.md`).
9. **Output:** the deal · our verdict with its counterfactual · their side as they'd see it · opening offer · walk-away · what a good counter looks like · sourced vs modelled. Publish `ΔP(title)` as its own line where step 6 ran it, under our applicable band.

Simulation: judgment call whether it's needle-moving on a given deal. Especially since most of the time we're invoking this, we already generated the team's eval file, which ran a sim for each player individually. What you _could_ do is run sims for actual swaps to make it more concrete. When you do think it's valuable, start with `evals/lineup-math/run sim.py --help` — the command's own surface is the spec for what it can be asked, and every table it prints labels its roster, its columns and its units. Nothing here restates them. I would say we probably don't want to run any sims when first feeling out a team, gathering info, brainstorming packages, etc. But maybe as we get closer to trade shape(s).

If contending, price the bracket weeks too — one joint run per side, `ΔP(title)` under our applicable band (`Eval Definitions §ΔP(title)`), which is a different currency from `Δw` and never nets against it.

**Branches.** _Evaluating an offer:_ also ask why they offered it — the answer names the asset they actually want. _Originating a buy:_ derive the target from our weakest slot, not the best available player. _Shopping one of ours:_ start from `evals/teams/my-team/My Team.md`'s **_Prime sell_** cell — recut on the current table, never off a name list in `evals/` — then find the counterparty whose `SIT` and roster shape fit the asset; never list him publicly without deciding what that leaks. _Scouting:_ stop after step 6.

# Deal shape

Body price, consolidation cap, the many-small-swaps arbitrage and the backfill regime are `Eval Definitions §Where our format pulls off consensus`'s. Three additions:

- **Buy the bottom of the roster first.** Upgrading sub-replacement bodies to durable mid-tier vets out-produces a top-end 1-for-1 at a fraction of the dynasty cost. **Read the multiple off `evals/lineup-math/findings.md` §_Consolidation is not the lever_**, never from here. Check for a pending roster expansion (`league-info`): while one is coming it supplies part of the same gain for nothing, and breadth stops differentiating once every team fills from the same pool. So buy the bottom **for this season's slot-nights**, not as a lasting edge.
- **Read the ceiling on a single move off `evals/lineup-math/findings.md` §_PF → wins_**, and the ladder off §_Consolidation_ — never a remembered figure. Distrust any pitch framed as transformational, including our own.
- **Never add NBA schedule on top of a `Δw`.** Already inside it for a player with a real NBA team; it applies only where the team is synthetic or unknown (`Eval Definitions §Where our format pulls off consensus` 5).

# Pricing their side

It is **not** a standing age edge — no aging term exists anywhere (`Eval Definitions §Δw`), and old-and-productive being board-cheap is a tiebreak, never a deal's thesis. Play the age gap **only on a short horizon, in either direction**:

- **Buy:** old + high current rate + durable — on a ≤2-season window.
- **Sell:** young + modest current rate; anything whose value is name or pedigree.
- **Don't shop _Core_** — the grid cell in `evals/teams/my-team/My Team.md`, recut per that file, and the only definition of it.

Assume competence, varying by owner. Two opposite risks follow from being the informed side: being badly wrong early on a hard evaluation, and negotiating at our own fair value. Sound them out before committing to a number.

1. **Assign their `SIT`, dated** (`Eval Definitions §SIT`). Fringe-now-contending-later changes what they buy today.
2. **Read their shape:** the hole in their BASE distribution · age profile · body count against the cap. **Slot-group counts are not a standing target** (`Eval Definitions §Non-factors`).
3. **Derive what they refuse, before what they'd want.** It also names the _right_ counterparty for that asset.
*
5. **Flag board-cheap but lineup-load-bearing** (`load-bearing`). Not gettable at his board price — name the tension before anchoring low.
6. **Hunt the asset their own source just soured on.**
7. **Name their untouchables**, symmetrically with ours, cause named. Still compute `Δw` for them (`Eval Definitions §Δw`).

# Notes

- `evals/` holds rosters, per-team valuations and the projections picks depend on. `team-info` maps owner username → real name.
- If getting back more players than giving up, will likely have to cut the difference, which should be factored in (maybe we change the deal to throw that player in, and get a small sweetener from the other team? but this shouldn't be thought about until we're very close to a deal)
- When reading a team-eval, it might state things about what they want or don't want. These are just guesses, before we have even spoken to them. Do not take them to be true necessarily.
