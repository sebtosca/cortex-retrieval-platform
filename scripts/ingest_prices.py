"""One-shot OHLCV ingestion for all tracked tickers. Run before first API start."""
from __future__ import annotations

import asyncio
import logging

from configs.settings import settings
from financial.fetcher import fetch_ohlcv
from financial.store import PriceStore

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    store = PriceStore(url=settings.postgres_url)
    await store.create_tables()
    try:
        for ticker in settings.tracked_tickers:
            logger.info("Fetching %s ...", ticker)
            bars = await asyncio.to_thread(fetch_ohlcv, ticker, 90)
            await store.upsert_prices(bars)
            logger.info("  → %d bars upserted", len(bars))
    finally:
        await store.close()


if __name__ == "__main__":
    asyncio.run(main())
