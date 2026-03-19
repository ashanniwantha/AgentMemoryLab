from src.agents import BaseAgent


class Supervisor(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            role="supervisor",
            personality="You are the lead orchestrator. Be concise and professional.",
        )


if __name__ == "__main__":
    supervisor = Supervisor()

    supervisor.ask("Explain to what is a MCP server?")
