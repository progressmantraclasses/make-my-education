"""
ingestion_service.py
Responsibility: College data chunking logic only.
  - read_colleges         : read CSV file into list of row dicts
  - build_structured_text : flatten structured columns into template string
  - build_about_text      : prefix about text with college name + ID
  - build_chunk_metadata  : build Pinecone metadata dict for a chunk
  - create_chunks         : produce 2 chunks per college (structured + about)
"""

import csv
import sys
from typing import Any


# ── Public functions ───────────────────────────────────────────────────────────


def read_colleges(csv_file_path: str) -> list[dict[str, Any]]:
    """Read college data from CSV and return list of row dicts.

    Args:
        csv_file_path: absolute or relative path to the CSV file

    Raises:
        SystemExit: if file is empty or cannot be read
    """
    with open(csv_file_path, encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        college_rows = list(reader)

    if not college_rows:
        sys.exit("FATAL: CSV is empty or could not be parsed.")

    print(f"Read {len(college_rows)} colleges from {csv_file_path}")
    return college_rows


def build_structured_text(college_row: dict[str, Any]) -> str:
    """Flatten all structured columns into a single readable template string.

    Special handling:
        - avg_placement_lpa == 0  →  "Not reported / not applicable"
          (prevents LLM from treating 0 as worst placement)
    """
    annual_fees  = int(float(college_row["annual_fees_inr"]))
    cutoff_pct   = int(float(college_row["last_year_cutoff_pct"]))
    placement_lpa = float(college_row["avg_placement_lpa"])
    estab_year   = int(float(college_row["established_year"]))
    total_seats  = int(float(college_row["total_seats"]))

    placement_display = (
        "Not reported / not applicable"
        if placement_lpa == 0
        else f"{placement_lpa} LPA"
    )

    return (
        f"College: {college_row['name']} ({college_row['college_id']}) | "
        f"Type: {college_row['type']} | "
        f"City: {college_row['city']}, {college_row['state']} | "
        f"Fees: ₹{annual_fees:,}/year | "
        f"Cutoff: {cutoff_pct}% (hard minimum aggregate) | "
        f"Courses: {college_row['courses_offered']} | "
        f"Hostel: {college_row['hostel_available']} | "
        f"NAAC: {college_row['naac_grade']} | "
        f"Avg placement: {placement_display} | "
        f"Total seats: {total_seats} | "
        f"Established: {estab_year}"
    )


def build_about_text(college_row: dict[str, Any]) -> str:
    """Prefix the about field with college name and ID for disambiguation.

    Ensures retrieval always knows which college a chunk belongs to, even
    for colleges with similar names (e.g. Ganga Valley vs Ganga Institute).
    """
    return f"{college_row['name']} ({college_row['college_id']}): {college_row['about']}"


def build_chunk_metadata(college_row: dict[str, Any], chunk_type: str) -> dict[str, Any]:
    """Build the Pinecone metadata dict to attach to every vector.

    Metadata is used both for citations and for pre-filtering retrieval.

    Args:
        college_row: single CSV row dict
        chunk_type : 'structured' | 'about'
    """
    return {
        "college_id":      college_row["college_id"],
        "name":            college_row["name"],
        "city":            college_row["city"],
        "type":            college_row["type"],
        "hostel_available": college_row["hostel_available"],
        "chunk_type":      chunk_type,
    }


def create_chunks(college_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create exactly 2 chunks per college: one structured, one about-text.

    Returns list of chunk dicts with keys: id, text, metadata.
    IDs are deterministic → re-ingestion is idempotent (overwrites, no duplicates).
    """
    all_chunks: list[dict[str, Any]] = []

    for college_row in college_rows:
        college_id = college_row["college_id"]

        # Chunk 1 — structured tabular data
        all_chunks.append({
            "id":       f"{college_id}_structured",
            "text":     build_structured_text(college_row),
            "metadata": build_chunk_metadata(college_row, "structured"),
        })

        # Chunk 2 — about narrative text
        all_chunks.append({
            "id":       f"{college_id}_about",
            "text":     build_about_text(college_row),
            "metadata": build_chunk_metadata(college_row, "about"),
        })

    return all_chunks
