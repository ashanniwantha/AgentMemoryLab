"""
Configuration settings loaded from environment variables.
All settings are accessed as module-level constants
"""

import os
from dotenv import load_dotenv

# Load environment varibles from .env file
load_dotenv()

# --- API KEYS ---

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")


# MODEL Configuration
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llama3.2:3b")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")

# Base URLS for OpenAI compatible endpoints
# Google Gemini
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# Database paths
SQL_DB_PATH = os.getenv("SQL_DB_PATH", "src/data/chat_history.db")
VECTOR_DB = os.getenv("VECTOR_DB", "src/data/chroma_db")

# Optional: other settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
SUMMARIZATION_TOKEN_THRESHOLD = int(os.getenv("SUMMARIZATION_TOKEN_THRESHOLD", 8000))
REFLECTION_INTERVAL_MINUTES = int(os.getenv("REFLECTION_INTERVAL_MINUTES", 5))
