"""
Episodic memory: raw conversation storage using SQLite
"""

import sqlite3
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4, UUID

from src.config import settings


def init_db():
    """
    Create the message table if not exists.
    Execute this once when the program start
    """

    conn = sqlite3.connect(settings.SQL_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )               
    """
    )

    conn.commit()
    conn.close()


def save_message(session_id: UUID, role: str, content: str):
    """
    Insert a message into the database.
    """

    conn = sqlite3.connect(settings.SQL_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
        (str(uuid4()), str(session_id), role, content),
    )

    conn.commit()
    conn.close()


def get_recent_messages(session_id: UUID, limit: int = 10) -> List[Tuple[str, str]]:
    """
    Return the most recent messages from a session, oldest first.
    Each tuple is (role, content).
    """

    conn = sqlite3.connect(settings.SQL_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT role, content FROM messages
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT ?""",
        (str(session_id), limit),
    )

    rows = cursor.fetchall()
    conn.close()

    return list(reversed(rows))
