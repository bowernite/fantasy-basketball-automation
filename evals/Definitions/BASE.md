# BASE

Expands `Eval Definitions §BASE`.

Blended points-format dynasty board rank and nothing else. **No adjustment by us for injury, durability, role, team situation, contract or aging** — the rank prices all six. **This binds BASE only**: the rate and `GP` feeding both win columns are projections (`Eval Definitions §Δw (season)`). BASE is the market price, not the truth; divergence is the edge. Picks: `eval-pick`.

| Board          | Weight | Skill                |
| -------------- | ------ | -------------------- |
| Dizzle Points  | 40%    | `dizzle-dynasty`     |
| Hashtag Points | 35%    | `hashtag-basketball` |

Hashtag crowd is the `Boards` figure in parens — printed, not blended. Weights renormalise when a blended board is absent (`~53.3 / 46.7` when both present).

Dynatyze (`dynatyze`) is too shallow to blend — reference only. Before adding a source, count analysts, not boards (`eval-player` §*Caveats*).

**`V()` each board's rank, then weight-average the values** — never average ranks first.

```
D    = teams × roster_size          # rostered players; past D a player is free
a    = √D                           # rank a is worth half of rank 1
V(r) = 9999 × (a+1)/(D−1) × (D−r)/(a+r)     for r < D, else 0
```

`roster_size` = **the size in effect for the season being valued** (`league-info`); flag it whenever current and announced differ. **BASE is comparable only within one `D`** — re-run every eval when the league resizes.

**Never divide by BASE** — no BASE-normalised ratio, anywhere; compare in absolute terms.

# Summing across a package

`a` is asserted, not measured, and a sum over unlike pieces inherits that. **Equal body count with no picks → the point value stands.** Otherwise publish `ΔBASE` as a band: sweep `a` over `[√D/2, 2√D]`, re-blend every player and re-price every pick at each step, and take **min/max over the whole sweep — the extreme is often interior, never read it off the endpoints.**

- **A band spanning zero is a BASE tie.** Publish the band; never quote the point value or its sign.
- Width tracks the body-count gap — a 1-for-1 barely moves, a 5-for-1 spans thousands.
- Stack it with any pick-slot range already carried (`eval-pick` §*Future picks*): min/max over both at once, one band.
- **Never charge a roster slot in BASE to offset body count** — the correction lands an order of magnitude under the band, and `Δw` prices body count already (`Format edges.md`).

# Depth and absence

Fetch every blended board as deep as it goes, record that depth (a dated fact — belongs in the eval), then per board per player:

| | |
| ---------------------------------------------------- | ---------------------------------------------------------------- |
| rank < `D`                                           | `V(rank)`                                                        |
| rank ≥ `D`, or absent from a board that reaches `D`  | **0** — absence is a statement of value                          |
| absent from a board that stops short of `D`          | renormalise that board's weight away, **for that player only**   |

Renormalise only where absence and below-depth are indistinguishable.

⚠️ **A board that puts a player past `D` while another ranks him inside 200 is a disagreement, not a price.** The blend still averages it, but hides the dispersion: a board ranking a player past `D` is saying *he is not rosterable*. **Flag any row whose per-board ranks straddle `D`** (`Eval Template.md`, `board split`). A row that is both split that way and a wide low-BASE/high-`Δw` gap signals the boards pricing a role or career risk no column here carries — never publish it as a buy without naming the split.
