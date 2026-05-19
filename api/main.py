from __future__ import annotations

from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from configs.settings import settings
from embeddings.bgem3 import BGEM3Embedder
from financial.cache import PriceCache
from financial.store import PriceStore
from llm.client import CortexLLM
from observability import configure_tracing
from retrieval.reranker import CrossEncoderReranker
from retrieval.store import QdrantStore

from api.routers import health, ingest, prices, query, traces


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_tracing(settings.otel_exporter_otlp_endpoint, settings.otel_service_name)
    app.state.embedder = BGEM3Embedder(use_fp16=True, batch_size=8)
    app.state.embedder._load()
    app.state.store = QdrantStore(url=settings.qdrant_url, collection=settings.qdrant_collection)
    app.state.store.setup_collection(recreate=False)
    app.state.reranker = CrossEncoderReranker()
    app.state.llm = CortexLLM(model=settings.rag_model, max_tokens=1024)
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    app.state.price_store = PriceStore(url=settings.postgres_url)
    await app.state.price_store.create_tables()
    app.state.price_cache = PriceCache(url=settings.redis_url)
    yield
    await app.state.arq_pool.aclose()
    await app.state.price_store.close()
    await app.state.price_cache.aclose()


app = FastAPI(title="Cortex", version="0.1.0", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)

app.include_router(query.router)
app.include_router(ingest.router)
app.include_router(prices.router)
app.include_router(health.router)
app.include_router(traces.router)
