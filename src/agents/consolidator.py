from uuid import UUID
from src.agents.base import BaseAgent


class ConsolidatorAgent(BaseAgent):
    def __init__(self, session_id: UUID):
        super().__init__(
            role="consolidator",
            personality="You're master editor who synthesizes feedback into a polished final output",
            session_id=session_id,
        )

    async def consolidate(self) -> str:
        await self.memory_service.init()

        draft = await self.memory_service.load_entry("draft", category="draft")
        if not draft:
            return "No draft available to reconstruct!"

        # Load feedbacks (category 'feedback')
        style_feedback = await self.memory_service.load_entry(
            "style_feedback", category="feedback"
        )
        fact_feedback = await self.memory_service.load_entry(
            "fact_feedback", category="feedback"
        )

        prompt = f"""
        Take the following draft and both style and factual feedbacks provided.
        Your task is to produce a final, improved, engaging, cohesive version of the draft
        taking both style and factual feedbacks into account
        while preserving the original drafts strengths and points.
        
        Original Draft:
        {draft}
        
        Style Feedback:
        {style_feedback}
        
        Factual Feedback:
        {fact_feedback}
        
        Final Story: 
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        final_story = response.choices[0].message.content
        if final_story is None:
            final_story = ""

        # Store final story with category 'final'
        await self.memory_service.store_entry(
            "final_draft", final_story, category="final"
        )
        return final_story
