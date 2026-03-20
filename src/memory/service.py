"""
MemoryService: Centralized memory management for multi-agent  systems.
Handle all memory operations (semantic, episodic, vectordb, summarizations)
and provide a clean API for agents to utilize
"""

import threading
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from openai.types.chat import ChatCompletionMessageParam

from src.config import settings, clients
from src.memory import episodic, semantic, vector_store, summarizer
from src.utils.embeddings import get_embeddings


class MemoryService:
    def __init__(self, session_id: UUID) -> None:
        # Initialize the databases, create table if needed
        episodic.init_db()
        summarizer.init_summary_table()
        semantic.init_semantic_table()

        self.session_id = session_id
        self.lock = threading.Lock()  # for thread-safe writes

        # LLM
        self.client = clients.get_openai_client()
        self.model = settings.OLLAMA_MODEL_NAME

        # Load cached data
        self.facts: Dict[str, str] = {}
        self._load_facts()

        self.summary: Optional[str] = None
        self._load_summary()

    def _load_facts(self):
        """Load all facts for this session into cache."""
        facts_list = semantic.get_all_facts(self.session_id)
        for fact in facts_list:
            self.facts[fact["key"]] = fact["value"]

    def _extract_facts(self, text: str) -> List[tuple[str, str, float]]:
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

    def _load_summary(self):
        """Load the latest summary for this session"""
        self.summary = summarizer.get_latest_summary(self.session_id)

    def store_user_message(self, content: str) -> None:
        """Store a user message in all memory systems"""
        with self.lock:
            # Episodic
            episodic.save_message(self.session_id, "user", content)

            # Extract facts
            extracted = self._extract_facts(content)
            for key, value, confidence in extracted:
                semantic.save_fact(
                    self.session_id, key=key, value=value, confidence=confidence
                )

            # 4. Vector embeddings
            embeddings = get_embeddings(text=content)
            msg_id = str(uuid4())
            vector_store.add_message_embedding(
                session_id=self.session_id,
                message_id=msg_id,
                role="user",
                content=content,
                embedding=embeddings,
            )

    def store_assistant_message(self, content: str):
        """Store a assistant message"""
        with self.lock:
            # Episodic
            episodic.save_message(self.session_id, "assistant", content)

            # Embed the assistant message and save it to the vector database
            embeddings = get_embeddings(content)
            msg_id = str(uuid4())
            vector_store.add_message_embedding(
                session_id=self.session_id,
                message_id=msg_id,
                role="assistant",
                content=content,
                embedding=embeddings,
            )

    def get_context(self, query: str) -> List[ChatCompletionMessageParam]:
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
        query_embeddings = get_embeddings(query)
        similar_embeddings = vector_store.query_similar_messages(
            self.session_id, query_embeddings, 3
        )
        if similar_embeddings:
            relevant_str = "Relevant past messages:\n"
            for msg in similar_embeddings:
                role = msg["metadata"]["role"]
                content = msg["metadata"]["content"]
                relevant_str += f"{role}: {content}"
            context.append({"role": "system", "content": relevant_str})

        return context
