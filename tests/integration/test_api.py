from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(http_client: AsyncClient):
    r = await http_client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["qdrant"] == "ok"


@pytest.mark.asyncio
async def test_ingest_returns_job_id_immediately(http_client: AsyncClient):
    r = await http_client.post(
        "/ingest",
        files={"file": ("test.pdf", b"not-a-real-pdf", "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body
    assert len(body["job_id"]) == 36  # UUID4


@pytest.mark.asyncio
async def test_query_sse_delivers_tokens(http_client: AsyncClient):
    tokens: list[str] = []
    async with http_client.stream(
        "POST", "/query", json={"query": "What is IBM Watsonx?"}
    ) as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        async for line in r.aiter_lines():
            if line.startswith("data: ") and not line.endswith("[DONE]"):
                tokens.append(line[6:])

    assert len(tokens) > 0


@pytest.mark.asyncio
async def test_query_sse_ends_with_done(http_client: AsyncClient):
    lines: list[str] = []
    async with http_client.stream(
        "POST", "/query", json={"query": "What are IBM Granite models?"}
    ) as r:
        async for line in r.aiter_lines():
            if line.startswith("data: "):
                lines.append(line[6:])

    assert "[DONE]" in lines


@pytest.mark.asyncio
async def test_ingest_job_status_queued(http_client: AsyncClient):
    r = await http_client.post(
        "/ingest",
        files={"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    r2 = await http_client.get(f"/ingest/{job_id}/status")
    assert r2.status_code == 200
    body = r2.json()
    assert body["job_id"] == job_id
    assert body["status"] in ("queued", "processing", "complete", "failed")


@pytest.mark.asyncio
async def test_ingest_status_unknown_job_returns_404(http_client: AsyncClient):
    r = await http_client.get("/ingest/00000000-0000-0000-0000-000000000000/status")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_price_returns_seeded_data(http_client: AsyncClient):
    r = await http_client.get("/prices/AAPL")
    assert r.status_code == 200
    body = r.json()
    assert body["ticker"] == "AAPL"
    assert body["close"] == pytest.approx(189.0, rel=1e-3)
    assert body["date"] == "2025-01-02"


@pytest.mark.asyncio
async def test_get_price_served_from_cache_on_second_call(http_client: AsyncClient):
    r1 = await http_client.get("/prices/AAPL")
    r2 = await http_client.get("/prices/AAPL")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()


@pytest.mark.asyncio
async def test_get_price_unknown_ticker_returns_404(http_client: AsyncClient):
    r = await http_client.get("/prices/ZZZZUNKNOWN9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_price_history_returns_list(http_client: AsyncClient):
    r = await http_client.get("/prices/AAPL/history")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0]["ticker"] == "AAPL"
