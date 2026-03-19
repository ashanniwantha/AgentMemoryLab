"""
Semantic memory: stores structured facts about the user.
"""

import sqlite3
from typing import Optional, Dict, Any, List
from uuid import uuid4, UUID

from src.config.settings import SQL_DB_PATH


def init_semantic_table():
    """Create a semantic_memory table if it doesn't exist."""
    conn = sqlite3.connect(SQL_DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
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
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_semantic_session_key
        ON semantic_memory (session_id, key)
    """
    )

    conn.commit()
    conn.close()


def save_fact(session_id: UUID, key: str, value: str, confidence: float = 1.0):
    """
    Insert or update a fact for a session.
    If the fact with same key already exists and the value is different,
    we update it (increment version, set new value/confidence).
    """
    conn = sqlite3.connect(SQL_DB_PATH)
    cursor = conn.cursor()

    # Check if the fact already exists
    cursor.execute(
        "SELECT value, version FROM semantic_memory WHERE session_id=? AND key=?",
        (str(session_id), key),
    )
    row = cursor.fetchone()

    if row:
        old_value, old_version = row
        if old_value != value:
            # Update with the new value and increment version
            cursor.execute(
                """
                UPDATE semantic_memory
                SET value=?, confidence=?, version=?, updated_at=CURRENT_TIMESTAMP
                WHERE session_id=? AND key=?
            """,
                (value, confidence, old_version + 1, str(session_id), key),
            )
    else:
        # Insert new fact
        cursor.execute(
            """
            INSERT INTO semantic_memory (id, session_id, key, value, confidence, version)
            VALUES (?, ?, ?, ?, ?, 1)
        """,
            (str(uuid4()), str(session_id), key, value, confidence),
        )

    conn.commit()
    conn.close()


def get_fact(session_id: UUID, key: str) -> Optional[Dict[str, Any]]:
    """
    Return the latest fact for a given key, or None if not found.
    """
    conn = sqlite3.connect(SQL_DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT key, value, confidence, version, updated_at
        FROM semantic_memory
        WHERE session_id=? AND key=?
        ORDER BY version DESC
        LIMIT 1
    """,
        (str(session_id), key),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "key": row[0],
            "value": row[1],
            "confidence": row[2],
            "version": row[3],
            "updated_at": row[4],
        }
    return None


def get_all_facts(session_id: UUID) -> List[Dict[str, Any]]:
    """
    Return all facts for a session (one per key).
    """
    conn = sqlite3.connect(SQL_DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
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
    )
    rows = cursor.fetchall()
    conn.close()

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


def delete_fact(session_id: UUID, key: str):
    """Remove all versions of a fact for a session."""
    conn = sqlite3.connect(SQL_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM semantic_memory WHERE session_id=? AND key=?",
        (str(session_id), key),
    )
    conn.commit()
    conn.close()
