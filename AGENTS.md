# Fantasy Basketball

## Objective

**Maximize titles over the next ~20 seasons** — weight the first ~7 flat, taper after (league survival uncertainty).

This does not mean we only have a 7 year title window. This just means that I want to maximize titles over the next 20 years, but I start to discount seasons after year 7 or so slightly every year, just because I don't know if the league will exist then. Let's do by 5% per year.

## Subagents

Do the following in subagents, parallelize / put in background when possible:

- Fetching league data
- Fetching board data

## Scripts

Avoid writing your own scripts whenever possible; rely on your own logic instead. Run the existing lineup-math scripts when you need sim output; copy stdout.

# Team files

Read `evals/teams/<owner>/<Name>.team.md` and `<Name>.shapes.md` only. Never read, grep, or shell-print `*'s Team.md`, `My Team.md`, or `* Trade Shapes.md`.

# Notes

- Always load/follow the `instructions-and-docs-ff` Skill when writing to `.md` files
