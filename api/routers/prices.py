from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_price_cache, get_price_store
from financial.cache import PriceCache
from financial.models import PriceBar
from financial.store import PriceStore

router = APIRouter()


@router.get("/prices/{ticker}", response_model=PriceBar)
async def get_latest_price(
    ticker: str,
    price_store: PriceStore = Depends(get_price_store),
    price_cache: PriceCache = Depends(get_price_cache),
):
    cached = await price_cache.get(ticker)
    if cached:
        return PriceBar.model_validate_json(cached)

    row = await price_store.get_latest(ticker)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No price data for {ticker.upper()!r}")

    bar = PriceBar.model_validate(row)
    await price_cache.set(ticker, bar.model_dump_json())
    return bar


@router.get("/prices/{ticker}/history", response_model=list[PriceBar])
async def get_price_history(
    ticker: str,
    limit: int = 30,
    price_store: PriceStore = Depends(get_price_store),
):
    rows = await price_store.get_history(ticker, limit=min(limit, 365))
    if not rows:
        raise HTTPException(status_code=404, detail=f"No price data for {ticker.upper()!r}")
    return [PriceBar.model_validate(r) for r in rows]
