#   python3 .claude/skills/read-messages/test_read_messages.py
import pathlib
import sqlite3
import sys
import unittest

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import read_messages  # noqa: E402


def seed_chat_db():
    """Minimal chat.db: same handle in a DM and a group."""
    con = sqlite3.connect(":memory:")
    con.executescript(
        """
        CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT);
        CREATE TABLE chat (
            ROWID INTEGER PRIMARY KEY,
            style INTEGER,
            room_name TEXT,
            chat_identifier TEXT
        );
        CREATE TABLE chat_handle_join (chat_id INTEGER, handle_id INTEGER);
        CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER);
        CREATE TABLE message (
            ROWID INTEGER PRIMARY KEY,
            guid TEXT,
            handle_id INTEGER,
            date INTEGER,
            is_from_me INTEGER,
            text TEXT,
            attributedBody BLOB,
            associated_message_type INTEGER,
            reply_to_guid TEXT
        );
        """
    )
    con.execute("INSERT INTO handle (ROWID, id) VALUES (1, '+15551234567')")
    con.execute(
        "INSERT INTO chat (ROWID, style, room_name, chat_identifier) VALUES (10, 45, NULL, '+15551234567')"
    )
    con.execute(
        "INSERT INTO chat (ROWID, style, room_name, chat_identifier) VALUES (20, 43, 'chatroom', 'chat999')"
    )
    con.execute("INSERT INTO chat_handle_join VALUES (10, 1)")
    con.execute("INSERT INTO chat_handle_join VALUES (20, 1)")
    # older group msg, newer DM msg — DESC LIMIT would prefer DM if both match; include
    # enough group noise that a handle-only query returns group text first.
    con.execute(
        """INSERT INTO message (ROWID, guid, handle_id, date, is_from_me, text, attributedBody, associated_message_type)
           VALUES (1, 'g1', 1, 100, 0, 'group only chatter', NULL, 0)"""
    )
    con.execute(
        """INSERT INTO message (ROWID, guid, handle_id, date, is_from_me, text, attributedBody, associated_message_type)
           VALUES (2, 'g2', 1, 200, 0, 'dm hello', NULL, 0)"""
    )
    con.execute(
        """INSERT INTO message (ROWID, guid, handle_id, date, is_from_me, text, attributedBody, associated_message_type)
           VALUES (3, 'g3', 1, 300, 0, 'more group noise', NULL, 0)"""
    )
    con.execute("INSERT INTO chat_message_join VALUES (20, 1)")
    con.execute("INSERT INTO chat_message_join VALUES (10, 2)")
    con.execute("INSERT INTO chat_message_join VALUES (20, 3)")
    return con


def add_dm(con, rowid, date, text, **kwargs):
    con.execute(
        """INSERT INTO message (ROWID, guid, handle_id, date, is_from_me, text, attributedBody,
                                 associated_message_type, reply_to_guid)
           VALUES (?, ?, 1, ?, ?, ?, NULL, 0, ?)""",
        (
            rowid,
            kwargs.get("guid", f"g{rowid}"),
            date,
            kwargs.get("is_from_me", 0),
            text,
            kwargs.get("reply_to_guid"),
        ),
    )
    con.execute("INSERT INTO chat_message_join VALUES (10, ?)", (rowid,))


def bodies(rows):
    return [read_messages.message_body(r[2], r[3], r[4]) for r in rows]


class FetchMessagesDmOnly(unittest.TestCase):
    def test_skips_group_chat_messages_for_same_handle(self):
        con = seed_chat_db()
        rows = read_messages.fetch_messages(con, [1], limit=10)
        self.assertEqual(bodies(rows), ["dm hello"])

    def test_skip_omits_newest(self):
        con = seed_chat_db()
        add_dm(con, 4, 400, "newer")
        add_dm(con, 5, 500, "newest")
        rows = read_messages.fetch_messages(con, [1], limit=10, skip=2)
        self.assertEqual(bodies(rows), ["dm hello"])

    def test_before_excludes_that_date_and_newer(self):
        con = seed_chat_db()
        add_dm(con, 4, 400, "mid")
        add_dm(con, 5, 500, "newest")
        rows = read_messages.fetch_messages(con, [1], limit=10, before=400)
        self.assertEqual(bodies(rows), ["dm hello"])

    def test_skip_and_before(self):
        con = seed_chat_db()
        add_dm(con, 4, 400, "mid")
        add_dm(con, 5, 500, "newest")
        add_dm(con, 6, 150, "oldest")
        rows = read_messages.fetch_messages(con, [1], limit=10, skip=1, before=400)
        self.assertEqual(bodies(rows), ["oldest"])

    def test_to_mac_ns_matches_printed_timestamp(self):
        ts = "2024-06-15 14:30:00"
        ns = read_messages.to_mac_ns(ts)
        printed = sqlite3.connect(":memory:").execute(
            "SELECT datetime(?/1000000000 + strftime('%s','2001-01-01'), 'unixepoch', 'localtime')",
            (ns,),
        ).fetchone()[0]
        self.assertEqual(printed, ts)

    def test_reply_to_parent_message(self):
        con = seed_chat_db()
        add_dm(con, 4, 400, "Duren+Suggs for Paolo+Camara?", is_from_me=1, guid="parent")
        add_dm(con, 5, 500, "counter offer", guid="child", reply_to_guid="parent")
        rows = read_messages.fetch_messages(con, [1], limit=10)
        self.assertEqual(bodies(rows), ["counter offer", "Duren+Suggs for Paolo+Camara?", "dm hello"])
        note = read_messages.format_reply_note("Pat", rows[0])
        self.assertEqual(note, "  ↳ replying to me: Duren+Suggs for Paolo+Camara?")


if __name__ == "__main__":
    unittest.main()
