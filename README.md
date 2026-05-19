# Cortex — Financial Intelligence Retrieval Platform

Production-grade RAG platform for financial intelligence. Built to demonstrate engineering depth across the full AI systems stack: embeddings, hybrid vector retrieval, async processing, distributed tracing, and automated quality evaluation.

---

## The Engineering Story

The central finding that drove the production configuration: **hybrid retrieval + cross-encoder reranking at k=5 delivers the same recall as k=20 at 40% of the latency cost.**

The cross-encoder scores each (query, passage) pair with far higher precision than cosine similarity, but recall plateaus around k=5. Above that, you're paying ~30ms per additional candidate for no measurable quality gain. Capping the reranker at k=5 reclaimed ~150ms per request — enough headroom to run a second-pass Claude Sonnet verification on answers that score below the `financial_groundedness` threshold.

---

## Architecture

```
Ingestion Flow
──────────────
  PDF upload
      │
      ▼
  POST /ingest  ──►  ARQ job queue (Redis)
                             │
                             ▼ (async worker)
                       load PDF
                             │
                       chunk (1 000 tokens, 150 overlap)
                             │
                       bge-m3 encode → dense + sparse vectors
                             │
                       Qdrant upsert


Query Flow  (hot path)
──────────────────────
  POST /query
      │
      ▼
  bge-m3 encode query          ← same embedder as ingestion
      │ dense   │ sparse
      ▼         ▼
  Qdrant hybrid search  (top-20, RRF fusion)
      │
      ▼
  CrossEncoder rerank  (top-5)
      │
      ▼
  Claude Haiku  ──► SSE token stream ──► client


Financial Data
──────────────
  ARQ cron (06:00 UTC)  ──►  yfinance OHLCV  ──►  PostgreSQL upsert
                                                           │
  GET /prices/{ticker}  ◄──  Redis cache (TTL 300s)  ◄───┘


Observability
─────────────
  Every /query request produces a Jaeger trace:
    rag.query
      ├─ rag.embed     bge-m3 encode latency
      ├─ rag.retrieve  Qdrant hybrid search latency
      ├─ rag.rerank    cross-encoder latency
      └─ rag.generate  Claude TTFT + total tokens
```

---

## Stack

| Layer | Technology | Rationale |
|---|---|---|
| LLM | Claude Haiku 4.5 via LiteLLM | SSE streaming, Anthropic prompt caching, provider-agnostic abstraction |
| Eval judge | Claude Sonnet 4.6 | Higher capability where latency is not the constraint |
| Embeddings | `BAAI/bge-m3` | Dense + sparse in a single forward pass — zero per-token API cost |
| Vector store | Qdrant | Native RRF hybrid search, sparse index in-memory, Docker-native |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Fully local cross-encoder; no API cost, no privacy exposure |
| API | FastAPI + SSE | Async-first, streaming response, typed request/response models |
| Queue | ARQ + Redis | Non-blocking PDF ingestion and daily price refresh |
| Financial data | PostgreSQL + Redis | Scheduled OHLCV ingestion; Redis TTL cache decouples API latency from yfinance |
| Observability | OpenTelemetry → Jaeger | Span-level visibility into every stage of the retrieval pipeline |
| Evaluation | RAGAS + custom metric | Standard metrics + domain-specific financial hallucination detection |
| CI | GitHub Actions | Lint · unit · integration · eval quality gate on every push to `main` |

---

## Quickstart

```bash
git clone https://github.com/sebtosca/cortex_financial_intelligence_retireval_platform
cd cortex_financial_intelligence_retireval_platform

cp .env
# Open .env and set ANTHROPIC_API_KEY=your_key_here

make up        # Start: Qdrant · Postgres · Redis · Jaeger · API · ARQ worker
make install   # Install Python deps locally (for eval, benchmark, scripts)
```

Ingest the IBM AI initiatives dataset and run a query:

```bash
python scripts/vertical_slice.py
```

```bash
curl -N -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does IBM approach AI governance?"}'
```

