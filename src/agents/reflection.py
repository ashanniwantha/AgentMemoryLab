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

        # Get all entries except those in 'insight' category (to avoid self‑reference)
        all_entries = await self.memory_service.get_all_entries(
            exclude_categories=["insight"]
        )
        if not all_entries:
            return "No entries to analyze."

        # Format entries for the prompt
        entries_text = ""
        for entry in all_entries:
            entries_text += f"[{entry['category']}] {entry['key']}: {entry['value']}\n"

        prompt = f"""
        You are a meta‑cognitive analyst. Review the following collection of memories, including user facts, story drafts, feedback, final stories, and other notes.
        Generate a concise summary that captures:
        - The user's interests and patterns
        - The quality or progression of any creative work (like stories)
        - Any notable contradictions or improvements
        - Suggestions for further exploration or next steps

        Memories:
        {entries_text}

        Insights:
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        insights = response.choices[0].message.content or ""

        # Store insights with category 'insight'
        await self.memory_service.store_entry(
            "reflection_insights", insights, category="insight"
        )
        return insights
