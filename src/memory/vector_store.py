"""
Vector memory: stores message embeddings for semantic search using ChromaDB.
"""

import asyncio
import chromadb
from chromadb.config import Settings
from uuid import UUID
from typing import List, Dict, Any

from src.config import settings as app_settings

# Initialize ChromaDB client (persistent storage)
client = chromadb.PersistentClient(path=app_settings.VECTOR_DB)


# Collection name for this session (we'll use session_id as part of the collection name)
# For simplicity, we'll use a single collection per session or per user.
# We'll create a collection per session: "session_<session_id>"
def _get_collection_sync(session_id: UUID):
    """Synchronous helper to get or create a collection."""
    collection_name = f"session_{session_id}"
    try:
        # Try to get existing collection
        return client.get_collection(collection_name)
    except:
        # Create new collection
        return client.create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}  # cosine similarity
        )


async def get_collection(session_id: UUID):
    """Async wrapper to get or create a collection"""
    return await asyncio.to_thread(_get_collection_sync, session_id)


async def add_message_embedding(
    session_id: UUID,
    message_id: str,  # UUID from episodic DB
    role: str,
    content: str,
    embedding: List[float],
):
    """Store a message embedding in the vector DB."""

    def _add():
        collection = _get_collection_sync(session_id)
        collection.add(
            ids=[message_id],
            embeddings=[embedding],
            metadatas=[{"role": role, "content": content}],
        )

    await asyncio.to_thread(_add)


async def query_similar_messages(
    session_id: UUID, query_embedding: List[float], n_results: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve most similar messages to the query embedding."""

    def _query():
        collection = _get_collection_sync(session_id)
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "distances"],
            )
        except Exception:
            return []

        messages = []
        # Safely extract results
        ids = results.get("ids")
        if ids and ids[0]:
            distances = results.get("distances", [None])[0] or []
            metadatas = results.get("metadatas", [None])[0] or []
            for i in range(len(ids[0])):
                messages.append(
                    {
                        "id": ids[0][i],
                        "distance": distances[i] if i < len(distances) else 0.0,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                    }
                )
        return messages

    return await asyncio.to_thread(_query)
