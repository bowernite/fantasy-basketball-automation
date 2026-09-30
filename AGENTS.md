# Fantasy Basketball

## Objective

**Maximize titles over the next ~20 seasons**: weight seasons 1–7 equally, then discount 5% per season after that (the league may not last).

## Subagents

Fetch league data and board data in subagents, in parallel / background when possible.

## Scripts

Use only existing scripts; do tiering, sorting, archiving, and comparisons by your own reasoning. For sim output, run the existing lineup-math scripts and copy stdout.

## Naming

Refer to teams by the owner's Name from the `team-info` Skill everywhere (reports, texts, files, tables), never the fantasy team name or its abbreviation. Label a pick by its original owner, e.g. "Chris '27 2nd", not "KC '27 2nd".

## Team files

Read only `strategy/teams/<owner>/<Name>.team.md` and `<Name>.shapes.md` (the agent files); read and edit them directly. Never read, grep, or shell-print the human files: `*'s Team.md`, `My Team.md`, `* Trade Shapes.md`.

Write a human file only when the `eval-team` or `trade-shapes` Skill calls for it: a spawned subagent writes the whole file via Bash (`cat > … <<'EOF'`), never Edit or Write.

## Writing `.md` files

Always load/follow the `instructions-and-docs-ff` Skill when writing or editing any `.md` file
