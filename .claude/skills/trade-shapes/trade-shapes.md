---
description: Use when archiving, refreshing or re-tiering a team's trade shapes (`.shapes.md` / `Trade Shapes.md`)
---

Always load/follow `trades` Skill.

# Files

- Agent file: `strategy/teams/<owner>/<Name>.shapes.md` (§Agent file). Read and rebuild deal bodies from this one
- Human file: `<Name> Trade Shapes.md`, same directory (§Table format). Written in full from the agent file by a spawned subagent (`AGENTS.md` §Team files)

Every archive or refresh writes both, agent file first.

# Workflow

1. **Sim** per `sims` Skill. New shapes: append the short list's deal bodies to tmp JSON (`trades` §Brainstorm). Refresh (roster or projections changed): rebuild tmp JSON from every `.shapes.md` row + eval rosters and run `--refresh`. Done when every deal has `results`.
2. **Gaps:** a deal with `eval_gap` (stdout `! <label>:` line) isn't archived; fix the eval or config, then `--refresh`.
3. **Map** `results` → columns: `score_us` Score · `delta_base_us` ΔBASE · `fdw_us` Δw · `dw_us` Δw (season) · `dp_title_us` ΔP(title) · `dage_us` Δage, rounded per §Table format.
4. **Agent file:** add or update each row (on refresh, every row); place per §Sections, sort per §Tiering and sort.
5. **Human file:** spawn the subagent to write it in full from the agent file.
6. Delete or overwrite the tmp JSON.

When inputs moved, quote rows only after a fresh run.

# Sections

Five sections, **top to bottom**: `## Above floor` → `## Floor` → `## Below bar` → `## Too lopsided` → `## Doesn't meet our minimums`.

| Section | When |
|---|---|
| Above floor | Clearly better than floor; we'd actively pursue |
| Floor | We'd take it if that's all we could get |
| Below bar | Not worth pursuing, but meets `trades` §General guidlines minimums |
| Too lopsided | Too lopsided per `trades` §General guidlines; reference only, never floated |
| Doesn't meet our minimums | Fails an archive-fail threshold in `trades` §General guidlines; reference only, never floated |

**Placement order** (each row lives in exactly one section):

1. Assign a tier (above floor / floor / below bar) per §Tiering and sort.
2. Too lopsided → `## Too lopsided`.
3. Else fails any minimum → `## Doesn't meet our minimums`.
4. Else keep the tier from step 1.

Executed deals stay out of shape rows.

# Tiering and sort

`Score` (`Eval Definitions §Score`) is the baseline: a starting order, not a verdict. Still read every number individually.

- **Tier** by `Score` against the floor: the best live alternative for the same assets (e.g. a benchmark offer), else what we'd settle for. Clearly above → Above floor, near → Floor, clearly below → Below bar. No floor yet → tier by judgment, `Score` as a guide. Override a row's `Score` tier only for something the score misses (roster context, `Δage`, competitor rules)
- **Sort** each actionable tier by `Score`, highest first; order ties (~250) by judgment on the individual numbers. Re-sort after every refresh or tier move
- **Too lopsided:** sort by ΔBASE, highest first
- **Doesn't meet our minimums:** sort by `Score`, lowest first; don't bold failed minimums

# Table format

Human file: one markdown table per section. Columns: `Out | In | Score | ΔBASE | Δw | Δw (season) | ΔP(title) | Δage`, then optional **Status**.

**Round:** `Score` and `ΔBASE` nearest 100 · win columns nearest tenth · `ΔP(title)` nearest whole with `%` suffix (`+5%`, `-2%`, `0%`) · `Δage` nearest tenth, signed (`+3.2`, `-1.2`, `0.0`). Picks are 0 in win columns. No `*` on any cell.

**Out** = our side; **In** = theirs. Each cell is one HTML bullet list, one asset per `<li>`, this exact wrapper even for a single asset:

```html
<ul style="list-style-type:disc;margin:0;padding-left:1.25em">
  <li>…</li>
</ul>
```

- **Players:** `**Name**` (last name or eval nickname) inside each `<li>`, no age or projection metadata. Out-side names from our eval; In-side from theirs
- **Picks:** on the side that sends them, as their own `<li>`, bold in square brackets: `**['27 1st]**`, `**[Chris '27 2.09]**` (ours bare, others original owner first per `AGENTS.md` §Naming; slot notation per `eval-pick`). Never parentheses or `+`-joined to a player
- **Bold:** Score, ΔBASE, Δw, Δw (season), ΔP(title) when positive, with `+` prefix on positive win numbers; Δage when negative; non-beneficial numbers plain. `ΔP(title)` keeps its `%` inside bold/strike (`**+10%**`, `~~**+6%**~~`, `-2%`, `0%`)
- **Status:** negotiation status only, latest only: `Us proposed`, `{owner} proposed`, `Us rejected` or `{owner} rejected` + date, verb bold (e.g. `Hlina **rejected** 9/2`). A rejection or superseding status replaces an earlier proposed. Blank when unset. Commentary and negotiation color go in the file intro or counterparty notes
- **Rejected rows:** strike through every other cell (`~~…~~`), including each `<li>` body (`<li>~~**Kessler**~~</li>`); Status stays plain (verb still bold)

**Rebuild for sim:** deal `label` = the agent line's `out > in` (`Δage` reads later picks from it); player arrays = bare names only; picks → JSON pick BASE fields (`sims` [config.md](../sims/config.md)), labeled like `Chris '27 1st`.

# Agent file

Same sections, prose and row order as the human file; no HTML, markdown table or bold.

First line: `# out > in | Score ΔBASE Δw Δw(season) ΔP(title) Δage | status`

One shape per line, e.g. `Cade+'27 1st > Brunson | +2200 +700 +1.9 +0.8 +9% +1.4 | Us proposed 9/10`

- Players: bare name. Picks: `'27 1st`, `Chris '27 2nd` (no brackets). Join assets with `+`
- Six numbers, space-separated, already rounded, keeping `+` and `%`; `?` for a number not yet priced. Omit a blank status. No bold or strike; the status text carries a rejection
- Keep section headers (`## Above floor`, …) and any prose under them, `**` stripped

# Notes

- Take format from this skill only, not from other teams' shapes files
