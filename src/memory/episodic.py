"""
Episodic memory: raw conversation storage using SQLite
"""

import aiosqlite
from datetime import datetime

from typing import List, Tuple
from uuid import uuid4, UUID

from src.config import settings


async def init_db():
    """
    Create the message table if not exists.
    Execute this once when the program start
    """

    async with aiosqlite.connect(settings.SQL_DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )               
        """
        )

        await db.commit()


async def save_message(session_id: UUID, role: str, content: str):
    """
    Insert a message into the database.
    """

    async with aiosqlite.connect(settings.SQL_DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            (str(uuid4()), str(session_id), role, content),
        )

        await db.commit()


async def get_recent_messages(
    session_id: UUID, limit: int = 10
) -> List[Tuple[str, str]]:
    """Return the most recent messages for a session, oldest first."""
    async with aiosqlite.connect(settings.SQL_DB_PATH) as db:
        async with db.execute(
            """
            SELECT role, content FROM messages
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (str(session_id), limit),
        ) as cursor:
            rows = await cursor.fetchall()
    # Convert each Row to a tuple of (role, content) and reverse to oldest first
    result = [(row[0], row[1]) for row in rows]
    return result[::-1]
