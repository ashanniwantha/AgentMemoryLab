import asyncio
import logging
import re
import uuid

from src.agents.supervisor import Supervisor
from src.pipelines.story_pipeline import run_story_pipeline
from src.agents.reflection import ReflectionAgent
from src.clients import close_client
from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Global session ID
session_id = None


async def periodic_reflection(session_id: uuid.UUID, interval_minutes: int):
    """Run reflection agent periodically in the background."""
    while True:
        await asyncio.sleep(interval_minutes * 60)
        logger.info("Running periodic reflection...")
        try:
            reflector = ReflectionAgent(session_id)
            insights = await reflector.reflect()
            # Log only first 200 chars to avoid clutter
            logger.info(f"Reflection insights updated: {insights[:200]}...")
        except Exception as e:
            logger.error(f"Periodic reflection failed: {e}")


async def run_immediate_reflection(session_id):
    """Helper to run reflection on demand (used by message‑based trigger or manual command)."""
    reflector = ReflectionAgent(session_id)
    insights = await reflector.reflect()
    logger.info("Manual reflection completed.")
    # Optionally print the full insights (if you want user to see)
    print("\n--- Reflection Insights ---")
    print(insights)


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
        print(f"New session ID: {session_id}")

    supervisor = Supervisor(session_id)

    # Start periodic reflection background task
    reflection_task = asyncio.create_task(
        periodic_reflection(session_id, settings.REFLECTION_INTERVAL_MINUTES)
    )

    message_count = 0

    try:
        while True:
            user_input = input("\nYou > ").strip()
            if user_input.lower() == "/quit":
                break
            elif user_input.lower() == "/reflect":
                # Manual reflection command
                print("Running reflection...")
                await run_immediate_reflection(session_id)
                continue

            message_count += 1

            # Get supervisor's response (streamed)
            supervisor_response = await supervisor.stream_response(user_input)

            # Check if supervisor wants to start a story
            if supervisor_response.startswith("[STORY]"):
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
            # else: normal response already printed by stream_response

            # (Optional) keep message‑based reflection as a fallback
            # If you prefer only periodic, remove this block.
            if message_count % 10 == 0:
                asyncio.create_task(run_immediate_reflection(session_id))

    finally:
        # Cancel background task on exit
        reflection_task.cancel()
        try:
            await reflection_task
        except asyncio.CancelledError:
            pass
        await close_client()
        print("\n--- Goodbye! ---")


if __name__ == "__main__":
    asyncio.run(main())
