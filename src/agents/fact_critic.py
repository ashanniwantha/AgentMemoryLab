from uuid import UUID

from src.agents.base import BaseAgent


class FactCriticAgent(BaseAgent):
    def __init__(self, session_id: UUID):
        super().__init__(
            role="fact_critic",
            personality="You're a strict critic focused on factual accuracy, logical consistency, and plot coherence",
            session_id=session_id,
        )
