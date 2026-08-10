# Base

Blended points-format dynasty board rank and nothing else. Keep in mind this is general fantasy basketball value, and doesn't necessarily reflect our league's format and how that might change certain players' value. I _believe_ that should be noted elsewhere.

| Board          | Weight | Skill                |
| -------------- | ------ | -------------------- |
| Dizzle Points  | 40%    | `dizzle-dynasty`     |
| Hashtag Points | 35%    | `hashtag-basketball` |
| Hashtag crowd  | 25%    | `hashtag-basketball` |

_(Dynatyze (`dynatyze`) is too shallow to blend — reference only)_

**`V()` each board's rank, then weight-average the values** — never average ranks first.

```
D    = teams × roster_size          # rostered players; past D a player is free
a    = √D                           # rank a is worth half of rank 1
V(r) = 9999 × (a+1)/(D−1) × (D−r)/(a+r)     for r < D, else 0
```
