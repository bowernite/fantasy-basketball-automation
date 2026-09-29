---
name: trade-shapes
description: Maintain a team's trade shapes — human HTML file plus agent .shapes.md. Tier, sort, Too lopsided, Doesn't meet our minimums, Status. Pair with sims Skill to price rows.
---

# Where

Human file Brett reads: `strategy/teams/<owner>/<Name> Trade Shapes.md`

Agent file: `strategy/teams/<owner>/<Name>.shapes.md` — same directory. Read this one. Never read, grep, or shell-print `* Trade Shapes.md`.

On every archive or refresh, write both. Rebuild deal bodies from `.shapes.md`.

**Always load the `trades` Skill** — deals to look for, minimums, metric preferences, competitor rules, what not to float.

# Sections

Five sections, **top to bottom**: `## Above floor` → `## Floor` → `## Below bar` → `## Too lopsided` → `## Doesn't meet our minimums`.

| Section                   | When                                                                                         |
| ------------------------- | -------------------------------------------------------------------------------------------- |
| Above floor               | Clearly better than floor — we'd actively pursue                                             |
| Floor                     | We'd take it if that's all we could get                                                      |
| Below bar                 | Not worth pursuing, but still meets `trades` §General guidlines minimums                     |
| Too lopsided              | **Our ΔBASE ≥ +1250** — keep for reference; do not float                                     |
| Doesn't meet our minimums | Fails at least one minimum in `trades` §General guidlines — keep for reference; do not float |

**Placement order** (each row lives in exactly one section):

1. Sim → assign tier (above floor / floor / below bar) per `§Tiering`.
2. If **our ΔBASE ≥ +1250** → `## Too lopsided`.
3. Else if **fails any minimum** (`trades` §General guidlines) → `## Doesn't meet our minimums`.
4. Else → keep the tier from step 1.

# Tiering and sort

`Score` (`Eval Definitions §Score`) is the baseline — a starting order, not a verdict. Still read every number individually.

- **Sort** each actionable tier (above floor / floor / below bar) by `Score`, highest first; order ties (~250) by judgment on the individual numbers. Re-sort after every refresh or tier move.
- **Tier** by `Score` against the floor — the best live alternative for the same assets (e.g. a benchmark offer), else what we'd settle for: clearly above → Above floor, near → Floor, clearly below → Below bar. No floor yet → tier by judgment, `Score` as a guide. Override a row's `Score` tier only for something the score misses (roster context, `Δage`, competitor rules).

**Too lopsided** — sort by **ΔBASE** descending (most lopsided first). Same columns and bolding rules.

**Doesn't meet our minimums** — sort by `Score`, lowest first. Same columns and bolding rules; do not bold failed minimums.

# Table format

Columns: `Out | In | Score | ΔBASE | Δw | Δw (season) | ΔP(title) | Δage`. Optional **`Status`** after the numbers when a shape has been floated or answered — **negotiation status only** (not general notes): `Us proposed`, `{owner} proposed`, `Us rejected`, or `{owner} rejected`, plus date (e.g. `Hlina **rejected** 9/2`). Bold the status verb. Latest status only — do not stack history; once rejected or superseded, drop an earlier proposed. Leave blank when unset. No commentary, context, or negotiation color in **Status** — put that in the file intro or counterparty notes.

**Round on archive:** `Score` and `ΔBASE` nearest 100 · win columns nearest tenth · `ΔP(title)` nearest whole with **`%` suffix** (e.g. `+5%`, `-2%`, `0%`) · `Δage` nearest tenth, signed (e.g. `+3.2`, `-1.2`, `0.0`).

**Picks** — win columns are bodies; picks are 0 there. Never convert BASE → `Δw`. No `*` on any cell.

**Out** = our side; **In** = theirs. Each cell is one HTML bullet list — one asset per `<li>`:

```html
<ul style="list-style-type:disc;margin:0;padding-left:1.25em">
  <li>…</li>
</ul>
```

Use that exact `<ul>` wrapper even for a single asset.

**Players** — `**Name**` inside each `<li>`. **Name** = last name or eval nickname, **bold**. No age or projection metadata. Out-side players from our eval; In-side from theirs.

**Picks** — **Out** only, as their own `<li>`. Square brackets, bold: `**['27 1st]**`, `**['27 2.09]**` (slot notation per `eval-pick`). Not parentheses, not `+`-joined to a player.

**Rebuild for sim** — deal `label` = the agent line's `out > in` (`Δage` reads later picks from it); strip list markup and bold; player arrays = bare names only. Picks → JSON pick BASE fields (`sims` [config.md](../sims/config.md)); pick label in JSON is `'27 1st` without brackets.

**Bold** asset names and picks in **Out** / **In**. Bold **Score**, **ΔBASE**, **Δw**, **Δw (season)**, **ΔP(title)** when positive, **Δage** when negative; prefix `+` on positive win numbers. **`ΔP(title)` always carries `%`** — inside bold/strike when those apply (e.g. `**+10%**`, `~~**+6%**~~`, `-2%`, `0%`). In **Status**, bold the status verb (`**proposed**`, `**rejected**`, etc.). Leave non-beneficial numbers plain. When **Status** is a rejection, strike through every other cell (`~~…~~`) including each `<li>` body (`<li>~~**Kessler**~~</li>`); leave **Status** plain (verb still bold).

Do not float executed deals as fake shape rows.

# Agent file

Same sections, prose, and row order as the human file. No HTML, no markdown table, no bold.

First line: `# out > in | Score ΔBASE Δw Δw(season) ΔP(title) Δage | status`

One shape per line:

`Cade+'27 1st > Brunson | +2200 +700 +1.9 +0.8 +9% +1.4 | Us proposed 9/10`

- Players: bare name. Picks: `'27 1st` (no brackets). Join assets with `+`.
- Six numbers, space-separated, already rounded. `?` for a number not yet priced. Keep `+` and `%`. Omit status when blank. Strip bold and strike; status text carries a rejection.
- Keep section headers (`## Above floor`, …) and any prose under them. Strip `**` from prose.

# Archive workflow

Run sims first (`sims` Skill). From stdout / JSON `results`:

1. Map `score_us` → **Score** (nearest 100) · `delta_base_us` → **ΔBASE** (nearest 100) · `fdw_us` → **Δw** (nearest tenth) · `dw_us` → **Δw (season)** (nearest tenth) · `dp_title_us` → **ΔP(title)** (nearest whole, `%` suffix) · `dage_us` → **Δage** (nearest tenth). A deal with `eval_gap` (stdout `! <label>:` line): don't archive it; fix the eval or config, then `--refresh`.
2. Add or update the row in both files; apply §Sections (tier, re-home lopsided / minimums, human bold, sort). Agent line per §Agent file.
3. Delete or overwrite the tmp JSON when done.

# Adding new shapes

1. Append the short list's deal bodies to tmp JSON (`trades` §Brainstorm, `sims` Skill).
2. Run `sim_run.py`.
3. Archive per §Archive workflow.

# Refresh

When roster or projections changed — rebuild tmp JSON from `.shapes.md` rows + eval rosters (edit JSON directly), run `sim_run.py --refresh` (`sims` Skill), update every row in both files from fresh `results`; apply §Sections.

Do not re-quote stale table rows without a fresh run when inputs moved.

# Notes

- **Never** index on other trade shapes files / use as reference on how to do this. Just follow instructions given / this skill faithfully.
