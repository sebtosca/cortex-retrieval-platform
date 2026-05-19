"""Ingest all company AI-initiatives PDFs into the production Qdrant collection.

Extracts every PDF from Companies-AI-Initiatives(1).zip, chunks and embeds each
one with bge-m3, and upserts into settings.qdrant_collection.

Usage:
    python scripts/ingest_documents.py            # ingest all companies
    python scripts/ingest_documents.py --recreate # drop and rebuild the collection first
    make ingest-docs
"""
from __future__ import annotations

import argparse
import time
import zipfile
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from configs.settings import settings
from embeddings.bgem3 import BGEM3Embedder
from ingestion.chunker import chunk_documents
from ingestion.loader import load_pdf
from retrieval.store import QdrantStore

ZIP_PATH = Path(__file__).parent.parent / "Companies-AI-Initiatives(1).zip"
EXTRACT_DIR = Path("/tmp/cortex_ingest_docs")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate the Qdrant collection before ingesting",
    )
    args = parser.parse_args()

    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Source zip not found: {ZIP_PATH}")

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(ZIP_PATH) as zf:
        pdf_names = sorted(n for n in zf.namelist() if n.upper().endswith(".PDF"))
        zf.extractall(EXTRACT_DIR)

    pdf_paths = [EXTRACT_DIR / name for name in pdf_names]
    print(f"Found {len(pdf_paths)} PDFs: {[p.name for p in pdf_paths]}")

    print(f"\nCollection : {settings.qdrant_collection}")
    print(f"Qdrant URL : {settings.qdrant_url}")
    print(f"Chunk size : {settings.chunk_size} tokens  overlap={settings.chunk_overlap}")

    store = QdrantStore(url=settings.qdrant_url, collection=settings.qdrant_collection)
    store.setup_collection(recreate=args.recreate)

    print("\nLoading bge-m3 embedder (first run downloads ~2 GB) ...")
    embedder = BGEM3Embedder(use_fp16=True, batch_size=8)
    embedder._load()

    total_chunks = 0
    t_start = time.time()

    for pdf_path in pdf_paths:
        company = pdf_path.stem
        print(f"\n── {company} ──")

        docs = load_pdf(pdf_path)
        chunks = chunk_documents(
            docs,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            company=company,
        )
        print(f"  {len(docs)} pages  →  {len(chunks)} chunks")

        t0 = time.time()
        embedded = embedder.embed_chunks(chunks)
        print(f"  Embedded in {time.time() - t0:.1f}s")

        store.upsert(embedded)
        print(f"  Upserted {len(embedded)} points")
        total_chunks += len(embedded)

    elapsed = time.time() - t_start
    print(f"\n{'=' * 50}")
    print(f"Ingested {total_chunks} chunks from {len(pdf_paths)} PDFs in {elapsed:.1f}s")
    print(f"Collection '{settings.qdrant_collection}' is ready.")
    print("\nNext steps:")
    print("  make eval          # run RAGAS evaluation (requires ANTHROPIC_API_KEY)")
    print("  make benchmark     # run retrieval benchmark")


if __name__ == "__main__":
    main()
