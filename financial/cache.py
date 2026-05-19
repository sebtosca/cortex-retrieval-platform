from __future__ import annotations

from redis.asyncio import Redis

PRICE_TTL_SECONDS = 300  # 5-minute TTL keeps latency low without stale-data risk


class PriceCache:
    def __init__(self, url: str) -> None:
        self._redis: Redis = Redis.from_url(url, decode_responses=True)

    @staticmethod
    def _key(ticker: str) -> str:
        return f"prices:{ticker.upper()}"

    async def get(self, ticker: str) -> str | None:
        return await self._redis.get(self._key(ticker))

    async def set(self, ticker: str, payload: str) -> None:
        await self._redis.setex(self._key(ticker), PRICE_TTL_SECONDS, payload)

    async def aclose(self) -> None:
        await self._redis.aclose()
