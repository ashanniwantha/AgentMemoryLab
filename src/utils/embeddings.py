from typing import List

from src.config import settings
from src.clients import get_openai_client


async def get_embeddings(text: str) -> List[float]:
    """Get embedding from Ollama using the dedicated embedding model."""
    # Get the shared client
    client = get_openai_client()

    # Use the client
    response = await client.embeddings.create(
        model=settings.OLLAMA_EMBEDDING_MODEL, input=text
    )
    return response.data[0].embedding
