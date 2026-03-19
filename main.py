from src.agent.supervisor import Supervisor


def main():
    print("\n---Welcome to the Agent Memory Lab!---")

    supervisor = Supervisor()

    # Loop for user to interact with the system via prompts
    while True:
        # prompt input
        prompt = input("\nYou > ")

        if prompt == "quit":
            print("\n---Goodbye!---")
            break

        supervisor.stream_response(prompt)


if __name__ == "__main__":
    main()
