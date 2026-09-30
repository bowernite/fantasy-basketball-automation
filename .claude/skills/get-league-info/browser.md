Runs in a subagent like API calls (`get-league-info` §Fetch in a subagent). `browser` Skill for commands. Base URL `https://www.fleaflicker.com/nba/leagues/30579` (`/` standings · `/teams/<id>` · `/players` · `/scores/<gameId>` · `/trades` · `/activity` · `/rules` · `/drafts`).

- Most pages render **logged out**. Log in only for Waivers/Watched/Settings or lineup edits; credentials are `FF_EMAIL` / `FF_PASSWORD` in the gitignored `.env` (not the keychain). Keep the password out of output
- **Reuse the parsers in `src/page/` and `src/data/`** rather than writing selectors — they handle the single-`<table>` layout, the `.injury` badge, and the prerendered `window.pageData.tooltips` map (hovering is the slow fallback)
- Dropdowns are anchor menus, not `<select>`: read `.dropdown-menu a[href]` for valid param values and navigate directly
- Stat columns are season-labelled — confirm which season a table shows before reading it
