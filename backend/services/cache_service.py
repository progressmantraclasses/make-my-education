"""
cache_service.py
Responsibility: Upstash Redis caching only.
  - get_redis_client : create Redis connection
  - cache_get        : look up cached response by key
  - cache_set        : store response with TTL
"""

import json
from typing import Any

from upstash_redis import Redis

import config


# ── Public functions ───────────────────────────────────────────────────────────


def get_redis_client() -> Redis:
    """Create and return an Upstash Redis client using env-var credentials."""
    return Redis(
        url=config.UPSTASH_REDIS_REST_URL,
        token=config.UPSTASH_REDIS_REST_TOKEN,
    )


def cache_get(redis_client: Redis, cache_key: str) -> dict[str, Any] | None:
    """Look up a cached query response.

    Returns:
        Parsed JSON dict if cache hit, None on miss or any Redis error.
        Errors degrade gracefully — never raise, just return None.
    """
    try:
        cached_value = redis_client.get(cache_key)
        if cached_value:
            return json.loads(cached_value) if isinstance(cached_value, str) else cached_value
    except Exception:
        pass  # Degrade to cache miss on any Redis error
    return None


def cache_set(redis_client: Redis, cache_key: str, response_dict: dict[str, Any]) -> None:
    """Store a response dict in cache with configured TTL.

    Never raises — if Redis write fails the request still succeeds.
    """
    try:
        redis_client.set(
            cache_key,
            json.dumps(response_dict),
            ex=config.CACHE_TTL_SECONDS,
        )
    except Exception:
        pass  # Don't fail the query if cache write fails
