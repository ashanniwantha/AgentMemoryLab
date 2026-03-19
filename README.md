agent_memory/                  # Project root
├── .env                       # Environment variables (API keys)
├── .gitignore                 # Ignore .env, __pycache__, etc.
├── pyproject.toml             # Project dependencies (uv)
├── README.md                  # Project overview
│
├── src/                       # Main source code
│   ├── __init__.py
│   ├── agents/                # All agent classes
│   │   ├── __init__.py
│   │   ├── base.py            # BaseAgent (as you showed)
│   │   ├── supervisor.py      # SupervisorAgent
│   │   └── ...                # Other agents (worker, summarizer, etc.)
│   │
│   ├── memory/                 # Memory management modules
│   │   ├── __init__.py
│   │   ├── episodic.py         # Raw chat storage (SQLite)
│   │   ├── semantic.py         # Fact storage & updates
│   │   ├── vector_store.py     # Embeddings & retrieval
│   │   └── summarizer.py       # Conversation summarization logic
│   │
│   ├── tools/                  # Tools/functions agents can use
│   │   ├── __init__.py
│   │   └── ...                 # e.g., web search, calculator
│   │
│   ├── config/                  # Configuration handling
│   │   ├── __init__.py
│   │   └── settings.py          # Load .env, model names, etc.
│   │
│   ├── data/                    # Database files, vector store persistence
│   │   ├── chat_history.db      (SQLite, will be created)
│   │   └── chroma_db/           (Vector store files)
│   │
│   └── utils/                   # Helper functions
│       ├── __init__.py
│       └── ...                   # e.g., token counting, text chunking
│
└── tests/                       # Unit tests (optional for now)
    ├── __init__.py
    └── test_agents.py
