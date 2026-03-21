import asyncio
from uuid import uuid4

from src.agents.drafter import DraftAgent
from src.agents.style_critic import StyleCriticAgent
from src.agents.fact_critic import FactCriticAgent
from src.agents.consolidator import ConsolidatorAgent


async def main():
    # Create a new session
    session_id = uuid4()
    print(f"Using session ID: {session_id}")

    draft_agent = DraftAgent(session_id)
    # Genarate draft
    print("\n--- Generating draft...---")
    draft = await draft_agent.generate_draft("How did Micheal Jackson die?")
    print(f"Draft generated:\n{draft}.\n Saved in memory!")

    style_critic = StyleCriticAgent(session_id)
    fact_critic = FactCriticAgent(session_id)

    # Run critics concurrently
    print("\n--- Runnign critics concurrently... ---")
    style_task = asyncio.create_task(style_critic.critique())
    fact_task = asyncio.create_task(fact_critic.critique())
    await asyncio.gather(style_task, fact_task)
    print("Both critics are finished!")

    # Consolidate
    consolidator = ConsolidatorAgent(session_id)
    print("\n--- Consolidating feedback ---")
    final_story = await consolidator.consolidate()

    print("\n--- Final Story ---")
    print(final_story)


if __name__ == "__main__":
    asyncio.run(main())
