from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d -]{7,}\d)(?!\d)")


def redact(text: str) -> str:
    return PHONE.sub("[PHONE]", EMAIL.sub("[EMAIL]", text))


def normalize(row: dict) -> dict:
    text = redact(str(row["text"]).strip())
    if not text:
        raise ValueError("empty text")
    datetime.fromisoformat(str(row["occurred_at"]).replace("Z", "+00:00"))
    return {
        "message_id": str(row["message_id"]),
        "conversation_id": str(row["conversation_id"]),
        "occurred_at": datetime.fromisoformat(str(row["occurred_at"]).replace("Z", "+00:00")).isoformat(),
        "channel": str(row["channel"]).lower().strip(),
        "author_type": str(row["author_type"]).lower().strip(),
        "text": text,
        "content_hash": hashlib.sha256(text.encode()).hexdigest(),
    }


def _schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, occurred_at TEXT NOT NULL,
            channel TEXT NOT NULL, author_type TEXT NOT NULL, text TEXT NOT NULL, content_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conversation_products (
            conversation_id TEXT PRIMARY KEY, message_count INTEGER NOT NULL,
            first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, customer_messages INTEGER NOT NULL,
            agent_messages INTEGER NOT NULL, redacted_text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rejected_messages (
            message_id TEXT, reason TEXT NOT NULL, raw_json TEXT NOT NULL
        );
        """
    )


def run_pipeline(records: Iterable[dict], database: str | Path) -> dict[str, int]:
    conn = sqlite3.connect(database)
    _schema(conn)
    accepted = rejected = duplicates = 0
    for raw in records:
        try:
            message = normalize(raw)
            cur = conn.execute("INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?, ?, ?, ?)", tuple(message.values()))
            if cur.rowcount:
                accepted += 1
            else:
                duplicates += 1
        except (KeyError, TypeError, ValueError) as exc:
            rejected += 1
            conn.execute("INSERT INTO rejected_messages VALUES (?, ?, ?)", (str(raw.get("message_id")), str(exc), json.dumps(raw, sort_keys=True)))
    rows = conn.execute("SELECT conversation_id, occurred_at, author_type, text FROM messages ORDER BY occurred_at, message_id").fetchall()
    grouped: dict[str, list[tuple]] = {}
    for row in rows:
        grouped.setdefault(row[0], []).append(row)
    for conversation_id, messages in grouped.items():
        customers = sum(row[2] == "customer" for row in messages)
        agents = sum(row[2] == "agent" for row in messages)
        conn.execute("INSERT OR REPLACE INTO conversation_products VALUES (?, ?, ?, ?, ?, ?, ?)", (conversation_id, len(messages), messages[0][1], messages[-1][1], customers, agents, "\n".join(row[3] for row in messages)))
    conn.commit()
    conn.close()
    return {"accepted": accepted, "rejected": rejected, "duplicates": duplicates, "conversations": len(grouped)}
