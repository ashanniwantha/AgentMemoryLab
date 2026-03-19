from src.agent.supervisor import Supervisor


def main():
    print("---Welcome to the Agent Memory Lab!\n")

    # Loop for user to interact with the system via prompts
    while True:
        # prompt input
        prompt = input("You > ")

        if prompt == "quit":
            print("\n---Goodbye!---")
            break

        supervisor = Supervisor()
        supervisor.ask(prompt)


if __name__ == "__main__":
    main()
