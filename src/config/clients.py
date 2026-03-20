from openai import OpenAI
from src.config import settings


def get_openai_client():
    """Return an OpenAI client configured for the current provider"""
    return OpenAI(api_key="ollama", base_url=settings.OLLAMA_BASE_URL)
