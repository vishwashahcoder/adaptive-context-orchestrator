import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Database configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "data", "orchestrator.db")

# Model configurations
SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-2.5-flash"
AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-thinking"
]

# Retriever weights
RETRIEVER_SEMANTIC_WEIGHT = 0.7
RETRIEVER_BM25_WEIGHT = 0.3

# Scorer weights
SCORER_SIMILARITY_WEIGHT = 0.5
SCORER_IMPORTANCE_WEIGHT = 0.3
SCORER_RECENCY_WEIGHT = 0.2
SCORER_RECENCY_HALF_LIFE_HOURS = 72.0  # 3 days half-life for exponential decay
SCORER_RECENCY_DECAY_HOURS = 168.0  # 7 days max cutoff fallback