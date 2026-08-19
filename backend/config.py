"""Central configuration — loads env vars, defines constants, fails loudly on missing keys."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ── Required env vars ──────────────────────────────────────────────────────────
_REQUIRED = [
    "GROQ_API_KEY",
    "PINECONE_API_KEY",
    "UPSTASH_REDIS_REST_URL",
    "UPSTASH_REDIS_REST_TOKEN",
]

_missing = [k for k in _REQUIRED if not os.getenv(k)]
if _missing:
    sys.exit(f"FATAL: missing environment variable(s): {', '.join(_missing)}")

GROQ_API_KEY: str = os.environ["GROQ_API_KEY"]
PINECONE_API_KEY: str = os.environ["PINECONE_API_KEY"]
UPSTASH_REDIS_REST_URL: str = os.environ["UPSTASH_REDIS_REST_URL"]
UPSTASH_REDIS_REST_TOKEN: str = os.environ["UPSTASH_REDIS_REST_TOKEN"]

# ── Pinecone ───────────────────────────────────────────────────────────────────
PINECONE_INDEX_NAME = "college-advisor"
PINECONE_NAMESPACE = "colleges-v1"
PINECONE_DIMENSION = 384          # all-MiniLM-L6-v2 output dim
PINECONE_METRIC = "cosine"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"

# ── Embedding model ───────────────────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ── Groq LLM ──────────────────────────────────────────────────────────────────
GROQ_MODEL_SMALL = "openai/gpt-oss-20b"
GROQ_MODEL_LARGE = "openai/gpt-oss-120b"
USE_LARGE_MODEL = os.getenv("USE_LARGE_MODEL", "false").lower() == "true"

# ── Retrieval ──────────────────────────────────────────────────────────────────
TOP_K = 20
    
# ── Cache ──────────────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS = 86400         # 24 hours

# ── Logging ────────────────────────────────────────────────────────────────────
QUERY_LOG_FILE = "query_log.jsonl"

# ── Data ───────────────────────────────────────────────────────────────────────
CSV_FILE = "sample_colleges.csv"
