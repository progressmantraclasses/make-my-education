"""
app.py
Responsibility: Create and configure the FastAPI application instance.
  - Creates FastAPI app with metadata
  - Adds CORS middleware for Vite dev server (localhost:5173)
  - Registers all routers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.query_routes import query_router

# ── App instance ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Make My Education — College Advisor API",
    description="RAG-powered API that answers natural-language questions about colleges, grounded in a verified dataset.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — allow Vite dev server and same-origin ──────────────────────────────

_ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173",
    "http://localhost:3000",   # Common alternative
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ───────────────────────────────────────────────────────────

app.include_router(query_router)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "ok", "service": "college-advisor-api"}
