from litellm import token_counter
from src.config import settings


def get_message_tokens(messages: list) -> int:
    """
    Automatically detects the correct tokenizer for the active model
    and returns the count.
    """
    return token_counter(model=settings.OLLAMA_MODEL_NAME, messages=messages)
