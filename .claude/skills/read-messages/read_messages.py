#!/usr/bin/env python3
"""Read iMessage history for a contact. Usage: read_messages.py <name|number> [limit] [--skip N] [--before TIMESTAMP]"""
import argparse
import glob
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

CHAT_DB = os.path.expanduser("~/Library/Messages/chat.db")
AB_GLOB = os.path.expanduser(
    "~/Library/Application Support/AddressBook/Sources/*/AddressBook-v22.abcddb"
)


def digits(s):
    return re.sub(r"\D", "", s)


def lookup_contact(query):
    """Return (label, [digit-strings]) for a contact name, or None."""
    hits = []
    for db in glob.glob(AB_GLOB):
        try:
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        except sqlite3.Error:
            continue
        rows = con.execute(
            """SELECT ROWID, ZFIRSTNAME, ZLASTNAME FROM ZABCDRECORD
               WHERE (COALESCE(ZFIRSTNAME,'') || ' ' || COALESCE(ZLASTNAME,''))
                     LIKE ? COLLATE NOCASE""",
            (f"%{query}%",),
        ).fetchall()
        for rowid, first, last in rows:
            name = " ".join(filter(None, [first, last]))
            nums = [
                digits(n)
                for (n,) in con.execute(
                    "SELECT ZFULLNUMBER FROM ZABCDPHONENUMBER WHERE ZOWNER = ?", (rowid,)
                )
            ]
            emails = [
                e
                for (e,) in con.execute(
                    "SELECT ZADDRESS FROM ZABCDEMAILADDRESS WHERE ZOWNER = ?", (rowid,)
                )
            ]
            if nums or emails:
                hits.append((name, nums, emails))
        con.close()
    return hits


def find_handles(con, nums, emails):
    ids = set()
    for rowid, hid in con.execute("SELECT ROWID, id FROM handle"):
        d = digits(hid)
        if any(d and d.endswith(n[-10:]) for n in nums if len(n) >= 10):
            ids.add(rowid)
        elif hid.lower() in {e.lower() for e in emails}:
            ids.add(rowid)
    return sorted(ids)


def decode_body(blob):
    """Extract text from the NSAttributedString blob used by modern Messages."""
    if not blob:
        return None
    idxs = [m.start() for m in re.finditer(rb"NSString", blob)]
    if not idxs:
        return None
    rest = blob[idxs[-1] + len(b"NSString") :]
    m = re.search(rb"[\x01\x84\x92\x94\x00]{1,10}\x2b(.)(.{0,2000})", rest, re.DOTALL)
    if not m:
        return None
    text = m.group(2)
    end = text.find(b"\x86")
    if end != -1:
        text = text[:end]
    return text.decode("utf-8", errors="replace").strip() or None


def to_mac_ns(ts):
    """Local `YYYY-MM-DD HH:MM:SS` → Messages date (ns since 2001-01-01 UTC)."""
    unix = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").timestamp()
    mac_epoch = datetime(2001, 1, 1, tzinfo=timezone.utc).timestamp()
    return int((unix - mac_epoch) * 1_000_000_000)


def message_body(text, blob, assoc):
    return text or decode_body(blob) or ("[tapback]" if assoc else "[no text]")


# iMessage often sets reply_to_guid to the prior message even without swipe-reply.
# Only suppress when the same person sent that prior message moments ago.
SAME_SENDER_BURST_SEC = 120


def should_show_reply(mine, prev_mine, reply_to_guid, prev_guid, gap_sec):
    if not reply_to_guid:
        return False
    if reply_to_guid != prev_guid:
        return True
    if (
        prev_mine is not None
        and mine == prev_mine
        and gap_sec is not None
        and gap_sec < SAME_SENDER_BURST_SEC
    ):
        return False
    return True


def format_reply_note(label, row):
    """Return a reply context line for a swipe-reply, or None."""
    mine = row[1]
    reply_to_guid, prev_guid = row[6], row[11]
    prev_mine, gap_sec = row[12], row[13]
    if not should_show_reply(mine, prev_mine, reply_to_guid, prev_guid, gap_sec):
        return None
    reply_mine, reply_text, reply_blob, reply_assoc = row[7:11]
    if reply_mine is None:
        return None
    who = "me" if reply_mine else label
    body = message_body(reply_text, reply_blob, reply_assoc)
    return f"  ↳ replying to {who}: {body}"


