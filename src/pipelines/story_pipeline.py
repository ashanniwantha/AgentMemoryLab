import asyncio
from uuid import UUID
from src.agents.drafter import DraftAgent
from src.agents.style_critic import StyleCriticAgent
from src.agents.fact_critic import FactCriticAgent
from src.agents.consolidator import ConsolidatorAgent


async def run_story_pipeline(session_id: UUID, topic: str) -> str:
    """
    Execute the complete story generation pipeline:
    1. Generate draft
    2. Run style and fact critics concurrently
    3. Consolidate feedback into final story
    Returns the final story string.
    """
    # 1. Generate draft
    draft_agent = DraftAgent(session_id)
    await draft_agent.generate_draft(topic)

    # 2. Run critics concurrently
    style_critic = StyleCriticAgent(session_id)
    fact_critic = FactCriticAgent(session_id)
    style_task = asyncio.create_task(style_critic.critique())
    fact_task = asyncio.create_task(fact_critic.critique())
    await asyncio.gather(style_task, fact_task)

    # 3. Consolidate
    consolidator = ConsolidatorAgent(session_id)
    final_story = await consolidator.consolidate()
    return final_story
