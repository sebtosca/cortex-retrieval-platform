from __future__ import annotations

import datetime
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

import pytest_asyncio
from arq import create_pool
from arq.connections import RedisSettings
from httpx import ASGITransport, AsyncClient

from configs.settings import settings
from embeddings.bgem3 import BGEM3Embedder
from financial.cache import PriceCache
from financial.store import PriceStore
from ingestion.chunker import chunk_documents
from ingestion.models import Document
from retrieval.reranker import CrossEncoderReranker
from retrieval.store import QdrantStore

TEST_COLLECTION = "cortex_integration_test"


class _StubLLM:
    """Returns a fixed token sequence without hitting the Anthropic API."""

    async def astream(self, messages: list[dict]) -> AsyncIterator[str]:  # type: ignore[override]
        for token in ["IBM ", "Watsonx ", "is ", "IBM's ", "central ", "AI ", "platform."]:
            yield token


@pytest_asyncio.fixture(scope="session")
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    from api.main import app
    from api.deps import get_arq_pool, get_embedder, get_llm, get_price_cache, get_price_store, get_reranker, get_store

    embedder = BGEM3Embedder(use_fp16=True, batch_size=8)
    reranker = CrossEncoderReranker()
    stub_llm = _StubLLM()

    test_store = QdrantStore(url=settings.qdrant_url, collection=TEST_COLLECTION)
    test_store.setup_collection(recreate=True)
    docs = [
        Document(
            source="ibm.pdf",
            page=0,
            text="IBM Watsonx is IBM's central AI and data platform, launched in 2023.",
        ),
        Document(
            source="ibm.pdf",
            page=1,
            text="IBM Granite models are open-source foundation models for enterprise AI.",
        ),
    ]
    chunks = chunk_documents(docs, chunk_size=1000, chunk_overlap=150)
    embedded = embedder.embed_chunks(chunks)
    test_store.upsert(embedded)

    arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))

    price_store = PriceStore(url=settings.postgres_url)
    await price_store.create_tables()
    await price_store.upsert_prices(
        [
            {
                "ticker": "AAPL",
                "date": datetime.date(2025, 1, 2),
                "open": 185.0,
                "high": 190.0,
                "low": 184.0,
                "close": 189.0,
                "volume": 50_000_000,
            }
        ]
    )

    price_cache = PriceCache(url=settings.redis_url)

    # Bypass the production lifespan — set app.state directly so endpoints that
    # read request.app.state (e.g. /health) work correctly.
    @asynccontextmanager
    async def _test_lifespan(a):
        a.state.embedder = embedder
        a.state.store = test_store
        a.state.reranker = reranker
        a.state.llm = stub_llm
        a.state.arq_pool = arq_pool
        a.state.price_store = price_store
        a.state.price_cache = price_cache
        yield

    app.router.lifespan_context = _test_lifespan

    # Also override via DI so dependency_overrides take precedence if needed
    app.dependency_overrides[get_embedder] = lambda: embedder
    app.dependency_overrides[get_store] = lambda: test_store
    app.dependency_overrides[get_reranker] = lambda: reranker
    app.dependency_overrides[get_llm] = lambda: stub_llm
    app.dependency_overrides[get_arq_pool] = lambda: arq_pool
    app.dependency_overrides[get_price_store] = lambda: price_store
    app.dependency_overrides[get_price_cache] = lambda: price_cache

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
    test_store._client.delete_collection(TEST_COLLECTION)
    await arq_pool.aclose()
    await price_store.close()
    await price_cache.aclose()
