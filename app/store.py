"""SQLite persistence.

stdlib only. One file, no server, no cost - correct for one client per instance,
which is where v1 lives. Swapping to Postgres later means replacing this module
and nothing else.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Iterable, Optional

from .models import ConvState, Contact, Conversation, Direction, Message, Outcome

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    wa_id         TEXT PRIMARY KEY,
    display_name  TEXT,
    first_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    wa_message_id TEXT PRIMARY KEY,          -- dedupes Meta's webhook retries
    wa_id         TEXT NOT NULL,
    direction     TEXT NOT NULL,
    timestamp     TEXT NOT NULL,
    text          TEXT,
    read_at       TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_wa_id ON messages(wa_id, timestamp);

-- The client's own login. One instance per client, so at most one row - but a
-- table rather than a config value, because the client sets it themselves and
-- we must never know or store it in plaintext.
CREATE TABLE IF NOT EXISTS account (
    wa_number     TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

-- One-time claim links. Hashed, so a leaked database does not hand over a live
-- setup link, and single-use, so a forwarded link cannot be redeemed twice.
CREATE TABLE IF NOT EXISTS setup_codes (
    code_hash  TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    used_at    TEXT
);

-- One row per Coexistence history phase (0: last day, 1: day 1-90, 2: day
-- 90-180). Chunks arrive out of order, so progress is kept as a high-water mark
-- rather than overwritten.
CREATE TABLE IF NOT EXISTS sync_phases (
    phase       INTEGER PRIMARY KEY,
    progress    INTEGER NOT NULL DEFAULT 0,
    chunks      INTEGER NOT NULL DEFAULT 0,
    imported    INTEGER NOT NULL DEFAULT 0,
    started_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    wa_id           TEXT PRIMARY KEY,
    last_message_at TEXT NOT NULL,
    last_direction  TEXT NOT NULL,
    state           TEXT NOT NULL,
    outcome         TEXT,
    quoted_amount   INTEGER,
    quoted_at       TEXT,
    closed_at       TEXT
);
"""


