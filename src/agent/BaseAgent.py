import os
from typing import List
from dotenv import load_dotenv

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

load_dotenv()


class BaseAgent:
    def __init__(self, role: str, personality: str) -> None:
        self.client = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        # Defaulting to a known stable model if the env var is missing
        self.model = os.getenv("MODEL_NAME", "gemini-2.5-flash")
        self.role = role
        self.personality = personality
        # This will hold our conversation state
        self.messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.personality}
        ]
