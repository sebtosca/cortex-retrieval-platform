# Cortex — Production Build Plan

> Production-grade retrieval and intelligence platform. Architecture is the hero; financial domain is the demonstration use case.

---

## Stack

| Layer | Choice |
|---|---|
| LLM | Claude Haiku 4.5 (RAG) + Claude Sonnet 4.6 (eval), via LiteLLM |
| Vector store | Qdrant — native sparse+dense hybrid search |
| Embeddings | `BAAI/bge-m3` — dense+sparse in one model pass |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| API | FastAPI + SSE streaming + ARQ/Redis async ingestion queue |
| Financial data | PostgreSQL (scheduled yfinance ingestion) + Redis cache |
| Observability | OpenTelemetry traces → Jaeger |
| Evaluation | RAGAS standard metrics + custom financial hallucination metric |
| Tests | Unit + integration (real Qdrant in Docker) + RAGAS CI quality gate |
| Infra | docker-compose, GitHub Actions CI |

---

## Build Order

### Issue 1 — Vertical stack proof
**Type:** AFK | **Blocked by:** None

Prove the full tech stack works end-to-end before any abstraction.

`scripts/vertical_slice.py`: one PDF → bge-m3 embed → store in Qdrant → hybrid query → cross-encoder rerank → Claude Haiku SSE stream via LiteLLM.

**Acceptance criteria:**
- [ ] bge-m3 produces both dense and sparse vectors from a single model pass
- [ ] Qdrant stores and retrieves documents using hybrid (dense+sparse) search
- [ ] Cross-encoder reranker re-scores top-20 candidates and returns top-5
- [ ] Claude Haiku streams a response via SSE using LiteLLM
- [ ] Full pipeline runs end-to-end in under 3 seconds on a single document

---

### Issue 2 — Modular package structure
**Type:** AFK | **Blocked by:** #1

Refactor the vertical slice into clean, independently testable Python modules.

Modules: `ingestion/` (PDF loading, chunking, metadata), `embeddings/` (bge-m3 wrapper, caching), `retrieval/` (Qdrant client, hybrid search, reranker), `llm/` (LiteLLM wrapper, prompt templates, streaming).

**Acceptance criteria:**
- [ ] Each module has a clear public interface (no circular imports)
- [ ] `make slice` still runs green using the refactored modules
- [ ] Unit tests exist for chunking logic, prompt formatting, and score normalization
- [ ] `ruff check .` passes

---

### Issue 3 — FastAPI async API
**Type:** AFK | **Blocked by:** #2

Build the production API surface.

Endpoints:
- `POST /query` — streams SSE tokens from Claude Haiku
- `POST /ingest` — accepts PDF upload, returns job ID
- `GET /health` — liveness check
- `GET /traces` — link to Jaeger UI

**Acceptance criteria:**
- [ ] `POST /query` streams tokens via SSE as they arrive from the LLM
- [ ] `POST /ingest` returns `{"job_id": "..."}` immediately (non-blocking)
- [ ] `GET /health` returns 200 with service status
- [ ] Integration test hits real Qdrant running in Docker
- [ ] `httpx` async test client verifies SSE stream delivers tokens

---

### Issue 4 — Async ingestion queue: ARQ + Redis
**Type:** AFK | **Blocked by:** #3

Make PDF ingestion non-blocking using ARQ (async Redis queue).

`GET /ingest/{job_id}/status` returns job state: `queued | processing | complete | failed`.

**Acceptance criteria:**
- [ ] `POST /ingest` enqueues job and returns job ID within 100ms
- [ ] ARQ worker processes: PDF parse → chunk → embed → store in Qdrant
- [ ] `GET /ingest/{job_id}/status` reflects real job state
- [ ] Failed jobs surface an error message in the status response
- [ ] Integration test verifies full queue-to-completion flow

---

### Issue 5 — PostgreSQL financial data layer
**Type:** AFK | **Blocked by:** #2

Store financial metrics in PostgreSQL and serve them via Redis cache.

Scheduled job fetches yfinance data for `[GOOGL, MSFT, IBM, NVDA, AMZN]` and upserts into `company_metrics` table. Redis caches hot lookups with a 1-hour TTL.

**Acceptance criteria:**
- [ ] `company_metrics` table schema covers: market cap, P/E, dividend yield, beta, total revenue
- [ ] Scheduled ingestion job runs and upserts without duplicates
- [ ] API serves financial metrics from Redis (cache hit) or PostgreSQL (cache miss)
- [ ] Cache miss falls through to DB and populates Redis
- [ ] Unit test verifies upsert idempotency

---

### Issue 6 — OTel tracing → Jaeger
**Type:** AFK | **Blocked by:** #3

Instrument the full RAG pipeline with OpenTelemetry distributed tracing.

