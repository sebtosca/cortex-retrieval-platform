from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from arq import cron
from arq.connections import RedisSettings

from configs.settings import settings
from embeddings.bgem3 import BGEM3Embedder
from financial.fetcher import fetch_ohlcv
from financial.store import PriceStore
from ingestion.chunker import chunk_documents
from ingestion.loader import load_pdf
from retrieval.store import QdrantStore

logger = logging.getLogger(__name__)


async def run_ingestion(ctx: dict, job_id: str, file_bytes: bytes) -> None:
    embedder: BGEM3Embedder = ctx["embedder"]
    store: QdrantStore = ctx["store"]

    tmp_path = Path(f"/tmp/cortex_ingest_{job_id}.pdf")
    tmp_path.write_bytes(file_bytes)
    try:
        docs = load_pdf(tmp_path)
        chunks = chunk_documents(
            docs,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        embedded = embedder.embed_chunks(chunks)
        store.upsert(embedded)
    finally:
        tmp_path.unlink(missing_ok=True)


async def ingest_prices(ctx: dict) -> None:
    """Daily OHLCV refresh for all tracked tickers — runs in a thread to avoid blocking."""
    price_store: PriceStore = ctx["price_store"]
    for ticker in settings.tracked_tickers:
        try:
            bars = await asyncio.to_thread(fetch_ohlcv, ticker, 90)
            await price_store.upsert_prices(bars)
            logger.info("Upserted %d bars for %s", len(bars), ticker)
        except Exception:
            logger.exception("Price ingestion failed for %s", ticker)


async def startup(ctx: dict) -> None:
    ctx["embedder"] = BGEM3Embedder(use_fp16=True, batch_size=8)
    ctx["embedder"]._load()
    ctx["store"] = QdrantStore(url=settings.qdrant_url, collection=settings.qdrant_collection)
    ctx["store"].setup_collection(recreate=False)
    ctx["price_store"] = PriceStore(url=settings.postgres_url)
    await ctx["price_store"].create_tables()


async def shutdown(ctx: dict) -> None:
    await ctx["price_store"].close()


class WorkerSettings:
    functions = [run_ingestion, ingest_prices]
    cron_jobs = [cron(ingest_prices, hour=6, minute=0)]  # daily 06:00 UTC
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
