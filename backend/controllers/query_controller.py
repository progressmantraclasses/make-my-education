"""
query_controller.py
Responsibility: Validate incoming query request and format the API response.
  - handle_query_request : validate → call query_service → return response dict
"""

from typing import Any

from services.query_service import run_query


# ── Request / Response schemas (plain dicts — FastAPI handles Pydantic above) ──


def handle_query_request(query_text: str) -> dict[str, Any]:
    """Validate the query text and invoke the RAG pipeline.

    Args:
        query_text: raw question string from the API request body

    Returns:
        Response dict: { answer, citations, answered, reason_if_unanswered }

    Raises:
        ValueError: if query_text is blank after stripping
    """
    stripped_query = query_text.strip()

    if not stripped_query:
        raise ValueError("Query must not be empty.")

    if len(stripped_query) > 2000:
        raise ValueError("Query exceeds maximum allowed length of 2000 characters.")

    return run_query(stripped_query)
