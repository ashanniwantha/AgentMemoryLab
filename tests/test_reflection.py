import asyncio
from uuid import UUID
from src.agents.reflection import ReflectionAgent


async def main():
    # Use an existing session ID where facts exist (e.g., the one from your test)
    session_id = UUID("41a5bbae-e5b9-4c2b-933e-159d8939ef83")
    reflector = ReflectionAgent(session_id)
    insights = await reflector.reflect()
    print("\n--- Reflection Insights ---")
    print(insights)


if __name__ == "__main__":
    asyncio.run(main())
