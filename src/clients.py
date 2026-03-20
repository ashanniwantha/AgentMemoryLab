from openai import OpenAI
from src.config import settings

from openai import AsyncOpenAI

# We initalize this to None and set it once
# This lives for the duration of life of the application
_async_openai_client: AsyncOpenAI | None = None


def get_openai_client():
    """Return an OpenAI client configured for the current provider"""
    global _async_openai_client

    if _async_openai_client is None:
        _async_openai_client = AsyncOpenAI(
            api_key="ollama", base_url=settings.OLLAMA_BASE_URL
        )

    return _async_openai_client


async def close_client():
    """Called when the app shutdowns"""
    global _async_openai_client

    if _async_openai_client:
        await _async_openai_client.close()
        _async_openai_client = None
