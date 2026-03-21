"""
MemoryService: Centralized memory management for multi‑agent systems.
Handles all memory operations (episodic, semantic, vector, summarization)
and provides a clean API for agents to utilize.
"""

import asyncio
from typing import List, Dict, Optional
from uuid import UUID, uuid4

from openai.types.chat import ChatCompletionMessageParam

from src.clients import get_openai_client
from src.config import settings
from src.memory import episodic, semantic, vector_store, summarizer
from src.utils.embeddings import get_embeddings


class MemoryService:
    def __init__(self, session_id: UUID) -> None:
        self.session_id = session_id
        self.lock = asyncio.Lock()  # for thread‑safe writes
        self.client = get_openai_client()  # async LLM client
        self.model = settings.OLLAMA_MODEL_NAME

        # Cached data
        self.user_facts: Dict[str, str] = {}
        self.summary: Optional[str] = None

        self._initialized = False

    async def init(self):
        """Async initialization: create tables and load cached data."""
        if self._initialized:
            return
        await episodic.init_db()
        await summarizer.init_summary_table()
        await semantic.init_semantic_table()
        await self._load_user_facts()
        await self._load_summary()
        self._initialized = True

    async def _load_user_facts(self):
        """Load all user facts (category='user_fact') into cache."""
        facts_list = await semantic.get_all_semantic(
            self.session_id, category="user_fact"
        )
        for fact in facts_list:
            self.user_facts[fact["key"]] = fact["value"]

    async def _load_summary(self):
        """Load the latest summary for this session."""
        self.summary = await summarizer.get_latest_summary(self.session_id)

    # ---- Public entry methods ----
    async def load_entry(
        self, key: str, category: Optional[str] = None
    ) -> Optional[str]:
        """
        Retrieve the value of a stored entry by key, optionally filtered by category.
        If category is None, returns the latest version (across categories).
        """
        # First, check if it's a user fact and we have it cached
        if category == "user_fact" and key in self.user_facts:
            return self.user_facts[key]
        # Otherwise query the database
        entry = await semantic.get_semantic(self.session_id, key)
        if entry:
            # If a category was given, ensure it matches
            if category is None or entry["category"] == category:
                return entry["value"]
        return None

    async def store_entry(
        self, key: str, value: str, category: str, confidence: float = 1.0
    ) -> None:
        """Store an entry in semantic memory (overwrites if exists)."""
        await semantic.save_semantic(self.session_id, key, value, category, confidence)
        # Update cache if this is a user fact
        if category == "user_fact":
            self.user_facts[key] = value

    # ---- Fact extraction (background) ----
    async def _extract_facts(self, text: str) -> List[tuple[str, str, float]]:
        """
        Use LLM to extract factual information from user message.
        Returns list of (key, value, confidence) tuples.
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

        Message: "{text}"
        Facts:
        """

        response = await self.client.chat.completions.create(
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
                facts.append((key, value, 1.0))
        return facts

    async def _extract_and_save_facts(self, content: str):
        """Background task: extract user facts and store them."""
        extracted = await self._extract_facts(content)
        async with self.lock:
            for key, value, confidence in extracted:
                await semantic.save_semantic(
                    self.session_id,
                    key,
                    value,
                    category="user_fact",
                    confidence=confidence,
                )
                self.user_facts[key] = value

    # ---- Message storage (core memory) ----
    async def store_user_message(self, content: str) -> None:
        """Store a user message (episodic + vector) and trigger background fact extraction."""
        # Episodic
        await episodic.save_message(self.session_id, "user", content)

        # Vector
        embedding = await get_embeddings(content)
        msg_id = str(uuid4())
        await vector_store.add_message_embedding(
            self.session_id, msg_id, "user", content, embedding
        )

        # Background fact extraction (don't wait)
        asyncio.create_task(self._extract_and_save_facts(content))

    async def store_assistant_message(self, content: str) -> None:
        """Store an assistant message (episodic + vector)."""
        await episodic.save_message(self.session_id, "assistant", content)

        embedding = await get_embeddings(content)
        msg_id = str(uuid4())
        await vector_store.add_message_embedding(
            self.session_id, msg_id, "assistant", content, embedding
        )

    # ---- Context building ----
    async def get_context(self, query: str) -> List[ChatCompletionMessageParam]:
        """Assemble context for the agent: summary, user facts, relevant past messages."""
        context: List[ChatCompletionMessageParam] = []

        if self.summary:
            context.append(
                {
                    "role": "system",
                    "content": f"Previous conversation summary: {self.summary}",
                }
            )

        if self.user_facts:
            facts_str = ", ".join(f"{k}: {v}" for k, v in self.user_facts.items())
            context.append({"role": "system", "content": f"User facts: {facts_str}"})

        # Vector search
        query_embedding = await get_embeddings(query)
        similar = await vector_store.query_similar_messages(
            self.session_id, query_embedding, n_results=3
        )
        if similar:
            relevant_str = "Relevant past messages:\n"
            for msg in similar:
                role = msg["metadata"]["role"]
                content = msg["metadata"]["content"]
                relevant_str += f"{role}: {content}\n"
            context.append({"role": "system", "content": relevant_str})

        return context

    # ---- Summarization (background candidate) ----
    async def maybe_summarize(
        self,
        messages: List[ChatCompletionMessageParam],
        keep_last: int = 10,
        threshold: int = 20,
    ) -> Optional[List[ChatCompletionMessageParam]]:
        """
        Check if summarization is needed. If the conversation length (excluding system)
        exceeds `threshold`, summarize messages older than the last `keep_last`.
        Returns the trimmed message list (system + recent messages) or None if no summarization.
        """
        if len(messages) - 1 > threshold:
            return await self._summarize_older_messages(messages, keep_last)
        return None

    async def _summarize_older_messages(
        self, messages: List[ChatCompletionMessageParam], keep_last: int = 10
    ) -> Optional[List[ChatCompletionMessageParam]]:
        """Summarize messages older than the last `keep_last` and return the trimmed list."""
        system_msg = messages[0]
        conversation = messages[1:]

        if len(conversation) <= keep_last:
            return None

        older_msgs = conversation[:-keep_last]
        recent_msgs = conversation[-keep_last:]

        # Build text to summarize
        text_to_summarize = "\n".join(
            f"{msg['role']}: {msg.get('content')}" for msg in older_msgs
        )

        summary_prompt = f"""
            Summarize the following conversation concisely, capturing key points such as facts, user preferences and others.
            Focus on information which would be useful for continuing the conversation.

            Text to summarize:
            {text_to_summarize}
        """

        response = await self.client.chat.completions.create(
            messages=[{"role": "user", "content": summary_prompt}],
            model=self.model,
            temperature=0.2,
        )
        summary = response.choices[0].message.content
        if summary is None:
            summary = ""

        # Store summary in database
        await summarizer.save_summary(self.session_id, summary, len(older_msgs))

        # Update cached summary for future context
        self.summary = summary

        # Return trimmed message list (system + recent messages)
        return [system_msg] + recent_msgs
