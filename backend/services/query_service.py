"""
query_service.py
Responsibility: Orchestrate the full RAG query pipeline.
  - log_query_metrics : append per-query metrics to JSONL log file
  - run_query         : cache → normalize → retrieve → generate → cache → log
"""

import datetime
import json
import time
from typing import Any

import config
from services.cache_service import cache_get, cache_set, get_redis_client
from services.generation_service import generate_answer
from services.normalization_service import (
    detect_unit_language,
    hash_query,
    should_use_large_model,
)
from services.retrieval_service import (
    build_embedder,
    build_pinecone_index,
    retrieve_context,
)


# ── Public functions ───────────────────────────────────────────────────────────


def log_query_metrics(
    query: str,
    input_token_count: int,
    output_token_count: int,
    latency_ms: float,
    was_cache_hit: bool,
    model_used: str,
) -> None:
    """Append a single-line JSON entry to the query metrics log file."""
    log_entry = {
        "timestamp":    datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "query":        query,
        "input_tokens":  input_token_count,
        "output_tokens": output_token_count,
        "latency_ms":   round(latency_ms, 1),
        "cache_hit":    was_cache_hit,
        "model":        model_used,
    }
    with open(config.QUERY_LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(log_entry) + "\n")


def run_query(query: str) -> dict[str, Any]:
    """Execute the full RAG pipeline for one user query.

    Pipeline order (cheapest checks first):
        1. Cache check  — return immediately on hit
        2. Unit normalization — detect semester/total language (regex, no LLM)
        3. Retrieval    — embed query → Pinecone metadata filter + vector search
        4. Model selection — 8B default, 70B for complex multi-college queries
        5. Generation   — Groq LLM with structured JSON output mode
        6. Cache write  — store response for 24h
        7. Log          — append metrics to JSONL file

    Returns:
        Response dict with keys: answer, citations, answered, reason_if_unanswered
    """
    pipeline_start_time = time.perf_counter()

    # ── Step 1: Cache check ────────────────────────────────────────────────────
    redis_client = get_redis_client()
    query_cache_key = hash_query(query)
    cached_response = cache_get(redis_client, query_cache_key)

    if cached_response is not None:
        latency_ms = (time.perf_counter() - pipeline_start_time) * 1000
        log_query_metrics(query, 0, 0, latency_ms, was_cache_hit=True, model_used="cache")
        return cached_response

    # ── Step 2: Query normalization ────────────────────────────────────────────
    unit_type = detect_unit_language(query)

    # ── Step 3: Retrieval ──────────────────────────────────────────────────────
    embedder = build_embedder()
    pinecone_index = build_pinecone_index()

    context_str, retrieved_college_ids, num_unique_colleges = retrieve_context(
        query, embedder, pinecone_index
    )

    if not context_str:
        empty_response = {
            "answer": "No matching colleges found in the dataset for this query.",
            "citations": [],
            "answered": False,
            "reason_if_unanswered": "No relevant data found in the college dataset.",
        }
        latency_ms = (time.perf_counter() - pipeline_start_time) * 1000
        log_query_metrics(query, 0, 0, latency_ms, was_cache_hit=False, model_used="none")
        cache_set(redis_client, query_cache_key, empty_response)
        return empty_response

    # ── Step 4: Model selection ────────────────────────────────────────────────
    selected_model = (
        config.GROQ_MODEL_LARGE
        if should_use_large_model(query, num_unique_colleges)
        else config.GROQ_MODEL_SMALL
    )

    # ── Step 5: LLM generation ─────────────────────────────────────────────────
    response_dict, input_token_count, output_token_count = generate_answer(
        query, context_str, unit_type, selected_model
    )

    # ── Step 6: Cache write ────────────────────────────────────────────────────
    # Only cache successful responses (avoid poisoning the cache with API failures)
    reason = response_dict.get("reason_if_unanswered")
    answer = response_dict.get("answer")
    if reason != "Failed to parse LLM response as JSON." and answer != "System Error":
        cache_set(redis_client, query_cache_key, response_dict)

    # ── Step 7: Log ────────────────────────────────────────────────────────────
    latency_ms = (time.perf_counter() - pipeline_start_time) * 1000
    log_query_metrics(
        query, input_token_count, output_token_count,
        latency_ms, was_cache_hit=False, model_used=selected_model
    )

    return response_dict
