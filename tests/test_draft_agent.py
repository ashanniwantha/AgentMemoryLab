from uuid import uuid4
from src.agents.drafter import DraftAgent


async def main():
    drafter = DraftAgent(uuid4())

    draft = await drafter.generate_draft("The man who survived against all odds")
    print(draft)
