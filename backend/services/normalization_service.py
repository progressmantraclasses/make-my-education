"""
normalization_service.py
Responsibility: Query normalization only.
  - normalize_query_for_cache : clean query string for cache key
  - hash_query                : SHA-256 hash of normalized query
  - detect_unit_language      : detect per-semester / total-cost phrasing
  - should_use_large_model    : decide whether to escalate to 70B LLM
"""

import hashlib
import re

import config


# ── Public functions ───────────────────────────────────────────────────────────


def normalize_query_for_cache(query: str) -> str:
    """Lowercase, collapse whitespace — produces stable cache key string."""
    cleaned = query.lower().strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def hash_query(query: str) -> str:
    """SHA-256 hash of the normalized query — used as Redis cache key."""
    normalized_query = normalize_query_for_cache(query)
    return hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()


def detect_unit_language(query: str) -> str:
    """Detect whether the query uses per-semester or total-course-cost language.

    Returns:
        'semester' — user asked about cost per semester
        'total'    — user asked about total/entire-course cost
        'default'  — annual fee language, no conversion needed
    """
    lower_query = query.lower()

    if re.search(r"per\s*sem(ester)?|/\s*sem(ester)?", lower_query):
        return "semester"

    if re.search(
        r"(total\s*(cost|fee|charge)|lakhs?\s*total|for\s*the\s*(entire\s*)?course)",
        lower_query,
    ):
        return "total"

    return "default"


def should_use_large_model(query: str, num_colleges_retrieved: int) -> bool:
    """Return True when the query warrants the 70B model instead of default 8B.

    Escalation triggers:
        - Config override (USE_LARGE_MODEL=true env var)
        - Complex multi-college comparison with many results retrieved
    """
    if config.USE_LARGE_MODEL:
        return True

    lower_query = query.lower()
    is_comparison_query = bool(
        re.search(r"\b(compare|rank|best|top|all colleges|every college)\b", lower_query)
    )
    has_many_results = num_colleges_retrieved > 6

    return is_comparison_query and has_many_results
