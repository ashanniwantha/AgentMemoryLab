# Import types necessary
from typing import Optional
from uuid import UUID

from src.agents import BaseAgent


class Supervisor(BaseAgent):
    def __init__(self, session_id: Optional[UUID] = None) -> None:
        super().__init__(
            role="supervisor",
            personality="You are the lead orchestrator. Be concise and professional.",
            session_id=session_id,
        )


if __name__ == "__main__":
    supervisor = Supervisor()

    supervisor.ask("Explain to what is a MCP server?")
