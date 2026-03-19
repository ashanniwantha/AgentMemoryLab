"""
BaseAgent: Parent Class for all agents
Handles client/model initalization and hold conversation state
"""

# Import all necessary types
from typing import cast, List, Optional
from uuid import uuid4, UUID

# OpenAI SDK related
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

# Import the settings configurations
from src.config import settings

# Import memory
from src.memory import episodic, summarizer, semantic


class BaseAgent:
    def __init__(
        self, role: str, personality: str, session_id: Optional[UUID] = None
    ) -> None:
        """
        Intialize an agent with a role and system personality.

        Args:
            role: Short identified role within the system (e.g, "supervisor, "summarizer")
            personality: system prompt that describes the behavior of the agent
        """
        self.role = role
        self.personality = personality

        # Conversation history: strat with system message
        # This will hold our conversation state
        self.messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.personality}
        ]

        # Intialize OpenAI SDK client
        self.client = OpenAI(
            api_key="ollama",
            base_url=settings.OLLAMA_BASE_URL,
        )

        # Initialize the model
        self.model = settings.OLLAMA_MODEL_NAME

        # Initialize the databases, create table if needed
        episodic.init_db()
        summarizer.init_summary_table()
        semantic.init_semantic_table()

        # Store facts in a dictionary
        self.facts = {}

        # Use existing or generate a unique session ID for this conversation
        if session_id:
            self.session_id = session_id
            # Load past messages from the database
            past_messages = episodic.get_recent_messages(self.session_id, limit=10)

            for role, content in past_messages:
                self.add_message(role, content)

            # Load the latest summary for the session
            self.summary = summarizer.get_latest_summary(self.session_id)

            # Load existing facts if any
            facts_list = semantic.get_all_facts(self.session_id)
            for fact in facts_list:
                self.facts[fact["key"]] = fact["value"]

        else:
            self.session_id = uuid4()
            self.summary = None

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
        # Add the user message to the conversation state and the database
        self.add_message("user", user_input)
        episodic.save_message(
            session_id=self.session_id, role="user", content=user_input
        )

        extracted_facts = self._extract_facts(user_input)
        for key, value, confidence in extracted_facts:
            semantic.save_fact(
                session_id=self.session_id, key=key, value=value, confidence=confidence
            )
            self.facts[key] = value

        # Check if we need to summarize
        self._maybe_summarize(keep_last=10, threshold=20)

        # Get streaming response from LLM
        response = self.client.chat.completions.create(
            model=self.model, messages=self._build_context_messages(), stream=True
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

        episodic.save_message(
            session_id=self.session_id, role="assistant", content=full_response
        )

        # Check if we need to summarize
        self._maybe_summarize(keep_last=10, threshold=20)

        return full_response

    def ask(self, prompt: str) -> str:
        """
        Convenience method to get a response (streamed by default).
        Override if non-streaming needed.
        """

        return self.stream_response(prompt)

    def _build_context_messages(self) -> List[ChatCompletionMessageParam]:
        """Build the message list for the LLM, including the summary if available"""
        context = []

        # Start adding the system message
        context.append(self.messages[0])

        if self.summary:
            # Add the summary to the context if available (better to add with a system prompt)
            context.append(
                {
                    "role": "system",
                    "content": f"Previous conversation summary: {self.summary}",
                }
            )

        if self.facts:
            # Add the facts to the context if available (better to add with a system prompt)
            facts_str = ", ".join(f"{k}: {v}" for k, v in self.facts.items())
            context.append({"role": "system", "content": f"User facts: {facts_str}"})

        context.extend(self.messages[1:])  # Recent messages
        return context

    def _maybe_summarize(self, keep_last: int = 10, threshold: int = 20):
        """
        Trigger summarization if total messages (excluding system) exceed threshold
        """

        # Cound only user/assistant messages (skip system)
        if len(self.messages) - 1 > threshold:
            self._summarize_older_messages(keep_last)

    def _summarize_older_messages(self, keep_last: int = 10):
        """
        Summarise messages older than the least keep_last,
        The summary is saved and older messages are removed from self.messages.
        """
        # Separate system message from the conversation
        system_msg = self.messages[0]
        conversation = self.messages[1:]

        if len(conversation) <= keep_last:
            return  # not enaugh to summarize

        # Split
        older_msgs = conversation[:-keep_last]
        recent_msgs = conversation[-keep_last:]

        # Format older messages for summarizations
        text_to_summarize = "\n".join(
            f"{msg['role']}: {msg.get('content')}" for msg in older_msgs
        )

        # Prompt for the summarization
        summary_prompt = f"""
            Summarize the following conversation concisely, capturing key points such as facts, user preferences and others.\n
            Focus on infomations which would be useful for continuing the conversation\n
            Text to summarize:
            {text_to_summarize}
        """

        # Call the LLM to generate the summary
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": summary_prompt}],
            model=self.model,
            temperature=0.2,
        )
        summary = response.choices[0].message.content

        if summary is None:
            summary = ""

        # Save the summary to database
        summarizer.save_summary(
            session_id=self.session_id, summary=summary, message_count=len(older_msgs)
        )

    def _extract_facts(self, user_input: str) -> List[tuple[str, str, float]]:
        """
        Use LLM to extract factual infomation from user message.
        Return list of (key, value, confidence) tuples.
        """
        prompt = f"""Extract factual information about the user from this message. 
        Return each fact as a line in the format "key: value". Only include facts that are stated or clearly implied. Use lowercase keys with underscores.

        Examples:
        Message: "My name is John and I love Python"
        Facts:
        name: john
        likes_python: true

        Message: "I'm from New York and I hate JavaScript"
        Facts:
        location: new york
        likes_javascript: false

        Message: "{user_input}"
        Facts:
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200,
        )
        content = response.choices[0].message.content
        if not content:
            return []

        facts = []
        for line in content.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                # Simple confidence: 1.0 for now (could be inferred from tone later)
                facts.append((key, value, 1.0))

        return facts
