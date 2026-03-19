"""
Summmarization history: stores conversation story
"""

import sqlite3
from typing import Optional
from uuid import UUID, uuid4

from src.config import settings


def init_summary_table():
    """Create the summaries table if doesn't exists"""
    conn = sqlite3.connect(settings.SQL_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS summaries (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            message_count INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP 
        )
    """
    )

    conn.commit()
    conn.close()


def save_summary(session_id: UUID, summary: str, message_count: int):
    """Store summary for a session on given message count"""
    conn = sqlite3.connect(settings.SQL_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO summaries (id, session_id, summary, message_count) VALUES (?, ?, ?, ?)",
        (str(uuid4()), str(session_id), summary, message_count),
    )

    conn.commit()
    conn.close()


def get_latest_summary(session_id: UUID) -> Optional[str]:
    """Retrive the latest summary for a session, if any"""
    conn = sqlite3.connect(settings.SQL_DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT summary FROM summaries
        WHERE session_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """,
        (str(session_id),),
    )

    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
