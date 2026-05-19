from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from financial.models import Base, StockPrice


class PriceStore:
    def __init__(self, url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(url, pool_pre_ping=True)
        self._sessions = async_sessionmaker(self._engine, expire_on_commit=False)

    async def create_tables(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def upsert_prices(self, bars: list[dict]) -> None:
        if not bars:
            return
        async with self._sessions() as session:
            stmt = pg_insert(StockPrice).values(bars)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_stock_prices_ticker_date",
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    "volume": stmt.excluded.volume,
                },
            )
            await session.execute(stmt)
            await session.commit()

    async def get_latest(self, ticker: str) -> StockPrice | None:
        async with self._sessions() as session:
            result = await session.execute(
                select(StockPrice)
                .where(StockPrice.ticker == ticker.upper())
                .order_by(desc(StockPrice.date))
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def get_history(self, ticker: str, limit: int = 30) -> list[StockPrice]:
        async with self._sessions() as session:
            result = await session.execute(
                select(StockPrice)
                .where(StockPrice.ticker == ticker.upper())
                .order_by(desc(StockPrice.date))
                .limit(limit)
            )
            return list(result.scalars().all())

    async def close(self) -> None:
        await self._engine.dispose()