def _dt(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


def _iso(value: Optional[datetime]) -> Optional[str]:
    return value.astimezone(timezone.utc).isoformat() if value else None


class Store:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ---- contacts ----

    def upsert_contact(self, contact: Contact) -> None:
        self.conn.execute(
            """INSERT INTO contacts (wa_id, display_name, first_seen_at)
               VALUES (?, ?, ?)
               ON CONFLICT(wa_id) DO UPDATE SET
                 display_name = COALESCE(excluded.display_name, contacts.display_name)""",
            (contact.wa_id, contact.display_name, _iso(contact.first_seen_at)),
        )
        self.conn.commit()

    def contact_name(self, wa_id: str) -> Optional[str]:
        row = self.conn.execute(
            "SELECT display_name FROM contacts WHERE wa_id = ?", (wa_id,)
        ).fetchone()
        return row["display_name"] if row else None

    # ---- messages ----

    def add_message(self, msg: Message) -> bool:
        """Returns False if we have seen this message id before.

        Meta retries deliveries; without this every retry would re-fold the same
        message into the conversation.
        """
        cur = self.conn.execute(
            """INSERT OR IGNORE INTO messages
               (wa_message_id, wa_id, direction, timestamp, text, read_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (msg.wa_message_id, msg.wa_id, msg.direction.value,
             _iso(msg.timestamp), msg.text, _iso(msg.read_at)),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def mark_read(self, wa_message_id: str, read_at: datetime) -> None:
        """Enrichment only - never feeds a state."""
        self.conn.execute(
            "UPDATE messages SET read_at = ? WHERE wa_message_id = ? AND read_at IS NULL",
            (_iso(read_at), wa_message_id),
        )
        self.conn.commit()

    def messages_for(self, wa_id: str, limit: int = 50) -> list[Message]:
        rows = self.conn.execute(
            """SELECT * FROM (
                   SELECT * FROM messages WHERE wa_id = ?
                   ORDER BY timestamp DESC LIMIT ?
               ) ORDER BY timestamp ASC""",
            (wa_id, limit),
        ).fetchall()
        return [
            Message(
                wa_message_id=r["wa_message_id"],
                wa_id=r["wa_id"],
                direction=Direction(r["direction"]),
                timestamp=_dt(r["timestamp"]),
                text=r["text"],
                read_at=_dt(r["read_at"]),
            )
            for r in rows
        ]

    # ---- conversations ----

    def get_conversation(self, wa_id: str) -> Optional[Conversation]:
        row = self.conn.execute(
            "SELECT * FROM conversations WHERE wa_id = ?", (wa_id,)
        ).fetchone()
        return self._conv(row) if row else None

    def save_conversation(self, conv: Conversation) -> None:
        self.conn.execute(
            """INSERT INTO conversations
               (wa_id, last_message_at, last_direction, state, outcome,
                quoted_amount, quoted_at, closed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(wa_id) DO UPDATE SET
                 last_message_at = excluded.last_message_at,
                 last_direction  = excluded.last_direction,
                 state           = excluded.state,
                 outcome         = excluded.outcome,
                 quoted_amount   = excluded.quoted_amount,
                 quoted_at       = excluded.quoted_at,
                 closed_at       = excluded.closed_at""",
            (conv.wa_id, _iso(conv.last_message_at), conv.last_direction.value,
             conv.state.value, conv.outcome.value if conv.outcome else None,
             conv.quoted_amount, _iso(conv.quoted_at), _iso(conv.closed_at)),
        )
        self.conn.commit()

    def all_conversations(self) -> list[Conversation]:
        rows = self.conn.execute(
            "SELECT * FROM conversations ORDER BY last_message_at DESC"
        ).fetchall()
        return [self._conv(r) for r in rows]

    # ---- account ----

    def account(self) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM account LIMIT 1").fetchone()
        return dict(row) if row else None

    def create_account(self, wa_number: str, password_hash: str) -> None:
        self.conn.execute(
            "INSERT INTO account (wa_number, password_hash, created_at) VALUES (?, ?, ?)",
            (wa_number, password_hash, _iso(datetime.now(timezone.utc))),
        )
        self.conn.commit()

    def set_password(self, wa_number: str, password_hash: str) -> None:
        self.conn.execute("UPDATE account SET password_hash = ? WHERE wa_number = ?",
                          (password_hash, wa_number))
        self.conn.commit()

    # ---- one-time setup codes ----

    def add_setup_code(self, code_hash: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO setup_codes (code_hash, created_at) VALUES (?, ?)",
            (code_hash, _iso(datetime.now(timezone.utc))),
        )
        self.conn.commit()

    def setup_code_valid(self, code_hash: str) -> bool:
        row = self.conn.execute(
            "SELECT used_at FROM setup_codes WHERE code_hash = ?", (code_hash,)
        ).fetchone()
        return bool(row) and row["used_at"] is None

    def burn_setup_code(self, code_hash: str) -> bool:
        """Single-use, enforced by the UPDATE itself so two simultaneous
        redemptions cannot both win."""
        cur = self.conn.execute(
            "UPDATE setup_codes SET used_at = ? WHERE code_hash = ? AND used_at IS NULL",
            (_iso(datetime.now(timezone.utc)), code_hash),
        )
        self.conn.commit()
        return cur.rowcount > 0

    # ---- history sync ----

    def record_sync_chunk(self, phase: int, progress: int, imported: int) -> None:
        """Fold one history chunk's metadata in. Progress only ever goes up, so a
        late-arriving early chunk cannot make a finished import look unfinished."""
        now = _iso(datetime.now(timezone.utc))
        self.conn.execute(
            """INSERT INTO sync_phases (phase, progress, chunks, imported, started_at, updated_at)
               VALUES (?, ?, 1, ?, ?, ?)
               ON CONFLICT(phase) DO UPDATE SET
                 progress   = MAX(sync_phases.progress, excluded.progress),
                 chunks     = sync_phases.chunks + 1,
                 imported   = sync_phases.imported + excluded.imported,
                 updated_at = excluded.updated_at""",
            (phase, progress, imported, now, now),
        )
        self.conn.commit()

    def sync_phases(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM sync_phases ORDER BY phase ASC"
        ).fetchall()
        return [
            {
                "phase": r["phase"],
                "progress": r["progress"],
                "chunks": r["chunks"],
                "imported": r["imported"],
                "started_at": r["started_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    @staticmethod
    def _conv(row: sqlite3.Row) -> Conversation:
        return Conversation(
            wa_id=row["wa_id"],
            last_message_at=_dt(row["last_message_at"]),
            last_direction=Direction(row["last_direction"]),
            state=ConvState(row["state"]),
            outcome=Outcome(row["outcome"]) if row["outcome"] else None,
            quoted_amount=row["quoted_amount"],
            quoted_at=_dt(row["quoted_at"]),
            closed_at=_dt(row["closed_at"]),
        )
