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

# Base URLS for OpenAI compatible endpoints
# Google Gemini
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# Database paths
SQL_DB_PATH = os.getenv("SQL_DB_PATH")
VECTOR_DB = os.getenv("VECTOR_DB")

if not SQL_DB_PATH or not VECTOR_DB:
    raise ValueError("SQL and Vector databases are not set in environment variable")

# Optional: other settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
