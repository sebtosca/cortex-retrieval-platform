from __future__ import annotations

from unittest.mock import patch

import pandas as pd


def _make_df() -> pd.DataFrame:
    idx = pd.DatetimeIndex([pd.Timestamp("2025-01-02"), pd.Timestamp("2025-01-03")])
    return pd.DataFrame(
        {
            "Open": [185.0, 186.0],
            "High": [190.0, 191.0],
            "Low": [184.0, 185.0],
            "Close": [189.0, 190.0],
            "Volume": [50_000_000, 45_000_000],
        },
        index=idx,
    )


def test_returns_list_of_dicts():
    from financial.fetcher import fetch_ohlcv

    with patch("financial.fetcher.yf.Ticker") as mock:
        mock.return_value.history.return_value = _make_df()
        result = fetch_ohlcv("AAPL", days=5)

    assert len(result) == 2
    required = {"ticker", "date", "open", "high", "low", "close", "volume"}
    assert all(required <= set(r.keys()) for r in result)


def test_empty_dataframe_returns_empty_list():
    from financial.fetcher import fetch_ohlcv

    with patch("financial.fetcher.yf.Ticker") as mock:
        mock.return_value.history.return_value = pd.DataFrame()
        result = fetch_ohlcv("AAPL", days=5)

    assert result == []


def test_ticker_normalised_to_uppercase():
    from financial.fetcher import fetch_ohlcv

    with patch("financial.fetcher.yf.Ticker") as mock:
        mock.return_value.history.return_value = _make_df()
        result = fetch_ohlcv("aapl", days=5)

    assert all(r["ticker"] == "AAPL" for r in result)


def test_nan_values_become_none():
    from financial.fetcher import fetch_ohlcv

    df = _make_df()
    df.loc[df.index[0], "Close"] = float("nan")

    with patch("financial.fetcher.yf.Ticker") as mock:
        mock.return_value.history.return_value = df
        result = fetch_ohlcv("AAPL", days=5)

    assert result[0]["close"] is None
    assert result[1]["close"] == 190.0
