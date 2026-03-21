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
        await self.memory_service.init()

        prompt = f"Write a medium‑length, creative story based on the following topic:\n{topic}"

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = response.choices[0].message.content
        draft = content if content is not None else ""

        # Store draft with category 'draft'
        await self.memory_service.store_entry("draft", draft, category="draft")
        return draft
