"""
BaseAgent: Parent Class for all agents
Handles client/model initialization and holds conversation state
"""

from typing import cast, List, Optional
from uuid import uuid4, UUID

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from src.config import settings, clients
from src.memory import episodic, summarizer, service  # service for MemoryService


class BaseAgent:
    def __init__(
        self, role: str, personality: str, session_id: Optional[UUID] = None
    ) -> None:
        self.role = role
        self.personality = personality

        # Determine session ID
        self.session_id = session_id if session_id else uuid4()

        # Create memory service (loads facts, summary, etc.)
        self.memory_service = service.MemoryService(self.session_id)

        # Conversation history: start with system message
        self.messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.personality}
        ]

        # If resuming, load past messages from episodic DB into self.messages
        if session_id:
            past_messages = episodic.get_recent_messages(self.session_id, limit=10)
            for role, content in past_messages:
                self.add_message(role, content)

        # Initialize OpenAI client (for LLM calls)
        self.client = clients.get_openai_client()
        self.model = settings.OLLAMA_MODEL_NAME

    def add_message(self, role: str, content: str):
        self.messages.append(
            cast(ChatCompletionMessageParam, {"role": role, "content": content})
        )

    def _build_prompt(
        self, service_context: List[ChatCompletionMessageParam]
    ) -> List[ChatCompletionMessageParam]:
        prompt = []
        prompt.append(self.messages[0])  # system personality
        prompt.extend(service_context)  # summary, facts, relevant messages
        prompt.extend(self.messages[1:])  # conversation history
        return prompt

    def stream_response(self, user_input: str) -> str:
        # 1. Add user message to conversation history
        self.add_message("user", user_input)

        # 2. Get context from memory service (summary, facts, retrieved messages)
        service_context = self.memory_service.get_context(user_input)

        # 3. Store user message in all memory systems
        self.memory_service.store_user_message(user_input)

        # 4. Check if summarization is needed
        self._maybe_summarize(keep_last=10, threshold=20)

        # 5. Build full prompt
        prompt = self._build_prompt(service_context)

        # 6. Get streaming response
        response = self.client.chat.completions.create(
            model=self.model, messages=prompt, stream=True
        )

        print(f"\n{self.role.upper()}> ", end="", flush=True)
        full_response = ""

        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
                full_response += content

        # 7. Add assistant response to conversation history
        self.add_message("assistant", full_response)
        print()

        # 8. Store assistant message in memory systems
        self.memory_service.store_assistant_message(full_response)

        # 9. Check summarization again (optional)
        self._maybe_summarize(keep_last=10, threshold=20)

        return full_response

    def ask(self, prompt: str) -> str:
        return self.stream_response(prompt)

    def _maybe_summarize(self, keep_last: int = 10, threshold: int = 20):
        if len(self.messages) - 1 > threshold:
            self._summarize_older_messages(keep_last)

    def _summarize_older_messages(self, keep_last: int = 10):
        system_msg = self.messages[0]
        conversation = self.messages[1:]

        if len(conversation) <= keep_last:
            return

        older_msgs = conversation[:-keep_last]
        recent_msgs = conversation[-keep_last:]

        text_to_summarize = "\n".join(
            f"{msg['role']}: {msg.get('content')}" for msg in older_msgs
        )

        summary_prompt = f"""
            Summarize the following conversation concisely, capturing key points such as facts, user preferences and others.
            Focus on information which would be useful for continuing the conversation.

            Text to summarize:
            {text_to_summarize}
        """

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": summary_prompt}],
            model=self.model,
            temperature=0.2,
        )
        summary = response.choices[0].message.content
        if summary is None:
            summary = ""

        summarizer.save_summary(
            session_id=self.session_id, summary=summary, message_count=len(older_msgs)
        )

        # Optionally update the service's summary cache? The service reloads from DB on next get_context, so not needed.
        self.messages = [system_msg] + recent_msgs
