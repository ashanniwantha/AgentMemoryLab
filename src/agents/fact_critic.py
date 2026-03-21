from uuid import UUID
from src.agents.base import BaseAgent


class FactCriticAgent(BaseAgent):
    def __init__(self, session_id: UUID):
        super().__init__(
            role="fact_critic",
            personality="You're a strict critic focused on factual accuracy, logical consistency, and plot coherence",
            session_id=session_id,
        )

    async def critique(self) -> str:
        await self.memory_service.init()

        draft = await self.memory_service.load_entry("draft", category="draft")
        if not draft:
            return "No draft available to critique"

        prompt = f"""Review the following draft and provide constructive criticisms 
        about its logical and plot consistency, factual accuracy etc. 
        
        Draft:
        {draft}
        
        Factual feedback:"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        feedback = response.choices[0].message.content
        if feedback is None:
            feedback = ""

        await self.memory_service.store_entry(
            "fact_feedback", feedback, category="feedback"
        )
        return feedback