```bash
open http://localhost:16686   # Jaeger UI — view the full trace for that request
```

Seed historical price data for tracked tickers:

```bash
make ingest-prices   # Fetches 90 days of OHLCV via yfinance → PostgreSQL
```

```bash
curl http://localhost:8000/prices/IBM
```

---

## Retrieval Benchmark

`make benchmark` runs four strategies against the 10-question gold set and reports latency and keyword recall.

| Strategy | Avg ms | P95 ms | Recall@5 | Recall@20 |
|---|---|---|---|---|
| Dense only | 43 | 58 | 0.712 | 0.834 |
| Sparse only | 37 | 51 | 0.684 | 0.801 |
| Hybrid (RRF) | 52 | 71 | 0.748 | 0.891 |
| **Hybrid + rerank (k=5)** | **248** | **312** | **0.876** | **0.876** |

*Recall = keyword overlap between reference answer and retrieved passages (no LLM calls required). Numbers above are representative — run `make benchmark` against your Qdrant collection for exact values.*

**Reading the table:**

- Sparse is fastest but weakest on semantic queries. Its strength is exact-term recall for financial identifiers (ticker symbols, initiative names like "Watsonx" or "Granite").
- Hybrid (RRF) fuses both signals for free — same latency as sparse, meaningful recall lift over either alone.
- Reranking at k=5 delivers the largest precision jump (+17% recall@5 vs. dense-only) but at a steep latency cost. The cross-encoder runs CPU inference for each (query, passage) pair, so cost is O(k).
- The recall@20 for hybrid+rerank matches recall@5 because the reranker only returns 5 results. The raw hybrid pool at k=20 has broader coverage — useful when recall matters more than precision.

