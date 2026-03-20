import asyncio
from uuid import UUID
from src.agents.style_critic import StyleCriticAgent


async def main():
    # Use the session ID from the draft you stored earlier
    # You can find it from the DB or from the output when you ran the draft test.
    # In your DB output, the session_id was: d8f08bc0-6075-4d74-b703-6b9f801f4d76
    session_id = UUID("d8f08bc0-6075-4d74-b703-6b9f801f4d76")
    critic = StyleCriticAgent(session_id)
    feedback = await critic.critique()
    print("\nStyle Feedback:\n", feedback)


if __name__ == "__main__":
    asyncio.run(main())
