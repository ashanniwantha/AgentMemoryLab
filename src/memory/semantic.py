"""
Semantic memory: stores structured facts about the user.
"""

import aiosqlite

from typing import Optional, Dict, Any, List
from uuid import uuid4, UUID

from src.config.settings import SQL_DB_PATH


async def init_semantic_table():
    """Create a semantic_memory table if it doesn't exist."""
    async with aiosqlite.connect(SQL_DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS semantic_memory (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                version INTEGER DEFAULT 1,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        # Create an index for fast lookup
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_semantic_session_key
            ON semantic_memory (session_id, key)
        """
        )

        await db.commit()


async def save_fact(session_id: UUID, key: str, value: str, confidence: float = 1.0):
    """
    Insert or update a fact for a session.
    If the fact with same key already exists and the value is different,
    we update it (increment version, set new value/confidence).
    """
    async with aiosqlite.connect(SQL_DB_PATH) as db:

        # Check if the fact already exists
        async with db.execute(
            "SELECT value, version FROM semantic_memory WHERE session_id=? AND key=?",
            (str(session_id), key),
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            old_value, old_version = row
            if old_value != value:
                # Update with the new value and increment version
                await db.execute(
                    """
                    UPDATE semantic_memory
                    SET value=?, confidence=?, version=?, updated_at=CURRENT_TIMESTAMP
                    WHERE session_id=? AND key=?
                """,
                    (value, confidence, old_version + 1, str(session_id), key),
                )
        else:
            # Insert new fact
            await db.execute(
                """
                INSERT INTO semantic_memory (id, session_id, key, value, confidence, version)
                VALUES (?, ?, ?, ?, ?, 1)
            """,
                (str(uuid4()), str(session_id), key, value, confidence),
            )

        await db.commit()


async def get_fact(session_id: UUID, key: str) -> Optional[Dict[str, Any]]:
    """
    Return the latest fact for a given key, or None if not found.
    """
    async with aiosqlite.connect(SQL_DB_PATH) as db:
        async with db.execute(
            """
            SELECT key, value, confidence, version, updated_at
            FROM semantic_memory
            WHERE session_id=? AND key=?
            ORDER BY version DESC
            LIMIT 1
        """,
            (str(session_id), key),
        ) as cursor:
            row = await cursor.fetchone()

    if row:
        return {
            "key": row[0],
            "value": row[1],
            "confidence": row[2],
            "version": row[3],
            "updated_at": row[4],
        }
    return None


async def get_all_facts(session_id: UUID) -> List[Dict[str, Any]]:
    """
    Return all facts for a session (one per key).
    """
    async with aiosqlite.connect(SQL_DB_PATH) as db:
        async with db.execute(
            """
            SELECT sm.key, sm.value, sm.confidence, sm.version, sm.updated_at
            FROM semantic_memory sm
            INNER JOIN (
                SELECT key, MAX(version) as max_version
                FROM semantic_memory
                WHERE session_id=?
                GROUP BY key
            ) latest ON sm.key = latest.key AND sm.version = latest.max_version
            WHERE sm.session_id=?
        """,
            (str(session_id), str(session_id)),
        ) as cursor:
            rows = await cursor.fetchall()

    facts = []
    for row in rows:
        facts.append(
            {
                "key": row[0],
                "value": row[1],
                "confidence": row[2],
                "version": row[3],
                "updated_at": row[4],
            }
        )
    return facts


async def delete_fact(session_id: UUID, key: str):
    """Remove all versions of a fact for a session."""
    async with aiosqlite.connect(SQL_DB_PATH) as db:
        await db.execute(
            "DELETE FROM semantic_memory WHERE session_id=? AND key=?",
            (str(session_id), key),
        )
        await db.commit()
