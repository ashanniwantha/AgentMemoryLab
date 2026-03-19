from uuid import UUID

from src.agents.base import BaseAgent


class Summarizer(BaseAgent):
    def __init__(self) -> None:
        super().__init__(role="summarizer", personality="You're an summarizing agent")
