"""
Summmarization history: stores conversation story
"""

import aiosqlite
from typing import Optional
from uuid import UUID, uuid4

from src.config import settings


async def init_summary_table():
    """Create the summaries table if doesn't exists"""
    async with aiosqlite.connect(settings.SQL_DB_PATH) as db:
        await db.execute(
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

        await db.commit()


async def save_summary(session_id: UUID, summary: str, message_count: int):
    """Store summary for a session on given message count"""
    async with aiosqlite.connect(settings.SQL_DB_PATH) as db:

        await db.execute(
            "INSERT INTO summaries (id, session_id, summary, message_count) VALUES (?, ?, ?, ?)",
            (str(uuid4()), str(session_id), summary, message_count),
        )
        await db.commit()


async def get_latest_summary(session_id: UUID) -> Optional[str]:
    """Retrive the latest summary for a session, if any"""
    async with aiosqlite.connect(settings.SQL_DB_PATH) as db:

        async with db.execute(
            """
            SELECT summary FROM summaries
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """,
            (str(session_id),),
        ) as cursor:
            row = await cursor.fetchone()

        return row[0] if row else None
