---
description: Use when valuing a player or a whole roster
---

This file owns the **procedure** and the **sources**. The blend, the curve, the columns, where our format pulls off consensus, and the output format: `strategy/Definitions/Eval Definitions.md`. Whole-team eval files: `eval-team`. Our situation: `strategy/teams/my-team/Ours.team.md`.

# Procedure

1. **Check `strategy/` first.** Read the date stamp; re-derive anything stale rather than quoting it.
2. **League truth** (`get-league-info`): `FetchRoster?team_id=&season=` for a whole roster, `FetchPlayerProfile` for one player (owner, `detail.dob`, **never `detail.age`**, `Eval Definitions §Columns`). Derive `GP` and check it before trusting any average.
3. **Pull boards in this order**, recording each one's update stamp and depth: Dizzle Points → Hashtag expert Points → Hashtag crowd (`/keeper`) → Dynatyze (reference only).
4. **Join league names to board rows** per §*Joining names to board rows*, before recording any rank or any absence.
5. **Blend into BASE: run the recipe and copy stdout**, never retype it. It carries `Eval Definitions §BASE`'s weights, curve, depth rule and renormalisation rule, and prints per-board ranks beside BASE, off the `strategy/` snapshots (re-cut those first if stale).

   ```bash
   # from the repo root -- `--roster` resolves against cwd
   python3 .claude/skills/eval-player/base.py --roster strategy/lineup-math/rosters/roster-161025-2025-26.json
   python3 .claude/skills/eval-player/base.py "Kyrie Irving" "Jaylin Williams:OKC"
   python3 .claude/skills/eval-player/test_base.py    # offline guard, no network
   ```

   A `REFUSED` line means fix the join or the flag, **not the recipe**.
6. **Refresh the projections** (`projections`): rate plus both GP snapshots (`hashtag_gp.py refresh`, `fanscout_gp.py refresh`). Both win columns run on them, and they go stale.
7. **Add the columns** (`Eval Definitions §Columns`, `eval-team/Eval Template.md`):
   - **Formula `Δw`**: `sim.formula_player_wins`.
   - **`Δw (season)` / `ΔP(title)`**, on our roster: `sim.py players` / `player_title` (or `title-column` `include: ["ours"]`). Not ours yet: `--eval <team_id>` / `incoming_wins(basis(), our_roster("their.json"))`, and `incoming_title` the same way. Leave `ROSTER` alone for incoming (never assign it their file).
   - **`W20`–`W23`**: `sim.py weeks`, closed form, any roster.
   - `sim.py title` is roster `P(title)`, not the table column.
8. **Read BASE against `FPts/Gp` in absolute terms.** Output per `eval-team/Eval Template.md`.

Done when every player has BASE, both win columns, `ΔP(title)`, `W20`–`W23` and flags, with each board's stamp and depth recorded.

# Joining names to board rows

`Eval Definitions §BASE` reads absence from a board that reaches `D` as a value of 0. **A failed join is indistinguishable from that and silently prices a real player at ~0**: the most common error. So:

- **Normalise both sides before matching:** strip generational suffixes (`Jr`/`Sr`/`II`/`III`/`IV`), fold accents to ASCII, strip a leading `R.SS / ` slot prefix, case-fold, drop punctuation and spacing. Common shapes: a suffix on every board but not in Fleaflicker, an accent in Fleaflicker but on no board. Boards differ from each other and from their own other tabs the same way.
- **Names are not unique keys: join on `(player, team)`.** The boards carry two different active players named `Jaylin Williams`. NBA team abbreviations differ across boards (`SAS`/`SA`, `PHX`/`PHO`, `GSW`/`GS`), and a board may show a player mid-move (`DAL -> DEN`): normalise the abbreviation and count both ends of a move, then match it exactly, and only to disambiguate a duplicate name. Loose team matching is how `SAC` reads as the Spurs and `PHX` as the 76ers.
- **One name on the same team twice on one board is one player listed twice**: take his best rank. The same name on different teams stays two players; a shared `FA` or blank team cell counts as no team.
- `hashtag_id` is a stable key but exists on the crowd board only; there is no shared id across boards.
- **Hand-check every all-boards absence before recording 0.** A player missing from *all* boards is far more often a join failure than a genuine 0: search the surname on each board first, and record 0 only once you've looked. Same for a row with no blended rank (`- -`) but a crowd rank: `base.py` prices it 0 without refusing.

`base.py` enforces the normalising, the team match and the duplicate rule. It **refuses** an all-boards absence until `--absent NAME` records the hand-check, and refuses a colliding name until `NAME:TEAM` splits it. A nickname no normalisation can reach (`Bub` / `Carlton Carrington`) goes in its `ALIAS` table, one hand-checked line per name. A rookie with no Dizzle dynasty row takes his Dizzle rank off the rookie tab + pick chart (`BASE.md` §Depth and absence); `base.py`'s `CHART` header line names every such row.

# Rules

`Eval Definitions §Non-factors` is settled; apply it as written, with no carve-outs:

- **Role is priced already.** A demotion, usage removed by a trade, or a new coach's stated plan is inside the projected rate (`projections`): **use the rate as projected, never hand-adjust it**. "NBA depth charts" stays a non-factor for a *young* player behind a temporary blocker.

Position enters **once**, via `POS` into the sim's `Δw (season)`. `Eval Definitions §Where our format pulls off consensus` 3 is its only other use, as a formula-`Δw` tiebreak. Recheck which slot group is tightest on the roster in question; never carry a count or a premium across rosters or forward in time (`Eval Definitions §Non-factors`).

**Who holds value and who fades, years 2–7:** `strategy/lineup-math/run sim.py progression` (one player: its module docstring). A review read beside BASE, never an input to BASE or either win column; its limits print with it.

# Sources

Boards are forward-looking and **not adjusted for our scoring**; `FPts/Gp` is both, but one season only (`projections`). Where they disagree the board is pricing the years after this one.

_List generated 2026-07: re-check staleness before relying on it._

| Skill | Use |
|---|---|
| `dizzle-dynasty` | Best fit: separate **Points** dynasty + rookie tabs, deepest, plus the only pick chart. Start here. Its chart value column is **shared across formats**; only "who I'd take" is per format |
| `hashtag-basketball` | Expert board has a Points view; `/keeper` is the crowd board, daily, and prices picks in bands |
| `dynatyze` | Elites only (shallow free tier), no points view. Unique asset: it prices **future 1sts** |

**Skip:** FantasyPros dynasty ECR (one expert, usually stale; check `"last_updated"`) · KeepTradeCut (no NBA product) · RotoWire (grouped by theme) · RotoBaller/NBC/Yahoo/FantasySP (rookies only).

## Caveats

- **Count independent analysts, not boards.** Dizzle's tabs are one person; Hashtag's expert views are one person; **Dizzle's author also sits on Dynatyze's panel**, so those two double-count. Crowd is printed on `Boards`, not blended.
- **No true consensus source exists.** Spreads between boards are part of the deliverable; divergence is two people disagreeing, not a market read.
- Watch for "draft class still normalizing" notices, visible whenever a pick prices above the player you'd take with it.
- Hashtag and Dynatyze 403 `WebFetch`; `curl -L` with a browser UA works.
