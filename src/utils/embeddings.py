from typing import List
from uuid import UUID

from openai import embeddings
from src.config import settings, clients


def get_embeddings(text: str) -> List[float]:
    """Get embedding from Ollama using the dedicated embedding model."""
    # Intialize the client
    client = clients.get_openai_client()

    response = client.embeddings.create(
        model=settings.OLLAMA_EMBEDDING_MODEL, input=text
    )
    return response.data[0].embedding
