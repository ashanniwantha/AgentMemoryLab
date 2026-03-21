from uuid import UUID
from src.agents.base import BaseAgent


class StyleCriticAgent(BaseAgent):
    def __init__(self, session_id: UUID):
        super().__init__(
            role="style_critic",
            personality="You're a literary critic specializing in style, narrative flow, tone",
            session_id=session_id,
        )

    async def critique(self) -> str:
        await self.memory_service.init()

        # Retrieve draft (category 'draft')
        draft = await self.memory_service.load_entry("draft", category="draft")
        if not draft:
            return "No draft available to critique"

        prompt = f"""Review the following draft's elements such as style, narrative flow, 
        attention to details, audience retention, and readability.
        Provide constructive criticisms and feedbacks in a concise form, focusing on how to improve the overall story:
        
        Draft:
        {draft}
        
        Style feedback:"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        feedback = response.choices[0].message.content
        if feedback is None:
            return ""

        # Store feedback with category 'feedback'
        await self.memory_service.store_entry(
            "style_feedback", feedback, category="feedback"
        )
        return feedback
