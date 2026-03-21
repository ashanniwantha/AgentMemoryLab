from uuid import UUID

from src.agents.base import BaseAgent


class ReflectionAgent(BaseAgent):
    def __init__(self, session_id: UUID):
        super().__init__(
            role="reflector",
            personality="You are an insightful anlyst who synthesizes infomation into high level summaries",
            session_id=session_id,
        )

    async def reflect(self) -> str:
        """Analyse all stored facts anbd generate insights"""
        await self.memory_service.init()
        # Get all facts
        facts = self.memory_service.facts
        if not facts:
            return "No facts to analyse"

        # Build a prompt that asks for insights
        prompt = f"""Refer to following facts about the user, generate a concise summary of it
        touching on topics such as user's interests, preferences, potention goals and more.
        Highlight any patters or signicats details.
        
        
        Facts;
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

        # Store insights as a fact
        await self.memory_service.set_fact("reflection_insights", insights)
        return insights
