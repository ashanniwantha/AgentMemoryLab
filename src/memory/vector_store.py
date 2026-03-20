"""
Vector memory: stores message embeddings for semantic search using ChromaDB.
"""

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
def get_collection(session_id: UUID):
    collection_name = f"session_{session_id}"
    try:
        # Try to get existing collection
        return client.get_collection(collection_name)
    except:
        # Create new collection
        return client.create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}  # cosine similarity
        )


def add_message_embedding(
    session_id: UUID,
    message_id: str,  # UUID from episodic DB
    role: str,
    content: str,
    embedding: List[float],
):
    """Store a message embedding in the vector DB."""
    collection = get_collection(session_id)
    collection.add(
        ids=[message_id],
        embeddings=[embedding],
        metadatas=[{"role": role, "content": content}],
    )


def query_similar_messages(
    session_id: UUID, query_embedding: List[float], n_results: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve most similar messages to the query embedding."""
    collection = get_collection(session_id)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["metadatas", "distances"],
    )
    # results is a dict with keys: ids, distances, metadatas
    messages = []
    if results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            messages.append(
                {
                    "id": results["ids"][0][i],
                    "distance": results["distances"][0][i],
                    "metadata": results["metadatas"][0][i],
                }
            )
    return messages
