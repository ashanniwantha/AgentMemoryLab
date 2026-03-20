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
        """Generate style feedback on the current draft."""
        await self.memory_service.init()

        # Retrieve draft from the memory
        draft = await self.memory_service.load_one_fact("draft")
        if not draft:
            return "No draft available to critique"

        prompt = f"""Review the following story draft's elements such as style, narrative flow, 
        attention to details, audience retention, and readability.
        Provide constructive criticisms and feedbacks in a concise form, focusing on how to improve the overall story:
        
        Story:
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

        # Store feedback in memory
        await self.memory_service.set_fact("style_feedback", feedback)
        return feedback
