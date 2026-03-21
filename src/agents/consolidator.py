from uuid import UUID
from src.agents.base import BaseAgent


class ConsolidatorAgent(BaseAgent):
    def __init__(self, session_id: UUID):
        super().__init__(
            role="consolidator",
            personality="You're master editor who synthasizes feedback into a polished final output",
            session_id=session_id,
        )

    async def consolidate(self) -> str:
        """Reconstruct the original draft with style and factual feedbacks into a final story"""
        await self.memory_service.init()

        draft = await self.memory_service.load_one_fact("draft")
        if not draft:
            return "No draft avaiable to reconstruct!"

        # Load all feedbacks from the semantic database
        style_feedback = await self.memory_service.load_one_fact("style_feedback")
        fact_feedback = await self.memory_service.load_one_fact("fact_feedback")

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
            model=self.model, messages=[{"role": "user", "content": prompt}]
        )
        final_story = response.choices[0].message.content
        if final_story is None:
            final_story = ""

        # Store final story in memory
        await self.memory_service.set_fact("final_draft", final_story)
        return final_story
