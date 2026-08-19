"""
ingest.py — CLI entry point for ingesting college data into Pinecone.

All chunking logic lives in backend/services/ingestion_service.py.
This file handles Pinecone index management and embedding — it is the
correct place for that since ingestion is a one-time / refresh operation.

Usage:
    python ingest.py
"""

import sys
import time

from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

import config
from services.ingestion_service import create_chunks, read_colleges


def main() -> None:
    ingest_start_time = time.perf_counter()

    # 1. Read CSV
    college_rows = read_colleges(config.CSV_FILE)

    # 2. Create chunks (2 per college)
    all_chunks = create_chunks(college_rows)
    print(f"Created {len(all_chunks)} chunks ({len(all_chunks) // 2} colleges × 2)")

    # 3. Load embedding model
    print(f"Loading embedding model: {config.EMBEDDING_MODEL} ...")
    embedder = SentenceTransformer(config.EMBEDDING_MODEL)

    # 4. Embed all chunk texts
    chunk_texts = [chunk["text"] for chunk in all_chunks]
    print(f"Embedding {len(chunk_texts)} chunks ...")
    embeddings = embedder.encode(chunk_texts, show_progress_bar=True, normalize_embeddings=True)
    print(f"Embedding complete. Dimension: {embeddings.shape[1]}")

    # 5. Connect to Pinecone — create index if it doesn't exist
    pinecone_client = Pinecone(api_key=config.PINECONE_API_KEY)

    if not pinecone_client.has_index(config.PINECONE_INDEX_NAME):
        print(f"Creating Pinecone index '{config.PINECONE_INDEX_NAME}' ...")
        pinecone_client.create_index(
            name=config.PINECONE_INDEX_NAME,
            dimension=config.PINECONE_DIMENSION,
            metric=config.PINECONE_METRIC,
            spec=ServerlessSpec(
                cloud=config.PINECONE_CLOUD,
                region=config.PINECONE_REGION,
            ),
        )
        # Wait for index to be ready
        index_desc = pinecone_client.describe_index(config.PINECONE_INDEX_NAME)
        while not getattr(
            index_desc.status,
            "ready",
            index_desc.status.get("ready") if isinstance(index_desc.status, dict) else False,
        ):
            print("  Waiting for index to be ready ...")
            time.sleep(2)
            index_desc = pinecone_client.describe_index(config.PINECONE_INDEX_NAME)
        print("  Index ready.")
    else:
        print(f"Pinecone index '{config.PINECONE_INDEX_NAME}' already exists.")

    pinecone_index = pinecone_client.Index(config.PINECONE_INDEX_NAME)

    # 6. Build vector list and upsert (idempotent — same IDs overwrite)
    vectors_to_upsert = [
        {
            "id":     chunk["id"],
            "values": emb.tolist(),
            "metadata": {**chunk["metadata"], "text": chunk["text"]},
        }
        for chunk, emb in zip(all_chunks, embeddings)
    ]

    batch_size = 50
    for batch_start in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[batch_start : batch_start + batch_size]
        pinecone_index.upsert(vectors=batch, namespace=config.PINECONE_NAMESPACE)
        batch_num = batch_start // batch_size + 1
        print(f"  Upserted batch {batch_num} ({len(batch)} vectors)")

    elapsed_seconds = time.perf_counter() - ingest_start_time
    print(f"\nIngestion complete. {len(vectors_to_upsert)} vectors in "
          f"namespace '{config.PINECONE_NAMESPACE}'. Took {elapsed_seconds:.1f}s.")

    # 7. Verify vector count
    index_stats = pinecone_index.describe_index_stats()
    namespaces_map = (
        getattr(index_stats, "namespaces", None)
        or (index_stats.get("namespaces", {}) if isinstance(index_stats, dict) else {})
    )
    namespace_stats = namespaces_map.get(config.PINECONE_NAMESPACE, {})
    vector_count = (
        getattr(namespace_stats, "vector_count", None)
        or (namespace_stats.get("vector_count", "N/A") if isinstance(namespace_stats, dict) else "N/A")
    )
    print(f"Index stats — namespace '{config.PINECONE_NAMESPACE}': {vector_count} vectors")


if __name__ == "__main__":
    main()
