# Multi-Agent Memory System

A production-grade, asynchronous multi-agent framework with layered memory (episodic, semantic, vector, summarization) and collaborative workflows. Built with Python, Ollama, and SQLite.

## Overview

Modern AI agents need more than conversation history. They need structured facts, semantic search, summarization, and agent coordination through a shared memory layer. This project demonstrates how to build that system in a practical, async-first architecture.

### Key Achievements

- Four memory layers: episodic (raw logs), semantic (structured facts with versioning), vector (semantic search with ChromaDB), and summarization (token-based context compression).
- Fully async I/O (`aiosqlite`, `httpx`, `asyncio`) for non-blocking operations.
- Background tasks for fact extraction and reflection.
- Multi-agent collaboration (story generation pipeline) with concurrent critics.
- Smart supervisor that handles regular chat and auto-triggers story workflow.
- Periodic reflection agent that analyzes stored memories and generates insights.

## Features

- **Episodic Memory**: all messages stored in SQLite (async) with session isolation.
- **Semantic Memory**: key-value facts with versioning, confidence scores, and categories (`user_fact`, `draft`, `feedback`, `final`, `insight`).
- **Vector Memory**: ChromaDB with cosine similarity, wrapped in `asyncio.to_thread`.
- **Summarization**: token-threshold-based compression of older messages into the `summaries` table.
- **Fact Extraction**: background task using an LLM prompt to extract user facts.
- **Reflection**: periodic/on-demand analysis of stored entries to generate high-level insights.
- **Multi-Agent Story Pipeline**:
  - `DraftAgent` produces the initial story.
  - `StyleCriticAgent` and `FactCriticAgent` run concurrently.
  - `ConsolidatorAgent` merges feedback into a final output.
- **Smart Supervisor**: detects story intents and routes to pipeline automatically.
- **Async Everywhere**: DB calls, embeddings, and LLM calls are async for concurrency.

## Architecture

```mermaid
graph TD
    Supervisor[Supervisor Agent] --> MemoryService
    Pipeline[Story Pipeline<br/>(Draft, Critics, Consolidator)] --> MemoryService
    Reflection[Reflection Agent] --> MemoryService

    MemoryService --> Episodic[(Episodic<br/>SQLite)]
    MemoryService --> Semantic[(Semantic<br/>SQLite)]
    MemoryService --> Vector[(Vector<br/>ChromaDB)]
    MemoryService --> Summaries[(Summaries<br/>SQLite)]
```

## Prerequisites

- Python 3.12+
- [Ollama](https://ollama.com/) installed and running (`ollama serve`)
- Required models:

```bash
ollama pull llama3.2:3b          # chat model
ollama pull nomic-embed-text     # embedding model
```

## Installation

```bash
git clone https://github.com/ashanniwantha/AgentMemoryLab.git
cd AgentMemoryLab
uv sync
cp .env.example .env
```

## Configuration

Edit `.env` (or create one based on `.env.example`) with at least:

```ini
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL_NAME=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
SUMMARIZATION_TOKEN_THRESHOLD=8000
REFLECTION_INTERVAL_MINUTES=5
```

## Run

```bash
uv run python -m main
```

## Commands

- `/quit` exits the application.
- `/reflect` runs reflection immediately.

## Usage Examples

### Normal Conversation

```text
You > What is the capital of France?
SUPERVISOR > The capital of France is Paris.

You > My name is Ashan and I love Python.
SUPERVISOR > Nice to meet you, Ashan! ...
```

### Story Generation (Automatically Triggered)

```text
You > Write a story about a robot that learns to paint.
SUPERVISOR > [STORY] topic: a robot that learns to paint
[Supervisor] Starting story pipeline...
... (final story printed)
```

### Manual Reflection

```text
You > /reflect
Running reflection...
--- Reflection Insights ---
Based on the stored memories, the user is interested in AI engineering...
```

## Documentation

Detailed explanations of the design and components are in:

- [docs/architecture.md](docs/architecture.md)
- [docs/project_structure.md](docs/project_structure.md)

## License

MIT