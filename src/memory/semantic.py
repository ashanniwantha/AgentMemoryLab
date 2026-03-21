"""
Semantic memory: a generic key‑value store with categories.
Used for user facts, drafts, feedback, insights, etc.
"""

import aiosqlite
from typing import Optional, Dict, Any, List
from uuid import uuid4, UUID

from src.config.settings import SQL_DB_PATH


async def init_semantic_table():
    """Create the semantic_memory table if it doesn't exist."""
    async with aiosqlite.connect(SQL_DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS semantic_memory (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'user_fact',
                confidence REAL DEFAULT 1.0,
                version INTEGER DEFAULT 1,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_semantic_session_key
            ON semantic_memory (session_id, key)
        """
        )
        await db.commit()


async def save_semantic(
    session_id: UUID,
    key: str,
    value: str,
    category: str = "user_fact",  # must match table default
    confidence: float = 1.0,
):
    """
    Insert or update an entry in semantic memory.
    If an entry with the same key already exists and the value is different,
    we update it (increment version, set new value/confidence/category).
    """
    async with aiosqlite.connect(SQL_DB_PATH) as db:
        # Check if the entry already exists
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
                    SET value=?, category=?, confidence=?, version=?, updated_at=CURRENT_TIMESTAMP
                    WHERE session_id=? AND key=?
                """,
                    (
                        value,
                        category,
                        confidence,
                        old_version + 1,
                        str(session_id),
                        key,
                    ),
                )
        else:
            # Insert new entry
            await db.execute(
                """
                INSERT INTO semantic_memory (id, session_id, key, value, category, confidence, version)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
                (str(uuid4()), str(session_id), key, value, category, confidence),
            )

        await db.commit()


async def get_semantic(session_id: UUID, key: str) -> Optional[Dict[str, Any]]:
    """
    Return the latest version of an entry for a given key, or None if not found.
    """
    async with aiosqlite.connect(SQL_DB_PATH) as db:
        async with db.execute(
            """
            SELECT key, value, category, confidence, version, updated_at
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
            "category": row[2],
            "confidence": row[3],
            "version": row[4],
            "updated_at": row[5],
        }
    return None


async def get_all_semantic(
    session_id: UUID, category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Return all latest entries for a session (one per key). Optionally filter by category.
    """
    async with aiosqlite.connect(SQL_DB_PATH) as db:
        # Build query with optional category filter
        query = """
            SELECT sm.key, sm.value, sm.category, sm.confidence, sm.version, sm.updated_at
            FROM semantic_memory sm
            INNER JOIN (
                SELECT key, MAX(version) as max_version
                FROM semantic_memory
                WHERE session_id = ?
            """
        params = [str(session_id)]
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " GROUP BY key) latest ON sm.key = latest.key AND sm.version = latest.max_version"
        if category:
            query += " WHERE sm.category = ?"
            params.append(category)
        query += " AND sm.session_id = ?"
        params.append(str(session_id))

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

    entries = []
    for row in rows:
        entries.append(
            {
                "key": row[0],
                "value": row[1],
                "category": row[2],
                "confidence": row[3],
                "version": row[4],
                "updated_at": row[5],
            }
        )
    return entries


async def delete_semantic(session_id: UUID, key: str):
    """Remove all versions of an entry for a session."""
    async with aiosqlite.connect(SQL_DB_PATH) as db:
        await db.execute(
            "DELETE FROM semantic_memory WHERE session_id=? AND key=?",
            (str(session_id), key),
        )
        await db.commit()
