from __future__ import annotations

import datetime

import pandas as pd
import yfinance as yf


def fetch_ohlcv(ticker: str, days: int = 90) -> list[dict]:
    """Fetch OHLCV bars from yfinance and return as plain dicts ready for upsert."""
    df: pd.DataFrame = yf.Ticker(ticker).history(period=f"{days}d")
    if df.empty:
        return []

    rows: list[dict] = []
    for ts, row in df.iterrows():
        rows.append(
            {
                "ticker": ticker.upper(),
                "date": ts.date() if hasattr(ts, "date") else datetime.date.fromisoformat(str(ts)[:10]),
                "open": float(row["Open"]) if pd.notna(row["Open"]) else None,
                "high": float(row["High"]) if pd.notna(row["High"]) else None,
                "low": float(row["Low"]) if pd.notna(row["Low"]) else None,
                "close": float(row["Close"]) if pd.notna(row["Close"]) else None,
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else None,
            }
        )
    return rows
