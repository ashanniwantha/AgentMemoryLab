from uuid import UUID
from src.agents.base import BaseAgent


class ReflectionAgent(BaseAgent):
    def __init__(self, session_id: UUID):
        super().__init__(
            role="reflector",
            personality="You are an insightful analyst who synthesizes information into high‑level summaries",
            session_id=session_id,
        )

    async def reflect(self) -> str:
        await self.memory_service.init()

        # Use the cached user facts (these are only user_fact category)
        facts = self.memory_service.user_facts
        if not facts:
            return "No user facts to analyze"

        prompt = f"""Based on the following facts about the user, generate a concise summary 
        touching on topics such as user's interests, preferences, potential goals and more.
        Highlight any patterns or significant details.

        Facts:
        {', '.join(f'{k}: {v}' for k, v in facts.items())}

        Insights:
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        insights = response.choices[0].message.content
        if insights is None:
            insights = ""

        # Store insights with category 'insight'
        await self.memory_service.store_entry(
            "reflection_insights", insights, category="insight"
        )
        return insights
