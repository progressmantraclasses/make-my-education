"""
retrieval_service.py
Responsibility: Pinecone vector retrieval only.
  - extract_metadata_filters : build Pinecone filter dict from query
  - retrieve_context         : embed query, fetch top-k chunks, merge by college
"""

import re
from collections import defaultdict
from typing import Any

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

import config


# ── Known city names in the dataset (for metadata filter extraction) ───────────
_KNOWN_CITIES = [
    "dehradun", "roorkee", "haridwar", "nainital", "almora",
    "rishikesh", "rudrapur", "mussoorie", "haldwani", "kashipur",
    "srinagar",
]


# ── Public functions ───────────────────────────────────────────────────────────


def extract_metadata_filters(query: str) -> dict[str, Any] | None:
    """Build a Pinecone metadata filter dict from the natural-language query.

    Extracts categorical constraints using regex (no LLM call):
        - College type  : Government / Private / Deemed
        - Hostel        : hostel_available = Yes
        - City          : exact city name match

    Returns:
        Pinecone filter dict, or None when no categorical filter detected.
    """
    lower_query = query.lower()
    filter_conditions: list[dict[str, Any]] = []

    # College type filter
    if re.search(r"\bgovernment\b|\bgovt\b|\bpublic\b", lower_query):
        filter_conditions.append({"type": {"$eq": "Government"}})
    elif re.search(r"\bprivate\b", lower_query):
        filter_conditions.append({"type": {"$eq": "Private"}})
    elif re.search(r"\bdeemed\b", lower_query):
        filter_conditions.append({"type": {"$eq": "Deemed"}})

    # Hostel availability filter
    if re.search(r"\bhostel\b", lower_query):
        filter_conditions.append({"hostel_available": {"$eq": "Yes"}})

    # City filter — stop at first match
    for city_name in _KNOWN_CITIES:
        if re.search(rf"\b{city_name}\b", lower_query):
            filter_conditions.append({"city": {"$eq": city_name.title()}})
            break

    if not filter_conditions:
        return None
    if len(filter_conditions) == 1:
        return filter_conditions[0]
    return {"$and": filter_conditions}


def retrieve_context(
    query: str,
    embedder: SentenceTransformer,
    pinecone_index: Any,
) -> tuple[str, list[str], int]:
    """Embed the query, retrieve top-k chunks from Pinecone, merge per college.

    Steps:
        1. Embed query with the provided sentence-transformer model
        2. Apply metadata filter (if any) before vector search
        3. Fetch top-k matches
        4. Deduplicate: group both chunks per college_id
        5. Build merged context string

    Returns:
        context_str         : LLM context with one block per college
        retrieved_college_ids : ordered list of college_ids retrieved
        num_unique_colleges : count of unique colleges in results
    """
    # Step 1 — embed query
    query_embedding = embedder.encode(query, normalize_embeddings=True).tolist()

    # Step 2 — extract metadata filter
    metadata_filter = extract_metadata_filters(query)

    # Step 3 — vector search
    pinecone_results = pinecone_index.query(
        vector=query_embedding,
        top_k=config.TOP_K,
        include_metadata=True,
        namespace=config.PINECONE_NAMESPACE,
        filter=metadata_filter,
    )

    matches = getattr(pinecone_results, "matches", None) or []
    if not matches:
        return "", [], 0

    # Step 4 — group by college_id, preserve retrieval order
    chunks_by_college: dict[str, list[str]] = defaultdict(list)
    college_id_order: list[str] = []

    for match in matches:
        match_metadata = getattr(match, "metadata", {}) or {}
        college_id = match_metadata.get("college_id", "unknown")
        chunk_text = match_metadata.get("text", "")

        if college_id not in chunks_by_college:
            college_id_order.append(college_id)
        chunks_by_college[college_id].append(chunk_text)

    # Step 5 — build merged context string
    context_blocks: list[str] = []
    for college_id in college_id_order:
        merged_text = "\n".join(chunks_by_college[college_id])
        context_blocks.append(f"--- {college_id} ---\n{merged_text}")

    context_str = "\n\n".join(context_blocks)
    retrieved_college_ids = college_id_order

    return context_str, retrieved_college_ids, len(retrieved_college_ids)


def build_pinecone_index() -> Any:
    """Create and return a Pinecone Index instance using config credentials."""
    pinecone_client = Pinecone(api_key=config.PINECONE_API_KEY)
    return pinecone_client.Index(config.PINECONE_INDEX_NAME)


def build_embedder() -> SentenceTransformer:
    """Load and return the sentence-transformer embedding model from config."""
    return SentenceTransformer(config.EMBEDDING_MODEL)
