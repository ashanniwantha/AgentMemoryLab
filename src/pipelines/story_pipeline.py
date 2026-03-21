import logging
import asyncio
from uuid import UUID

from src.agents.drafter import DraftAgent
from src.agents.style_critic import StyleCriticAgent
from src.agents.fact_critic import FactCriticAgent
from src.agents.consolidator import ConsolidatorAgent

logger = logging.getLogger(__name__)


async def run_story_pipeline(session_id: UUID, topic: str) -> str:
    """
    Execute the complete story generation pipeline:
    1. Generate draft
    2. Run style and fact critics concurrently
    3. Consolidate feedback into final story
    Returns the final story string.
    """
    logger.info(f"Starting story pipeline for topic: {topic}")

    # 1. Generate draft
    draft_agent = DraftAgent(session_id)
    logger.info("Generating draft...")
    await draft_agent.generate_draft(topic)
    logger.info("Draft generated.")

    # 2. Run critics concurrently
    style_critic = StyleCriticAgent(session_id)
    fact_critic = FactCriticAgent(session_id)
    logger.info("Starting style and fact critics concurrently...")
    style_task = asyncio.create_task(style_critic.critique())
    fact_task = asyncio.create_task(fact_critic.critique())
    await asyncio.gather(style_task, fact_task)
    logger.info("Both critics finished.")

    # 3. Consolidate
    consolidator = ConsolidatorAgent(session_id)
    logger.info("Consolidating feedback...")
    final_story = await consolidator.consolidate()
    logger.info("Final story generated.")

    return final_story
