"""
BaseAgent: Parent Class for all agents
Handles client/model initialization and holds conversation state
"""

from typing import cast, List, Optional
from uuid import uuid4, UUID

from litellm import acompletion

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from src.clients import get_openai_client
from src.config import settings
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
            # We'll load them asynchronously later, so we need to set a flag
            self._past_loaded = False
        else:
            self._past_loaded = True

        # Initialize OpenAI client (for LLM calls)
        self.client = get_openai_client()
        self.model = settings.OLLAMA_MODEL_NAME

    async def _load_past_messages(self):
        """Load past messages from DB into self.messages"""
        past_messages = await episodic.get_recent_messages(self.session_id, limit=10)
        for role, content in past_messages:
            self.add_message(role, content)

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

    async def stream_response(self, user_input: str) -> str:
        # Ensure service is initialized
        await self.memory_service.init()

        # Load past messages if not done
        if not self._past_loaded:
            await self._load_past_messages()
            self._past_loaded = True

        # 1. Add user message to local history
        self.add_message("user", user_input)

        # 2. Get context from memory service (summary, facts, retrieved messages)
        service_context = await self.memory_service.get_context(user_input)

        # 3. Store user message in all memory systems
        await self.memory_service.store_user_message(user_input)

        # 4. Check if summarization is needed
        summaried = await self.memory_service.maybe_summarize(
            self.messages,
            keep_last=10,
            token_threshold=settings.SUMMARIZATION_TOKEN_THRESHOLD,
        )

        if summaried is not None:
            self.messages = summaried

        # 5. Build full prompt
        prompt = self._build_prompt(service_context)

        # 6. Stream the response
        response = await acompletion(model=self.model, messages=prompt, stream=True)

        print(f"\n{self.role.upper()}> ", end="", flush=True)
        full_response = ""

        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
                full_response += content

        # 7. Add assistant response to conversation history
        self.add_message("assistant", full_response)
        print()

        # 8. Store assistant message in memory systems
        await self.memory_service.store_assistant_message(full_response)

        # 9. Check summarization again (optional)
        summaried = await self.memory_service.maybe_summarize(
            self.messages,
            keep_last=10,
            token_threshold=settings.SUMMARIZATION_TOKEN_THRESHOLD,
        )

        if summaried is not None:
            self.messages = summaried

        return full_response

    async def ask(self, prompt: str) -> str:
        return await self.stream_response(prompt)
