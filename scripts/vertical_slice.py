"""
Vertical slice smoke test — Issue #1/#2.
Proves: one PDF → bge-m3 (dense+sparse) → Qdrant hybrid search
        → cross-encoder rerank → Claude Haiku SSE stream via LiteLLM.

Run: make slice
     python scripts/vertical_slice.py
     python scripts/vertical_slice.py --query "What AI projects is NVDA working on?"

First run downloads bge-m3 (~2GB). Subsequent runs use the HuggingFace cache.
Requires: Qdrant running at QDRANT_URL (default: http://localhost:6333)
          ANTHROPIC_API_KEY set in environment or .env
"""

import argparse
import os
import time
import zipfile
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from embeddings.bgem3 import BGEM3Embedder
from ingestion.chunker import chunk_documents
from ingestion.loader import load_pdf
from llm.client import CortexLLM
from llm.prompts import build_rag_messages
from retrieval.reranker import CrossEncoderReranker
from retrieval.store import QdrantStore

ZIP_PATH = Path(__file__).parent.parent / "Companies-AI-Initiatives(1).zip"
EXTRACT_DIR = Path("/tmp/cortex_pdfs")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "cortex_slice_test"
CANDIDATES_K = 20
RERANK_K = 5
DEFAULT_QUERY = "What is the most important AI project IBM is working on?"


def extract_pdf(company: str = "IBM") -> Path:
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        pdf_names = [n for n in zf.namelist() if n.upper().endswith(".PDF")]
        target = next(
            (p for p in pdf_names if company.upper() in p.upper()),
            pdf_names[0],
        )
        zf.extract(target, EXTRACT_DIR)
        path = EXTRACT_DIR / target
    print(f"  PDF: {path.name}")
    return path


def main():
    parser = argparse.ArgumentParser(description="Cortex vertical slice smoke test")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--company", default="IBM", help="Which company PDF to ingest")
    args = parser.parse_args()

    print("Cortex — Vertical Slice Smoke Test")
    print("=" * 60)
    t_total = time.time()

    print("\n[1/6] Extracting PDF...")
    pdf_path = extract_pdf(args.company)

    print("\n[2/6] Chunking...")
    docs = load_pdf(pdf_path)
    chunks = chunk_documents(docs, chunk_size=1000, chunk_overlap=150)
    print(f"  Chunks: {len(chunks)}")

    print("\n[3/6] Embedding with bge-m3...")
    t0 = time.time()
    embedder = BGEM3Embedder(use_fp16=True, batch_size=8)
    embedded_chunks = embedder.embed_chunks(chunks)
    print(f"  Embedded {len(embedded_chunks)} chunks in {time.time() - t0:.1f}s")

    print("\n[4/6] Storing in Qdrant (hybrid collection)...")
    store = QdrantStore(url=QDRANT_URL, collection=COLLECTION)
    store.setup_collection(recreate=True)
    store.upsert(embedded_chunks)
    print(f"  Stored {len(embedded_chunks)} points in Qdrant")

    print("\n[5/6] Embedding query + hybrid search + rerank...")
    q_dense, q_sparse = embedder.encode_texts([args.query])
    q_idx = [int(k) for k in q_sparse[0].keys()]
    q_vals = [float(v) for v in q_sparse[0].values()]
    candidates = store.hybrid_search(q_dense[0], q_idx, q_vals, limit=CANDIDATES_K)

    reranker = CrossEncoderReranker()
    top_results = reranker.rerank(args.query, candidates, top_k=RERANK_K)
    print(f"  Retrieved {len(candidates)} candidates, reranked to {len(top_results)}")
    print(f"  (top score: {top_results[0].score:.3f}, bottom: {top_results[-1].score:.3f})")

    print("\n[6/6] Streaming from Claude Haiku via LiteLLM...")
    passages = [r.text for r in top_results]
    messages = build_rag_messages(args.query, passages)
    llm = CortexLLM(model="claude-haiku-4-5-20251001", max_tokens=1024)

    print(f"\n{'=' * 60}")
    print(f"Query: {args.query}")
    print(f"{'=' * 60}\n")

    for token in llm.stream(messages):
        print(token, end="", flush=True)
    print("\n")

    print(f"Total wall time: {time.time() - t_total:.1f}s")
    print("Vertical slice complete. Full stack is proven.")


if __name__ == "__main__":
    main()
