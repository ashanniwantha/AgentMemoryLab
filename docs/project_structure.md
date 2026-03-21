# Project Structure

## File Descriptions

| File | Description |
|------|-------------|
| `main.py` | Main loop, session resumption, command parsing, starts background reflection task. |
| `src/agents/base.py` | `BaseAgent` – holds conversation history (`self.messages`), manages prompt building, and handles streaming responses. |
| `src/agents/supervisor.py` | Specialised agent that includes a personality to detect story requests and output the `[STORY]` marker. |
| `src/agents/drafter.py` | Generates story drafts using the LLM and stores them with category `draft`. |
| `src/agents/style_critic.py` | Critiques style, narrative flow, and readability; stores feedback with category `feedback`. |
| `src/agents/fact_critic.py` | Critiques factual/logical consistency; stores feedback with category `feedback`. |
| `src/agents/consolidator.py` | Reads the draft and both feedbacks, produces a final story (category `final`). |
| `src/agents/reflection.py` | Analyses all stored entries (all categories) and stores insights (category `insight`). |
| `src/memory/service.py` | `MemoryService` – central manager for all memory operations. |
| `src/memory/episodic.py` | Async SQLite functions for the `messages` table (raw logs). |
| `src/memory/semantic.py` | Async SQLite functions for the `semantic_memory` table (key‑value with categories). |
| `src/memory/vector_store.py` | Wraps ChromaDB operations in `asyncio.to_thread`. |
| `src/memory/summarizer.py` | Async SQLite functions for the `summaries` table. |
| `src/pipelines/story_pipeline.py` | Orchestrates the story workflow: draft → concurrent critics → final. |
| `src/utils/embeddings.py` | Async HTTP call to Ollama’s `/embeddings` endpoint. |
| `src/utils/token_counter.py` | Uses `litellm.token_counter` to count tokens in OpenAI‑style message lists. |
| `src/config/settings.py` | Loads environment variables, provides typed settings. |
| `src/clients.py` | Singleton `AsyncOpenAI` client pointing to Ollama. |
| `data/` | Runtime storage; ignored in git. |