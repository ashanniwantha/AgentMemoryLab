import asyncio
import re
import uuid
from src.agents.supervisor import Supervisor
from src.pipelines.story_pipeline import run_story_pipeline
from src.agents.reflection import ReflectionAgent
from src.clients import close_client

# Global session ID (user can choose to resume)
session_id = None


async def main():
    global session_id
    print("\n--- Welcome to the Agent Memory Lab ---")
    resume = input("Resume previous session? (y/n): ").strip().lower()
    if resume == "y":
        session_str = input("Session ID: ").strip()
        try:
            session_id = uuid.UUID(session_str)
            print(f"Resuming session {session_id}")
        except ValueError:
            print("Invalid UUID, starting new session.")
            session_id = uuid.uuid4()
    else:
        session_id = uuid.uuid4()

    supervisor = Supervisor(session_id)

    # Track message count for reflection trigger
    message_count = 0

    while True:
        user_input = input("\nYou > ").strip()
        if user_input.lower() == "/quit":
            break

        # Increment message count for every user input
        message_count += 1

        # Get supervisor's response (streamed)
        supervisor_response = await supervisor.stream_response(user_input)

        # Check if supervisor wants to start a story
        if supervisor_response.startswith("[STORY]"):
            # Extract topic
            match = re.search(
                r"\[STORY\] topic:\s*(.+)", supervisor_response, re.IGNORECASE
            )
            if match:
                topic = match.group(1).strip()
                print(f"\n[Supervisor] Starting story pipeline for topic: {topic}")
                final_story = await run_story_pipeline(session_id, topic)
                print("\n--- Final Story ---")
                print(final_story)
            else:
                print("[Supervisor] Could not extract topic. Please try again.")
        else:
            # Normal response already printed by stream_response, nothing extra needed
            pass

        # Trigger background reflection every 10 messages
        if message_count % 10 == 0:
            asyncio.create_task(run_reflection_background(session_id))

    # Cleanup
    await close_client()
    print("\n--- Goodbye! ---")


async def run_reflection_background(session_id):
    """Background task to run reflection agent."""
    reflection_agent = ReflectionAgent(session_id)
    insights = await reflection_agent.reflect()
    print("\n[Background Reflection] Insights updated in memory.")


if __name__ == "__main__":
    asyncio.run(main())
