from uuid import UUID

from src.agents.base import BaseAgent


class PlannerAgent(BaseAgent):
    def __init__(self, session_id: UUID):
        super().__init__(
            role="planner", personality="You are an professional learning planner"
        )