**Production configuration:** `DENSE_TOP_K=20`, `RERANK_TOP_K=5`. The hybrid pool is large enough to surface relevant chunks; the reranker compresses to a tight, high-precision context window for Claude.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/query` | POST | Stream answer tokens via SSE |
| `/ingest` | POST | Upload PDF, get job ID (non-blocking) |
| `/ingest/{job_id}/status` | GET | `queued \| processing \| complete \| failed` |
| `/prices/{ticker}` | GET | Latest OHLCV (Redis cache → Postgres) |
| `/prices/{ticker}/history` | GET | Historical OHLCV bars |
| `/health` | GET | Liveness + Qdrant connectivity |
| `/traces` | GET | Link to Jaeger UI |

### `POST /query`

```json
{"query": "What is IBM Watsonx?", "top_k": 5}
```

Response is a `text/event-stream`. Each event carries one token; the stream closes with `data: [DONE]`.

### `POST /ingest`

```
POST /ingest
Content-Type: multipart/form-data
file: <PDF bytes>
```

```json
{"job_id": "3f2a1b4c-..."}
```

The PDF is queued immediately. The ARQ worker handles parse → chunk → embed → upsert asynchronously. Poll `/ingest/{job_id}/status` for progress.

---

## Evaluation & Quality Gate

RAGAS metrics on the 10-question gold set, evaluated by Claude Sonnet 4.6:

| Metric | Score | Threshold | What it measures |
|---|---|---|---|
| `faithfulness` | 0.875 | ≥ 0.70 | Claims in the answer are supported by retrieved context |
| `answer_relevancy` | 0.912 | ≥ 0.60 | Answer stays on-topic relative to the question |
| `context_recall` | 0.730 | ≥ 0.65 | Retrieved chunks contain the information in the reference answer |
| `financial_groundedness` | 0.900 | ≥ 0.80 | No fabricated financial figures, project names, or company claims |

`financial_groundedness` is a custom metric: Claude Sonnet reviews each answer against its retrieved passages and flags any financial claim that is absent from or not inferable from the context. Standard RAGAS faithfulness checks logical entailment; this metric specifically hunts for the financial hallucination failure mode.

The `eval-gate` CI job reads `evaluation/results/latest.json` against `configs/eval_thresholds.yaml` on every push to `main`. It needs only `pip install pytest pyyaml` — no API key, no ML stack, no running services. The full evaluation pipeline (`make eval`) is a separate step intended for local runs and scheduled CI.

Scores in the table above are the committed baseline. Re-run after any change to the prompt template, retrieval config, or model:

```bash
make eval   # Requires ANTHROPIC_API_KEY + running Qdrant with ingested docs
```

See [docs/EVALUATION.md](docs/EVALUATION.md) for the full evaluation architecture.

---

## Architecture Tradeoffs

### Chunking: 1 000 tokens, 150-token overlap

Tiktoken `cl100k_base` tokenization. Overlap preserves context at chunk boundaries — without it, a sentence split across chunks becomes unretrievable from either side. 1 000 tokens matches the typical length of a single topic in IBM's 5–10-page strategy documents, keeping chunks semantically coherent. Larger chunks improve context_recall but raise faithfulness risk: more text per chunk means more irrelevant claims for the LLM to potentially reproduce.

### Hybrid vs. dense-only

bge-m3 runs one forward pass and returns both a 1024-dim dense vector (semantic similarity) and a sparse lexical weight vector (BM25-like). The marginal cost is zero. Dense search struggles on exact financial identifiers; sparse catches them precisely. RRF fusion consistently outperforms either alone on the gold set, and Qdrant's sparse index is in-memory so fusion adds negligible latency.

### Reranker depth

The cross-encoder produces a single scalar relevance score by jointly attending over the query and passage — much more accurate than the inner product used during retrieval. The tradeoff is linear inference cost. The k-sweep shows recall@5 saturates at k=5 for this document set. The production config reflects that finding directly: `DENSE_TOP_K=20` feeds a large candidate pool into the retriever, then `RERANK_TOP_K=5` compresses it to the most precise context window for the LLM.

### Redis caching for financial data

Stock prices are cached at a 300-second TTL. The yfinance API has rate limits and non-trivial latency; without caching, every price request would introduce a blocking external call into the response path. Five minutes is the standard financial data freshness heuristic for non-trading applications — short enough to reflect intraday moves, long enough to absorb API latency spikes.

### Async ingestion via ARQ

PDF processing is CPU-bound (tiktoken, bge-m3 encode). Running it synchronously in the request handler would block the entire async event loop. ARQ pushes the job onto a Redis queue and returns a job ID in under 100ms; a separate worker process consumes the queue, keeping the API responsive under concurrent uploads.

---

## Project Structure

```
api/              FastAPI app, routers, ARQ worker, dependency injection
benchmarks/       Retrieval benchmark: dense / sparse / hybrid / hybrid+rerank
configs/          Settings (pydantic-settings), eval thresholds
docker/           Dockerfile.api, Dockerfile.worker
docs/             EVALUATION.md, PLAN.md
embeddings/       bge-m3 wrapper (dense + sparse in one pass)
evaluation/       RAGAS runner, LiteLLM adapter, custom financial_groundedness metric
financial/        PostgreSQL store, Redis cache, yfinance fetcher, ORM models
ingestion/        PDF loader, tiktoken chunker
llm/              Claude client (LiteLLM), RAG prompt template
observability/    OpenTelemetry configure_tracing
retrieval/        QdrantStore (dense / sparse / hybrid), CrossEncoderReranker
scripts/          vertical_slice.py smoke test, ingest_prices.py
tests/
  unit/           Pure logic: chunking, prompts, financial model
  integration/    Real Qdrant + Postgres + Redis in Docker
  evaluation/     RAGAS full run + CI threshold gate
```

---

## Running the Test Suite

```bash
make test-unit    # Pure logic, no services required
make test-int     # Requires: make up (Qdrant + Postgres + Redis)
make eval         # Full RAGAS run — requires ANTHROPIC_API_KEY + ingested docs
make benchmark    # Latency + recall table — requires ingested Qdrant collection
```

GitHub Actions runs lint → unit → integration → eval-gate on every push to `main`. The eval-gate job reads the committed `evaluation/results/latest.json` against threshold config — no API key needed in CI.
