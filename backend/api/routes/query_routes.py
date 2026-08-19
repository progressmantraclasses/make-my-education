"""
query_routes.py
Responsibility: Define HTTP routes for the /api/query endpoint.
  - POST /api/query : accepts { "query": "..." }, returns RAG answer JSON
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from controllers.query_controller import handle_query_request

query_router = APIRouter(prefix="/api", tags=["query"])


# ── Request / Response models ──────────────────────────────────────────────────


class QueryRequest(BaseModel):
    """Incoming request body for the query endpoint."""
    query: str


class QueryResponse(BaseModel):
    """Outgoing response body from the query endpoint."""
    answer: str
    citations: list[str]
    answered: bool
    reason_if_unanswered: str | None
    follow_up_questions: list[str] = []


# ── Route handlers ─────────────────────────────────────────────────────────────


@query_router.post("/query", response_model=QueryResponse)
async def post_query(request_body: QueryRequest) -> QueryResponse:
    """Accept a natural-language college question and return a grounded answer.

    - Checks Upstash Redis cache first (no LLM call on cache hit).
    - Retrieves relevant college chunks from Pinecone.
    - Generates a structured JSON answer via Groq LLM.
    - Caches and logs the result.
    """
    try:
        result = handle_query_request(request_body.query)
    except ValueError as validation_error:
        raise HTTPException(status_code=422, detail=str(validation_error))
    except Exception as pipeline_error:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(pipeline_error)}")

    return QueryResponse(**result)
