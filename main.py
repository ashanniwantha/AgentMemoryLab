from src.agents.supervisor import Supervisor
from uuid import UUID


def main():
    print("\n---Welcome to the Agent Memory Lab!---")

    # Ask if resuming a session
    resume = input("Do you want to resume a previous session? (y/n): ").strip().lower()
    session_id = None
    if resume == "y":
        session_str = input("Enter the session ID (UUID): ").strip()
        try:
            session_id = UUID(session_str)
            print(f"Resuming session {session_id}")
        except ValueError:
            print("Invalid UUID. Starting a new session.")
            session_id = None

    supervisor = Supervisor(session_id=session_id)

    while True:
        prompt = input("\nYou > ")
        if prompt.lower() == "quit":
            print("\n---Goodbye!---")
            break
        supervisor.stream_response(prompt)


if __name__ == "__main__":
    main()
