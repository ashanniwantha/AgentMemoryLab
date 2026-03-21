# Import types necessary
from typing import Optional
from uuid import UUID

from src.agents import BaseAgent


class Supervisor(BaseAgent):
    def __init__(self, session_id: Optional[UUID] = None) -> None:
        super().__init__(
            role="supervisor",
            personality="""
            You are the lead orchestrator. Your task is to handle user requests efficiently.

            - If the user asks for a story, creative narrative, or something that requires a long, structured, or imaginative response, respond with exactly this format:
            [STORY] topic: <extracted topic>
            Replace <extracted topic> with a brief summary of what the user wants a story about.

            - For all other queries, answer concisely and professionally.
            """,
            session_id=session_id,
        )
