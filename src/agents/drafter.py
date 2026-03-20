from uuid import UUID
from src.agents.base import BaseAgent


class DraftAgent(BaseAgent):
    def __init__(self, session_id: UUID):
        super().__init__(
            role="drafter",
            personality="You're a creative writer. Write engaging, imaginative drafts",
            session_id=session_id,
        )

    async def generate_draft(self, topic: str) -> str:
        """
        Generate a draft for a given topic using LLM and store it in semantic memory.
        """
        prompt = f"Write a medium‑length, creative story based on the following topic:\n{topic}"

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # higher temperature = more creativity
        )

        content = response.choices[0].message.content
        if content is None:
            # If the LLM returns no content, we still need to return a string.
            # You could raise an exception, but for now we'll use an empty string.
            draft = ""
        else:
            draft = content

        # Store the draft in semantic memory
        await self.memory_service.set_fact("draft", draft, confidence=1.0)
        return draft
