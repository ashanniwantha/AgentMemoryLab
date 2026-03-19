"""
BaseAgent: Parent Class for all agents
Handles client/model initalization and hold conversation state
"""

# Import all necessary types
from typing import cast, List

# Import the settings configurations
from src.config import settings

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam


class BaseAgent:
    def __init__(self, role: str, personality: str) -> None:
        """
        Intialize an agent with a role and system personality.

        Args:
            role: Short identified role within the system (e.g, "supervisor, "summarizer")
            personality: system prompt that describes the behavior of the agent
        """

        # Defaulting to a known stable model if the env var is missing
        self.role = role
        self.personality = personality

        # Intialize OpenAI SDK client
        self.client = OpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url=settings.GEMINI_BASE_URL,
        )

        # Initialize the model
        self.model = settings.GEMINI_MODEL_NAME

        # Conversation history: strat with system message
        # This will hold our conversation state
        self.messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.personality}
        ]

    def add_message(self, role: str, content: str):
        """Add a message to the conversation state"""
        self.messages.append(
            cast(ChatCompletionMessageParam, {"role": role, "content": content})
        )

    def stream_response(self, user_input: str) -> str:
        """
        Send user input to the LLM and stream it back to the user
        The response will be added to the conversation state after streaming is finished

        Returns:
            The full response text.
        """
        # Add the user message to the conversation state
        self.add_message("user", user_input)

        # Get streaming response from LLM
        response = self.client.chat.completions.create(
            model=self.model, messages=self.messages, stream=True
        )

        print(f"\n{self.role.upper()}> ", end="", flush=True)
        full_response = ""

        for chunk in response:
            content = chunk.choices[0].delta.content

            if content:
                print(content, end="", flush=True)
                full_response += content

        # Add assistant response to the conversation state
        self.add_message("assistant", full_response)
        print()  # newline after response

        return full_response

    def ask(self, prompt: str) -> str:
        """
        Convenience method to get a response (streamed by default).
        Override if non-streaming needed.
        """

        return self.stream_response(prompt)
