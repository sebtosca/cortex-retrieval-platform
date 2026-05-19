from __future__ import annotations

from fastapi import APIRouter, Depends
from opentelemetry import trace
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from api.deps import get_embedder, get_llm, get_reranker, get_store
from configs.settings import settings
from embeddings.bgem3 import BGEM3Embedder
from llm.client import CortexLLM
from llm.prompts import build_rag_messages
from retrieval.reranker import CrossEncoderReranker
from retrieval.store import QdrantStore

router = APIRouter()
tracer = trace.get_tracer("cortex.query")


class QueryRequest(BaseModel):
    query: str
    top_k: int = settings.rerank_top_k


@router.post("/query")
async def query_endpoint(
    body: QueryRequest,
    embedder: BGEM3Embedder = Depends(get_embedder),
    store: QdrantStore = Depends(get_store),
    reranker: CrossEncoderReranker = Depends(get_reranker),
    llm: CortexLLM = Depends(get_llm),
):
    async def stream():
        with tracer.start_as_current_span("rag.query") as root:
            root.set_attribute("query.text", body.query[:200])
            root.set_attribute("query.top_k", body.top_k)

            with tracer.start_as_current_span("rag.embed") as s:
                dense, sparse = embedder.encode_texts([body.query])
                q_idx = [int(k) for k in sparse[0].keys()]
                q_vals = [float(v) for v in sparse[0].values()]
                s.set_attribute("query.length", len(body.query))

            with tracer.start_as_current_span("rag.retrieve") as s:
                candidates = store.hybrid_search(
                    dense[0], q_idx, q_vals, limit=settings.dense_top_k
                )
                s.set_attribute("candidates.count", len(candidates))
                s.set_attribute("dense_top_k", settings.dense_top_k)

            with tracer.start_as_current_span("rag.rerank") as s:
                top = reranker.rerank(body.query, candidates, top_k=body.top_k)
                s.set_attribute("top_k", body.top_k)
                s.set_attribute("results.count", len(top))

            passages = [r.text for r in top]
            messages = build_rag_messages(body.query, passages)

            with tracer.start_as_current_span("rag.generate") as s:
                s.set_attribute("llm.model", settings.rag_model)
                s.set_attribute("context.passages", len(passages))
                token_count = 0
                async for token in llm.astream(messages):
                    token_count += 1
                    yield {"data": token}
                s.set_attribute("tokens.generated", token_count)

        yield {"data": "[DONE]"}

    return EventSourceResponse(stream())