def fetch_messages(con, handles, limit, skip=0, before=None):
    """Recent DM messages for handles (style 45); excludes group chats."""
    extra = ""
    if before is not None:
        extra = " AND m.date < ?"
    in_handles = ",".join("?" * len(handles))
    sql = f"""SELECT datetime(m.date/1000000000 + strftime('%s','2001-01-01'),
                            'unixepoch', 'localtime'),
                   m.is_from_me, m.text, m.attributedBody, m.associated_message_type,
                   m.guid, m.reply_to_guid,
                   rt.is_from_me, rt.text, rt.attributedBody, rt.associated_message_type,
                   (SELECT m2.guid
                    FROM message m2
                    JOIN chat_message_join cmj2 ON cmj2.message_id = m2.ROWID
                    JOIN chat c2 ON c2.ROWID = cmj2.chat_id
                    WHERE m2.handle_id IN ({in_handles})
                      AND c2.style = 45
                      AND m2.date < m.date
                    ORDER BY m2.date DESC LIMIT 1),
                   (SELECT m2.is_from_me
                    FROM message m2
                    JOIN chat_message_join cmj2 ON cmj2.message_id = m2.ROWID
                    JOIN chat c2 ON c2.ROWID = cmj2.chat_id
                    WHERE m2.handle_id IN ({in_handles})
                      AND c2.style = 45
                      AND m2.date < m.date
                    ORDER BY m2.date DESC LIMIT 1),
                   (m.date - (SELECT m2.date
                              FROM message m2
                              JOIN chat_message_join cmj2 ON cmj2.message_id = m2.ROWID
                              JOIN chat c2 ON c2.ROWID = cmj2.chat_id
                              WHERE m2.handle_id IN ({in_handles})
                                AND c2.style = 45
                                AND m2.date < m.date
                              ORDER BY m2.date DESC LIMIT 1)) / 1000000000.0
            FROM message m
            JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
            JOIN chat c ON c.ROWID = cmj.chat_id
            LEFT JOIN message rt ON rt.guid = m.reply_to_guid
            WHERE m.handle_id IN ({in_handles})
              AND c.style = 45
              {extra}
            ORDER BY m.date DESC LIMIT ? OFFSET ?"""
    params = (*handles, *handles, *handles, *handles)
    if before is not None:
        params += (before,)
    params += (limit, skip)
    return con.execute(sql, params).fetchall()


def parse_args(argv):
    p = argparse.ArgumentParser(description="Read iMessage history for a contact.")
    p.add_argument("query")
    p.add_argument("limit", nargs="?", type=int, default=30)
    p.add_argument("--skip", type=int, default=0, help="omit the N newest")
    p.add_argument(
        "--before",
        metavar="TIMESTAMP",
        help="only older than this local YYYY-MM-DD HH:MM:SS",
    )
    return p.parse_args(argv)


def main():
    args = parse_args(sys.argv[1:])
    query, limit, skip = args.query, args.limit, args.skip
    before = to_mac_ns(args.before) if args.before else None

    if digits(query) and len(digits(query)) >= 10:
        label, nums, emails = query, [digits(query)], []
    else:
        hits = lookup_contact(query)
        if not hits:
            sys.exit(f"No contact matching {query!r}")
        if len({h[0] for h in hits}) > 1:
            sys.exit("Ambiguous: " + ", ".join(sorted({h[0] for h in hits})))
        label = hits[0][0]
        nums = sorted({n for h in hits for n in h[1]})
        emails = sorted({e for h in hits for e in h[2]})

    con = sqlite3.connect(f"file:{CHAT_DB}?mode=ro", uri=True)
    handles = find_handles(con, nums, emails)
    if not handles:
        sys.exit(f"No iMessage handles for {label} ({nums or emails})")

    rows = fetch_messages(con, handles, limit, skip=skip, before=before)

    for row in reversed(rows):
        ts, mine, text, blob, assoc = row[:5]
        body = message_body(text, blob, assoc)
        print(f"{ts} | {'me' if mine else label}: {body}")
        note = format_reply_note(label, row)
        if note:
            print(note)


if __name__ == "__main__":
    main()
