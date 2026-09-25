# `ΔP(title)` — title probability

Expands `Eval Definitions §ΔP(title)` and §*Counterparty title reads*.

**`ΔP(title)`** is the change in probability of winning the title from a player being on the roster — 19 regular periods, standings (record then points-for), then the bracket with its byes (`league-info` §*Matchup periods*). Seed is simulated, not held. Same replacement-body counterfactual as **`Δw (season)`**. Re-run it, never quote a remembered figure. **Eval files:** `100 ×` the sim figure, **one decimal, `%` suffix** (e.g. **9.8%**); the sim report keeps two decimals without `%`.

**Two ΔP reads, like `Δw (season)`** (`Eval Definitions §Columns`):

- **Ours, on roster** — `sim.player_title(basis(), names)` · roster `P(title)` from `sim.py title`
- **Ours, not yet on roster** — `incoming_title(basis(), our_roster("their.json"))` / `--eval <team_id>` — **`ΔP(title) ours`** on counterparty evals; never priced on their roster

**`W20`–`W23`** (`Columns.md`) are expected points in each bracket period: `FPts/Gp` × that player's NBA games inside the period × `GPp` ÷ his NBA team's games. `sim.py weeks` — closed-form, any roster. Points, never wins: never fed into either win column's units, read against the 0.1-win floor, or compared to a season rate. Round count and window come off the period data, never a remembered shape.

⚠️ **`W20`–`W23` and `ΔP(title)` both carry availability, so never add them.** Summing counts the same GP haircut twice on top of mixing currencies.

⚠️ **`P(title)` and `ΔP(title)` are different numbers.** `P(title)` is the whole roster's odds; `ΔP(title)` is one player's contribution. Name which you are printing.

⚠️ **`ΔP(title)` and `Δw (season)` are different currencies, combined only in `Score.md`.** `Δw (season)` is wins over `Delta w (season).md`'s 19-matchup regular-season basis; `ΔP(title)` is percentage points of title probability. Outside `Score.md`, **never sum, net, average or exchange them**, and never read one against the other's thresholds. Formula **`Δw`** is a third currency — same rule.

- **What it may do:** decide a title-odds question — which of two comparable bodies to field, hold or acquire when the rest of the read is level.
- **What it may not do:** reprice BASE, adjust `Δw (season)`, resize a row, or stand in for a trade decision on its own.
- **One season, one roster**, as `Δw (season)`. A multi-piece side on one roster gets one joint run — `sim.roster_title(after, before)` — never added rows. A two-team deal: both rosters in one field (`sim.deal_odds` / `trade-screen`) — that row's `Δw (season)` is the same run's wins.
- Moot at `SIT` tanking.
- **Table column** after `Δw (season)`, before `W20`–`W23` — **`ΔP(title)`** on our roster, **`ΔP(title) ours`** on a counterparty's. **`# Title odds`** names roster `P(title)` only.

`sim.py playoffs` is `P(title|seed)` — diagnostic, not the column. Error bars: `method.md` §*The season end to end*.

# Counterparty title reads

**No `ΔP(title)` priced on their roster** — we do not price on their sim (`Eval Definitions §Counterparty title reads`).

For **our** title odds if we acquire them: **`ΔP(title) ours`** in the counterparty table (`incoming_title` on `basis()`). Projected PF rank + `SIT` for whether they contend.
