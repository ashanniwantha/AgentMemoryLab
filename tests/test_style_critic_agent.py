import asyncio
from uuid import UUID
from src.agents.style_critic import StyleCriticAgent
from src.agents.fact_critic import FactCriticAgent


async def main():
    # Use the session ID from the draft you stored earlier
    # You can find it from the DB or from the output when you ran the draft test.
    # In your DB output, the session_id was: d8f08bc0-6075-4d74-b703-6b9f801f4d76
    session_id = UUID("d8f08bc0-6075-4d74-b703-6b9f801f4d76")
    style_crtic = StyleCriticAgent(session_id)
    fact_critic = FactCriticAgent(session_id)

    style_task = asyncio.create_task(style_crtic.critique())
    fact_task = asyncio.create_task(fact_critic.critique())

    style_feedback, fact_feedback = await asyncio.gather(style_task, fact_task)

    print("\n--- Style Feedback ---")
    print(style_feedback)
    print("\n--- Fact Feedback ---")
    print(fact_feedback)


if __name__ == "__main__":
    asyncio.run(main())
