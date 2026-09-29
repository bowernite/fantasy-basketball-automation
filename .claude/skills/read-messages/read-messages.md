---
name: read-messages
description: Read local iMessage history with a league mate — use when a trade negotiation happened over text and you need what was actually said.
---

```
python3 .claude/skills/read-messages/read_messages.py "<contact name|phone>" [limit]
```

Resolves the name against Contacts, finds every matching iMessage handle, prints
oldest→newest DM messages as `timestamp | sender: body` (group chats excluded).
Swipe-replies print the quoted message on the next line as `↳ replying to …`.

Reply detection uses `reply_to_guid` from the DB. iMessage often sets that to
the chronologically prior message even when you did not swipe-reply, so the
script only **suppresses** reply context when the same person sent that prior
message within ~2 minutes (rapid multi-text burst). Otherwise it shows the
link — including when someone replies to one of several offers you sent in a
row, or when `reply_to_guid` happens to match the message above after a gap.
That can produce a false positive (e.g. your next text after a week away looks
like a reply to their last message). Treat `↳` as best-effort context, not proof.

- Prefer full name; a partial that matches two contacts exits with the candidates.
- Default limit 30. Raise it rather than re-running with different names.
- Cross-reference the owner via `team-info` before reasoning about a deal.

# Going back

Read last 10. If the oldest is about fantasy basketball, fetch the next 10 with `--skip` (count already printed) or `--before` (oldest timestamp already printed). Repeat until fantasy conversations stopped.

# Reading today's date

Always capture today's date as well (it'll put into context the timestamps of the conversation)

# Notes

- **Read-only.** Never send a message or write to the DB. Draft replies as text for the user to send.
- Attachments, reactions and unsupported payloads print as `[tapback]` / `[no text]`; treat gaps as unknown, don't infer content.
- Private data: query narrowly for the task at hand, and quote only what the answer needs.

# Finding contact names

See `team-info` Skill if you need to map team name to a contact name

_Maps name to contact name_

- Micheal or Bonin -> `Michael Bonin`
- Josh -> `Josh Damro`
- Chris -> `Chris Kelnhofer`
- Brian -> `Brian Weidenfeller`
- Joe -> `Joe Kelnhofer`
- Matt or Hlina -> `Matt Hlina`
- Matthew -> `Matthew Pook`
  > **Henry:** query `Henry`. Do not expand to the full Contacts label — apostrophe is U+2019 (`'`), not ASCII `'`.
- Henry -> `Henry` (Contacts label: `Henry (Chris’s cousin)`)
- Jon -> `Jon Drew`
- Mitch -> `Mitch Brault`
- Todd -> `Todd Marino`
