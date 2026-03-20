"""
MemoryService: Centralized memory management for multi-agent  systems.
Handle all memory operations (semantic, episodic, vectordb, summarizations)
and provide a clean API for agents to utilize
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
        self.lock = asyncio.Lock()  # for thread-safe writes

        # LLM
        self.client = get_openai_client()
        self.model = settings.OLLAMA_MODEL_NAME

        # Initialized cached data
        self.facts: Dict[str, str] = {}
        self.summary: Optional[str] = None

        # We'll initialize DBs and load data in an async init method
        self._initialized = False

    async def init(self):
        """Assync initialization: create table and load cached data."""
        if self._initialized:
            return

        # Initialize the databases, create table if needed
        await episodic.init_db()
        await summarizer.init_summary_table()
        await semantic.init_semantic_table()

        # Load cached data
        await self._load_facts()
        await self._load_summary()

        self._initialized = True

    async def _load_facts(self):
        """Load all facts for this session into cache."""
        facts_list = await semantic.get_all_facts(self.session_id)
        for fact in facts_list:
            self.facts[fact["key"]] = fact["value"]

    async def _extract_facts(self, text: str) -> List[tuple[str, str, float]]:
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
                # Simple confidence: 1.0 for now (could be inferred from tone later)
                facts.append((key, value, 1.0))

        return facts

    async def _background_extract_facts(self, content: str):
        """Background task for fact extraction"""
        extracted = await self._extract_facts(content)
        async with self.lock:
            for key, value, confidence in extracted:
                await semantic.save_fact(self.session_id, key, value, confidence)
                self.facts[key] = value

    async def _load_summary(self):
        """Load the latest summary for this session"""
        self.summary = await summarizer.get_latest_summary(self.session_id)

    async def store_user_message(self, content: str) -> None:
        """Store a user message in all memory systems"""
        # Episodic
        await episodic.save_message(self.session_id, "user", content)

        # Vector embeddings
        embeddings = await get_embeddings(text=content)
        msg_id = str(uuid4())
        await vector_store.add_message_embedding(
            session_id=self.session_id,
            message_id=msg_id,
            role="user",
            content=content,
            embedding=embeddings,
        )

        asyncio.create_task(self._background_extract_facts(content))

    async def store_assistant_message(self, content: str):
        """Store a assistant message"""
        # Episodic
        await episodic.save_message(self.session_id, "assistant", content)

        # Embed the assistant message and save it to the vector database
        embeddings = await get_embeddings(content)
        msg_id = str(uuid4())
        await vector_store.add_message_embedding(
            session_id=self.session_id,
            message_id=msg_id,
            role="assistant",
            content=content,
            embedding=embeddings,
        )

    async def get_context(self, query: str) -> List[ChatCompletionMessageParam]:
        """
        Assemble context for the agent including summary, facts, recent messages,
        and relevant past messages from vector search
        """
        context: List[ChatCompletionMessageParam] = []

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

        # Vector search
        query_embeddings = await get_embeddings(query)
        similar_embeddings = await vector_store.query_similar_messages(
            self.session_id, query_embeddings, 3
        )
        if similar_embeddings:
            relevant_str = "Relevant past messages:\n"
            for msg in similar_embeddings:
                role = msg["metadata"]["role"]
                content = msg["metadata"]["content"]
                relevant_str += f"{role}: {content}\n"
            context.append({"role": "system", "content": relevant_str})

        return context

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
        if len(messages) - 1 > threshold:  # exclude system prompt
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