Distinct spans: `retrieval` (Qdrant query latency), `rerank` (cross-encoder latency), `generation` (Claude time-to-first-token + total).

**Acceptance criteria:**
- [ ] Every `POST /query` request produces a trace in Jaeger UI
- [ ] Retrieval, rerank, and generation are separate child spans with timing
- [ ] Token count and model name are recorded as span attributes
- [ ] `docker-compose up` starts Jaeger and traces are visible at `localhost:16686`
- [ ] OTel adds < 5ms overhead to p50 request latency

---

### Issue 7 — RAGAS evaluation harness
**Type:** AFK | **Blocked by:** #2

Build the evaluation dataset and scoring pipeline.

- RAGAS `TestsetGenerator` produces 50+ synthetic question/answer pairs from the company PDFs
- 10 questions manually verified against source documents (gold set)
- Standard metrics: `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`
- Custom metric: financial hallucination — does the answer fabricate a project name or initiative not in the retrieved context? (Claude Sonnet judge)

**Acceptance criteria:**
- [ ] `make eval` runs the full evaluation suite and prints a metrics table
- [ ] Gold set of 10 questions is committed to `tests/evaluation/gold_questions.json`
- [ ] Custom hallucination metric scores each answer 1–5 with a justification
- [ ] Results are saved to `evaluation/results/latest.json` for CI comparison
- [ ] All metrics documented in `docs/EVALUATION.md`

---

### Issue 8 — CI quality gate
**Type:** AFK | **Blocked by:** #7

Fail the CI build if RAGAS scores regress below thresholds.

Thresholds (starting points, tunable): `faithfulness >= 0.80`, `context_recall >= 0.75`, `hallucination_rate <= 0.15`.

**Acceptance criteria:**
- [ ] GitHub Actions `eval-gate` job runs on every push to `main`
- [ ] Build fails with a clear message if any threshold is breached
- [ ] Thresholds are configurable in `configs/eval_thresholds.yaml` (not hardcoded)
- [ ] Baseline scores from Issue #7 are committed so the gate has a reference point

---

### Issue 9 — Retrieval benchmark suite
**Type:** AFK | **Blocked by:** #7

Produce the benchmark table that becomes the centrepiece of the README and interview story.

Compare four retrieval strategies on the gold question set:

| Strategy | RAGAS Faithfulness | RAGAS Context Recall | p50 Latency |
|---|---|---|---|
| Dense only | | | |
| Sparse (bge-m3) only | | | |
| Hybrid (dense+sparse) | | | |
| Hybrid + reranker (k=5) | | | |

Also measure reranker latency at k=3, k=5, k=10, k=20 to find the quality/latency knee.

**Acceptance criteria:**
- [ ] `make benchmark` produces the full table and saves to `benchmarks/results/retrieval.json`
- [ ] Latency measured at p50 and p95 for each strategy
- [ ] Reranker k-sweep (k=3/5/10/20) shows the quality/latency tradeoff curve
- [ ] Results committed to repo so the table is reproducible

---

### Issue 10 — docker-compose full stack
**Type:** AFK | **Blocked by:** #3 #4 #5 #6

Wire all services into a single `docker-compose up` that starts a fully working system.

Services: Qdrant, PostgreSQL, Redis, Jaeger, API worker, ARQ worker.

**Acceptance criteria:**
- [ ] `make up` starts all services with no manual steps
- [ ] `make slice` passes against the running stack
- [ ] Health checks defined for each service
- [ ] `make down` cleans up cleanly
- [ ] `README.md` quickstart section works from a cold clone

---

### Issue 11 — README + architecture diagrams + engineering story
**Type:** HITL | **Blocked by:** #9 #10

Write the portfolio-facing documentation that makes the engineering depth legible to a recruiter or technical interviewer.

**Acceptance criteria:**
- [ ] Architecture diagram covers: ingestion flow, query flow, observability flow
- [ ] Benchmark table from Issue #9 is embedded with commentary
- [ ] "Engineering story" section explains the reranker k-sweep finding and hallucination characterization
- [ ] Quickstart: `git clone → cp .env.example .env → make up → make slice` works
- [ ] Tradeoffs section discusses: chunking strategy, hybrid vs dense, reranker depth, caching decisions

---

## Core Engineering Story

> "I benchmarked reranker depth (k=3 through k=20) against RAGAS faithfulness scores and found that quality plateaued above k=5 while latency grew linearly. I capped reranking at k=5, which freed ~150ms per request — enough to add a Claude Sonnet verification pass on answers scoring below 0.7 on the custom hallucination metric."

This is the narrative that turns a demo into an engineering story.

---

## Decisions Log

All architectural decisions locked in grill-me session on 2026-05-13. See `docs/adr/` for individual ADRs as they are written.
