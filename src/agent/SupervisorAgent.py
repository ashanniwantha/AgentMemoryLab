from dotenv import load_dotenv
from src.agent import BaseAgent

load_dotenv()


class SupervisorAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            role="supervisor",
            personality="You are the lead orchestrator. Be concise and professional.",
        )

    def ask(self, prompt: str) -> None:
        # 1. Add User message to memory
        self.messages.append({"role": "user", "content": prompt})

        # 2. Trigger the stream
        response = self.client.chat.completions.create(
            model=self.model, messages=self.messages, stream=True
        )

        print(f"\n{self.role.upper()} > ", end="", flush=True)
        full_response = ""

        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
                full_response += content

        # 3. Add Assistant response to memory so it "remembers"
        self.messages.append({"role": "assistant", "content": full_response})
        print()


if __name__ == "__main__":
    supervisor = SupervisorAgent()

    supervisor.ask("Who is Eminem?")
