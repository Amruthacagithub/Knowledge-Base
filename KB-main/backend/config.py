"""
Application configuration — loads environment variables from .env file.
Works locally (Docker Postgres + Qdrant) and online (Supabase + Qdrant Cloud).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# PostgreSQL — use DATABASE_URL for Supabase; otherwise build from parts (local Docker)
_database_url = os.getenv("DATABASE_URL", "").strip()
if _database_url:
    DATABASE_URL = _database_url
else:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "ekip")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ekip_dev_2026")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "ekip")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

# Qdrant — QDRANT_URL + QDRANT_API_KEY for Qdrant Cloud; else host/port (local Docker)
QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "enterprise_docs")

# Gemini — primary key (backward compatible)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "ekip-dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"

# CORS — comma-separated origins (add your Vercel URL in production)
_default_cors = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", _default_cors)

# Paths
DOCUMENTS_DIR = PROJECT_ROOT / "documents"
BM25_INDEX_DIR = PROJECT_ROOT / "indexdir"

# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Reranker model
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def get_gemini_api_keys() -> list[str]:
    """
    Ordered Gemini API keys: GEMINI_API_KEY, then GEMINI_API_KEY_2, _3, …
    Skips empty values and duplicates. At least one key is required for LLM answers.
    """
    keys: list[str] = []
    seen: set[str] = set()

    def add(key: str | None) -> None:
        if key and key.strip() and key.strip() not in seen:
            seen.add(key.strip())
            keys.append(key.strip())

    add(os.getenv("GEMINI_API_KEY"))
    n = 2
    while True:
        extra = os.getenv(f"GEMINI_API_KEY_{n}")
        if not extra:
            break
        add(extra)
        n += 1

    return keys


def get_gemini_models() -> list[str]:
    """
    Ordered Gemini models: primary then fallbacks when overloaded (503) or rate-limited.
    Override with GEMINI_MODEL and GEMINI_MODEL_FALLBACK (comma-separated) in .env.
    """
    primary = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite").strip()
    fallback_raw = os.getenv(
        "GEMINI_MODEL_FALLBACK",
        "gemini-3.1-flash-lite,gemini-2.5-flash,gemini-3.5-flash,gemini-3-flash-preview",
    )
    models: list[str] = []
    seen: set[str] = set()
    for name in [primary, *fallback_raw.split(",")]:
        name = name.strip()
        if name and name not in seen:
            seen.add(name)
            models.append(name)
    return models or ["gemini-2.5-flash-lite"]
