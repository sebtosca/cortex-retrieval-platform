from __future__ import annotations

from configs.settings import settings
from embeddings.bgem3 import BGEM3Embedder
from llm.client import CortexLLM
from llm.prompts import build_rag_messages
from retrieval.reranker import CrossEncoderReranker
from retrieval.store import QdrantStore


def run_rag_pipeline(
    question: str,
    embedder: BGEM3Embedder,
    store: QdrantStore,
    reranker: CrossEncoderReranker,
    llm: CortexLLM,
) -> tuple[str, list[str]]:
    """Run embed → retrieve → rerank → generate and return (answer, contexts)."""
    dense, sparse = embedder.encode_texts([question])
    q_idx = [int(k) for k in sparse[0].keys()]
    q_vals = [float(v) for v in sparse[0].values()]
    candidates = store.hybrid_search(dense[0], q_idx, q_vals, limit=settings.dense_top_k)
    top = reranker.rerank(question, candidates, top_k=settings.rerank_top_k)
    passages = [r.text for r in top]
    messages = build_rag_messages(question, passages)
    answer = llm.complete(messages)
    return answer, passages
