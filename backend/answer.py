"""
answer.py — CLI entry point for the RAG query pipeline.

All pipeline logic lives in backend/services/. This file is a thin wrapper
so the original CLI contract is preserved exactly:

Usage:
    python answer.py "Which colleges offer an MBA, and what do they cost?"

Prints exactly one JSON object to stdout.
"""

import json
import sys

from services.query_service import run_query


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit('Usage: python answer.py "<your question>"')

    query = sys.argv[1]
    result = run_query(query)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
