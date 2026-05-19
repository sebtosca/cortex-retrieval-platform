"""Retrieval benchmark: dense → sparse → hybrid → hybrid+rerank.

Measures per-strategy latency (avg/p95 ms) and keyword recall (@5 and @20)
on the 10-question gold set.  No LLM calls required — quality is measured via
keyword overlap between reference answers and retrieved passages.

Requires a running Qdrant instance with documents ingested.

Run with:
    make benchmark
    # or
    python benchmarks/retrieval_benchmark.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_GOLD_PATH = _REPO_ROOT / "tests" / "evaluation" / "gold_questions.json"
_RESULTS_DIR = Path(__file__).parent / "results"

_TOP_K = 20
_RERANK_K = 5


# ── quality metric ─────────────────────────────────────────────────────────────

def _word_set(text: str) -> set[str]:
    return set(re.findall(r"\b[a-z]{3,}\b", text.lower()))


def _keyword_recall(reference: str, passages: list[str], k: int) -> float:
    """Fraction of reference content words found in the top-k passages."""
    ref_words = _word_set(reference)
    if not ref_words:
        return 0.0
    retrieved_words = _word_set(" ".join(passages[:k]))
    return len(ref_words & retrieved_words) / len(ref_words)


# ── stats helpers ──────────────────────────────────────────────────────────────

def _avg(values: list[float]) -> float:
    return sum(values) / len(values)


def _p95(values: list[float]) -> float:
    idx = max(0, int(len(sorted(values)) * 0.95) - 1)
    return sorted(values)[idx]


# ── benchmark core ─────────────────────────────────────────────────────────────

def run_benchmark() -> dict:
    from configs.settings import settings
    from embeddings.bgem3 import BGEM3Embedder
    from retrieval.reranker import CrossEncoderReranker
    from retrieval.store import QdrantStore

    gold = json.loads(_GOLD_PATH.read_text())
    questions = [q["question"] for q in gold]
    references = [q["reference"] for q in gold]
    n = len(gold)
    print(f"[benchmark] {n} questions loaded")

    print("[benchmark] Loading bge-m3 embedder ...")
    embedder = BGEM3Embedder(use_fp16=True, batch_size=8)
    embedder._load()

    print("[benchmark] Loading cross-encoder reranker ...")
    reranker = CrossEncoderReranker()
    reranker._load()

    store = QdrantStore(url=settings.qdrant_url, collection=settings.qdrant_collection)
    try:
        store._client.get_collections()
    except Exception as exc:
        print(f"[benchmark] ERROR: cannot connect to Qdrant at {settings.qdrant_url}: {exc}")
        sys.exit(1)

    print("[benchmark] Encoding queries ...")
    dense_vecs, sparse_weights = embedder.encode_texts(questions)
    s_indices = [[int(k) for k in sw.keys()] for sw in sparse_weights]
    s_values = [[float(v) for v in sw.values()] for sw in sparse_weights]

    strategies = ["dense", "sparse", "hybrid", "hybrid+rerank"]
    rows: dict[str, dict] = {}

    for strategy in strategies:
        print(f"[benchmark] Strategy: {strategy} ...")
        latencies: list[float] = []
        rec5: list[float] = []
        rec20: list[float] = []

        for i in range(n):
            dense = dense_vecs[i]
            s_idx = s_indices[i]
            s_val = s_values[i]
            q = questions[i]
            ref = references[i]

            t0 = time.perf_counter()

            if strategy == "dense":
                hits = store.dense_search(dense, limit=_TOP_K)
            elif strategy == "sparse":
                hits = store.sparse_search(s_idx, s_val, limit=_TOP_K)
            elif strategy == "hybrid":
                hits = store.hybrid_search(dense, s_idx, s_val, limit=_TOP_K)
            else:  # hybrid+rerank
                candidates = store.hybrid_search(dense, s_idx, s_val, limit=_TOP_K)
                hits = reranker.rerank(q, candidates, top_k=_RERANK_K)

            latencies.append((time.perf_counter() - t0) * 1000)
            passages = [h.text for h in hits]
            rec5.append(_keyword_recall(ref, passages, k=5))
            rec20.append(_keyword_recall(ref, passages, k=20))

        rows[strategy] = {
            "avg_latency_ms": _avg(latencies),
            "p95_latency_ms": _p95(latencies),
            "recall_at_5": _avg(rec5),
            "recall_at_20": _avg(rec20),
        }

    return rows


# ── output ─────────────────────────────────────────────────────────────────────

def _print_table(rows: dict) -> None:
    col = [18, 16, 16, 12, 12]
    header = (
        f"{'Strategy':<{col[0]}}"
        f"{'Avg ms':>{col[1]}}"
        f"{'P95 ms':>{col[2]}}"
        f"{'Recall@5':>{col[3]}}"
        f"{'Recall@20':>{col[4]}}"
    )
    sep = "-" * len(header)
    print()
    print(sep)
    print(header)
    print(sep)
    for strategy, r in rows.items():
        print(
            f"{strategy:<{col[0]}}"
            f"{r['avg_latency_ms']:>{col[1]}.1f}"
            f"{r['p95_latency_ms']:>{col[2]}.1f}"
            f"{r['recall_at_5']:>{col[3]}.4f}"
            f"{r['recall_at_20']:>{col[4]}.4f}"
        )
    print(sep)
    print()


def _save(rows: dict) -> None:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_questions": 10,
        "top_k": _TOP_K,
        "rerank_k": _RERANK_K,
        "strategies": rows,
    }
    out = _RESULTS_DIR / "latest.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"[benchmark] Results saved → {out}")


if __name__ == "__main__":
    rows = run_benchmark()
    _print_table(rows)
    _save(rows)
